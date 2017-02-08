# -*- coding: utf-8 -*-

# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_config_tempest
----------------------------------

Tests for `config_tempest` module.
"""

from config_tempest import config_tempest
from config_tempest.tests import base
from fixtures import MonkeyPatch
from mock import Mock


class TestClientManager(base.TestCase):

    def _get_conf(self, V2, V3):
        """Create fake conf for testing purposes"""
        conf = config_tempest.TempestConf()
        conf.read(config_tempest.DEFAULTS_FILE)
        uri = "http://172.16.52.151:5000/"
        conf.set("identity", "auth_version", "v3")
        conf.set("identity", "uri", uri + V2, priority=True)
        conf.set("identity", "uri_v3", uri + V3)
        conf.set("identity", "admin_username", "admin")
        conf.set("identity", "admin_tenant_name", "adminTenant")
        conf.set("identity", "admin_password", "adminPass")
        conf.set("auth", "allow_tenant_isolation", "False")
        return conf

    def setUp(self):
        super(TestClientManager, self).setUp()
        conf = self._get_conf("v2.0", "v3")
        self.client = config_tempest.ClientManager(conf, admin=False)
        self.conf = conf

    def test_get_credentials_v2(self):
        mock = Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock))
        self.client.get_credentials(self.conf, "name", "Tname", "pass")
        mock.assert_called_with(auth_url=None,
                                fill_in=False,
                                identity_version='v2',
                                disable_ssl_certificate_validation='true',
                                ca_certs=None,
                                password='pass',
                                tenant_name='Tname',
                                username='name')

    def test_get_credentials_v3(self):
        mock = Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock))
        self.client.get_credentials(self.conf, "name", "project_name",
                                    "pass", identity_version='v3')
        mock.assert_called_with(auth_url=None,
                                fill_in=False,
                                identity_version='v3',
                                disable_ssl_certificate_validation='true',
                                ca_certs=None,
                                password='pass',
                                username='name',
                                project_name='project_name',
                                domain_name='Default',
                                user_domain_name='Default')

    def test_get_auth_provider_keystone_v2(self):
        # check if method returns correct method - KeystoneV2AuthProvider
        mock = Mock()
        # mock V2Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV2AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock.assert_called_with('', 'http://172.16.52.151:5000/v2.0',
                                'true', None)

    def test_get_auth_provider_keystone_v3(self):
        # check if method returns correct method - KeystoneV3AuthProvider
        # make isinstance return True
        test = 'config_tempest.config_tempest.isinstance'
        mockIsInstance = Mock(return_value=True)
        self.useFixture(MonkeyPatch(test, mockIsInstance))
        mock = Mock()
        # mock V3Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV3AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock.assert_called_with('', 'http://172.16.52.151:5000/v3',
                                'true', None)

    def test_get_identity_version_v2(self):
        resp = self.client.get_identity_version(self.conf)
        self.assertEqual(resp, 'v2')

    def test_get_identity_version_v3(self):
        conf = self._get_conf("v3", "v3")  # uri has to be v3
        resp = self.client.get_identity_version(conf)
        self.assertEqual(resp, 'v3')

    def test_init_manager_as_admin(self):
        mock = Mock(return_value={"id": "my_fake_id"})
        func2mock = 'config_tempest.config_tempest.identity.get_tenant_by_name'
        self.useFixture(MonkeyPatch(func2mock, mock))
        config_tempest.ClientManager(self.conf, admin=True)
        # check if admin credentials were set
        admin_tenant = self.conf.get("identity", "admin_tenant_name")
        admin_password = self.conf.get("identity", "admin_password")
        self.assertEqual(self.conf.get("identity", "admin_username"), "admin")
        self.assertEqual(admin_tenant, "adminTenant")
        self.assertEqual(admin_password, "adminPass")
        # check if admin tenant id was set
        admin_tenant_id = self.conf.get("identity", "admin_tenant_id")
        self.assertEqual(admin_tenant_id, "my_fake_id")


class TestTempestConf(base.TestCase):
    def setUp(self):
        super(TestTempestConf, self).setUp()
        self.conf = config_tempest.TempestConf()

    def test_set_value(self):
        resp = self.conf.set("section", "key", "value")
        self.assertTrue(resp)
        self.assertEqual(self.conf.get("section", "key"), "value")
        self.assertEqual(self.conf.get_defaulted("section", "key"), "value")

    def test_set_value_overwrite(self):
        resp = self.conf.set("section", "key", "value")
        resp = self.conf.set("section", "key", "value")
        self.assertTrue(resp)

    def test_set_value_overwrite_priority(self):
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        resp = self.conf.set("sectionPriority", "key", "value")
        self.assertFalse(resp)

    def test_set_value_overwrite_by_priority(self):
        resp = self.conf.set("section", "key", "value")
        resp = self.conf.set("section", "key", "value", priority=True)
        self.assertTrue(resp)

    def test_set_value_overwrite_priority_by_priority(self):
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        resp = self.conf.set("sectionPriority", "key", "value", priority=True)
        self.assertTrue(resp)

    def test_get_bool_value(self):
        self.assertTrue(self.conf.get_bool_value("True"))
        self.assertFalse(self.conf.get_bool_value("False"))
        self.assertRaises(ValueError, self.conf.get_bool_value, "no")
