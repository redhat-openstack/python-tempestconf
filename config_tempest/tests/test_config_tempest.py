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


from config_tempest import config_tempest as tool
from config_tempest.tests import base
from fixtures import MonkeyPatch
import logging
import mock

# disable logging when running unit tests
logging.disable(logging.CRITICAL)


def _get_conf(V2, V3):
    """Creates fake conf for testing purposes"""
    conf = tool.TempestConf()
    conf.read(tool.DEFAULTS_FILE)
    uri = "http://172.16.52.151:5000/"
    conf.set("identity", "auth_version", "v3")
    conf.set("identity", "uri", uri + V2, priority=True)
    conf.set("identity", "uri_v3", uri + V3)
    conf.set("identity", "admin_username", "admin")
    conf.set("identity", "admin_tenant_name", "adminTenant")
    conf.set("identity", "admin_password", "adminPass")
    conf.set("auth", "allow_tenant_isolation", "False")
    return conf


def _get_clients(conf, admin=False):
    """Returns ClientManager instance"""
    return tool.ClientManager(conf, admin=admin)


class TestClientManager(base.TestCase):

    def setUp(self):
        super(TestClientManager, self).setUp()
        self.conf = _get_conf("v2.0", "v3")
        self.client = _get_clients(self.conf)

    def test_get_credentials_v2(self):
        mock_function = mock.Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock_function))
        self.client.get_credentials(self.conf, "name", "Tname", "pass")
        mock_function.assert_called_with(
            auth_url=None, fill_in=False, identity_version='v2',
            disable_ssl_certificate_validation='true',
            ca_certs=None, password='pass', tenant_name='Tname',
            username='name')

    def test_get_credentials_v3(self):
        mock_function = mock.Mock()
        function2mock = 'config_tempest.config_tempest.auth.get_credentials'
        self.useFixture(MonkeyPatch(function2mock, mock_function))
        self.client.get_credentials(self.conf, "name", "project_name",
                                    "pass", identity_version='v3')
        mock_function.assert_called_with(
            auth_url=None, fill_in=False, identity_version='v3',
            disable_ssl_certificate_validation='true',
            ca_certs=None, password='pass',
            username='name',
            project_name='project_name',
            domain_name='Default',
            user_domain_name='Default')

    def test_get_auth_provider_keystone_v2(self):
        # check if method returns correct method - KeystoneV2AuthProvider
        mock_function = mock.Mock()
        # mock V2Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV2AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock_function())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock_function.assert_called_with('', 'http://172.16.52.151:5000/v2.0',
                                         'true', None)

    def test_get_auth_provider_keystone_v3(self):
        # check if method returns KeystoneV3AuthProvider
        # make isinstance return True
        mockIsInstance = mock.Mock(return_value=True)
        self.useFixture(MonkeyPatch('config_tempest.config_tempest.isinstance',
                                    mockIsInstance))
        mock_function = mock.Mock()
        # mock V3Provider, if other provider is called, it fails
        func2mock = 'config_tempest.config_tempest.auth.KeystoneV3AuthProvider'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        resp = self.client.get_auth_provider(self.conf, "")
        self.assertEqual(resp, mock_function())
        # check parameters of returned function
        self.client.get_auth_provider(self.conf, "")
        mock_function.assert_called_with('', 'http://172.16.52.151:5000/v3',
                                         'true', None)

    def test_get_identity_version_v2(self):
        resp = self.client.get_identity_version(self.conf)
        self.assertEqual(resp, 'v2')

    def test_get_identity_version_v3(self):
        conf = _get_conf("v3", "v3")  # uri has to be v3
        resp = self.client.get_identity_version(conf)
        self.assertEqual(resp, 'v3')

    def test_init_manager_as_admin(self):
        mock_function = mock.Mock(return_value={"id": "my_fake_id"})
        func2mock = 'config_tempest.config_tempest.identity.get_tenant_by_name'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        tool.ClientManager(self.conf, admin=True)
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
        self.conf = tool.TempestConf()

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


class TestConfigTempest(base.TestCase):

    FAKE_SERVICES = {
        'compute': {
            'url': 'http://172.16.52.151:8774/v2.1/402486',
            'extensions': ['NMN', 'OS-DCF', 'OS-EXT-AZ', 'OS-EXT-IMG-SIZE'],
            'versions': ['v2.0', 'v2.1']
        },
        'network': {
            'url': 'http://172.16.52.151:9696',
            'extensions': ['default-subnetpools', 'network-ip-availability'],
            'versions': ['v2.0']
        },
        'image': {
            'url': 'http://172.16.52.151:9292',
            'extensions': [],
            'versions': ['v2.4', 'v2.3', 'v2.2']
        },
        'volume': {
            'url': 'http://172.16.52.151:8776/v1/402486',
            'extensions': ['OS-SCH-HNT', 'os-hosts'],
            'versions': ['v1.0', 'v2.0', 'v3.0']
        },
        'identity': {
            'url': 'http://172.16.52.151:5000/v3',
            'versions': ['v3.8', 'v2.0']
        },
        'ec2': {
            'url': 'http://172.16.52.151:5000'
        },
        's3': {
            'url': 'http://172.16.52.151:5000'
        }
    }

    def setUp(self):
        super(TestConfigTempest, self).setUp()
        self.conf = _get_conf("v2.0", "v3")

    def _mock_get_identity_v3_extensions(self):
        mock_function = mock.Mock(return_value=['FAKE-EXTENSIONS'])
        func2mock = 'config_tempest.api_discovery.get_identity_v3_extensions'
        self.useFixture(MonkeyPatch(func2mock, mock_function))

    def test_configure_boto(self):
        tool.configure_boto(self.conf, self.FAKE_SERVICES)
        expected_url = "http://172.16.52.151:5000"
        self.assertEqual(self.conf.get("boto", "ec2_url"), expected_url)
        self.assertEqual(self.conf.get("boto", "s3_url"), expected_url)

    def test_configure_horizon(self):
        mock_function = mock.Mock(return_value=True)
        self.useFixture(MonkeyPatch('urllib2.urlopen', mock_function))
        tool.configure_horizon(self.conf)
        self.assertEqual(self.conf.get('service_available', 'horizon'), "True")
        self.assertEqual(self.conf.get('dashboard', 'dashboard_url'),
                         "http://172.16.52.151/dashboard/")
        self.assertEqual(self.conf.get('dashboard', 'login_url'),
                         "http://172.16.52.151/dashboard/auth/login/")

    def test_discovered_services(self):
        self._mock_get_identity_v3_extensions()
        tool.configure_discovered_services(self.conf, self.FAKE_SERVICES)
        # check enabled services
        enabled_services = ["image", "volume", "compute", "network"]
        # iterating through tuples = (service_name, codename)
        for service in tool.SERVICE_NAMES.iteritems():
            if service[0] in enabled_services:
                enabled = "True"
            else:
                enabled = "False"
            self.assertEqual(self.conf.get("service_available", service[1]),
                             enabled)

        # check versions
        for service, versions in tool.SERVICE_VERSIONS.iteritems():
            section = service + '-feature-enabled'
            for version in versions:
                # only image v1 is expected to be False
                exp_support = str(not(service == "image" and version == "v1"))
                self.assertEqual(self.conf.get(section, 'api_' + version),
                                 exp_support)

        # check extensions
        for service, ext_key in tool.SERVICE_EXTENSION_KEY.iteritems():
            if service in self.FAKE_SERVICES:
                section = service + '-feature-enabled'
                if service == "identity":
                    exp_ext = ",FAKE-EXTENSIONS"
                else:
                    extensions = self.FAKE_SERVICES[service]['extensions']
                    exp_ext = ','.join(extensions)
                self.assertEqual(self.conf.get(section, 'api_extensions'),
                                 exp_ext)

    def test_discovered_services_volume_service_disabled(self):
        self.conf.set("services", "volume", "False")
        self._mock_get_identity_v3_extensions()
        tool.configure_discovered_services(self.conf, self.FAKE_SERVICES)
        self.assertFalse(self.conf.has_option("service_available", "cinder"))
        self.assertFalse(self.conf.has_option("volume-feature-enabled",
                                              "api_v1"))
        self.assertFalse(self.conf.has_option("volume-feature-enabled",
                                              "api_v2"))


class TestFlavors(base.TestCase):
    """Flavors test class

    Tests for create_tempest_flavors and find_or_create_flavor methods.
    """

    CLIENT_MOCK = 'tempest.lib.services.compute.flavors_client.FlavorsClient'
    FLAVORS_LIST = [
        {"id": "Fakeid", "name": "Name"},
        {"id": "MyFakeID", "name": "MyID"}
    ]

    def setUp(self):
        super(TestFlavors, self).setUp()
        self.conf = _get_conf("v2.0", "v3")
        self.client = _get_clients(self.conf).flavors

    def _mock_create_tempest_flavor(self, mock_function):
        func2mock = 'config_tempest.config_tempest.find_or_create_flavor'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        tool.create_tempest_flavors(client=self.client,
                                    conf=self.conf,
                                    allow_creation=True)

    def _mock_find_or_create_flavor(self, return_value, func2mock, flavor_name,
                                    expected_resp, allow_creation=False,
                                    flavor_id=None):
        mock_function = mock.Mock(return_value=return_value)
        self.useFixture(MonkeyPatch(self.CLIENT_MOCK + func2mock,
                                    mock_function))
        resp = tool.find_or_create_flavor(self.client,
                                          flavor_id=flavor_id,
                                          flavor_name=flavor_name,
                                          allow_creation=allow_creation)
        self.assertEqual(resp, expected_resp)

    def test_create_tempest_flavors(self):
        mock_function = mock.Mock(return_value="FakeID")
        self._mock_create_tempest_flavor(mock_function)
        self.assertEqual(self.conf.get('compute', 'flavor_ref'), "FakeID")
        self.assertEqual(self.conf.get('compute', 'flavor_ref_alt'), "FakeID")
        calls = [mock.call(self.client, None, 'm1.nano', True, ram=64),
                 mock.call(self.client, None, 'm1.micro', True, ram=128)]
        mock_function.assert_has_calls(calls, any_order=True)

    def test_create_tempest_flavors_overwrite(self):
        mock_function = mock.Mock(return_value="FakeID")
        self.conf.set('compute', 'flavor_ref', "FAKE_ID")
        self.conf.set('compute', 'flavor_ref_alt', "FAKE_ID")
        self._mock_create_tempest_flavor(mock_function)
        calls = [mock.call(self.client, "FAKE_ID", 'm1.nano', True, ram=64),
                 mock.call(self.client, "FAKE_ID", 'm1.micro', True, ram=128)]
        mock_function.assert_has_calls(calls, any_order=True)

    def test_create_flavor_not_allowed(self):
        exc = Exception
        self.assertRaises(exc,
                          tool.find_or_create_flavor,
                          client=self.client,
                          flavor_id="id",
                          flavor_name="name",
                          allow_creation=False)

    def test_create_flavor(self):
        return_value = {"flavor": {"id": "MyFakeID", "name": "MyID"}}
        # mock list_flavors() to return empty list
        mock_function = mock.Mock(return_value={"flavors": []})
        self.useFixture(MonkeyPatch(self.CLIENT_MOCK + '.list_flavors',
                                    mock_function))
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.create_flavor',
                                         flavor_name="MyID",
                                         expected_resp="MyFakeID",
                                         allow_creation=True)

    def test_find_flavor_by_id(self):
        return_value = {"flavors": self.FLAVORS_LIST}
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.list_flavors',
                                         flavor_id="MyFakeID",
                                         flavor_name=None,
                                         expected_resp="MyFakeID")

    def test_find_flavor_by_name(self):
        return_value = {"flavors": self.FLAVORS_LIST}
        self._mock_find_or_create_flavor(return_value=return_value,
                                         func2mock='.list_flavors',
                                         flavor_name="MyID",
                                         expected_resp="MyFakeID")


class TestFindImage(base.TestCase):

    CLIENT_MOCK = 'tempest.lib.services.image.v2.images_client.ImagesClient'
    IMAGES_LIST = [
        {"status": "active", "name": "ImageName"},
        {"status": "default", "name": "MyImage"},
        {"status": "active", "name": "MyImage"}
    ]

    def setUp(self):
        super(TestFindImage, self).setUp()
        conf = _get_conf("v2.0", "v3")
        self.client = _get_clients(conf).images

    def _mock_list_images(self, return_value, image_name, expected_resp):
        mock_function = mock.Mock(return_value=return_value)
        func2mock = self.CLIENT_MOCK + '.list_images'
        self.useFixture(MonkeyPatch(func2mock, mock_function))
        resp = tool._find_image(client=self.client,
                                image_id=None,
                                image_name=image_name)
        self.assertEqual(resp, expected_resp)

    def test_find_image_found(self):
        expected_resp = {"status": "default", "name": "MyImage"}
        self._mock_list_images(return_value={"images": self.IMAGES_LIST},
                               image_name="MyImage",
                               expected_resp=expected_resp)

    def test_find_image_not_found(self):
        self._mock_list_images(return_value={"images": self.IMAGES_LIST},
                               image_name="DoesNotExist",
                               expected_resp=None)


class TestFindOrUploadImage(base.TestCase):

    def setUp(self):
        super(TestFindOrUploadImage, self).setUp()
        conf = _get_conf("v2.0", "v3")
        self.client = _get_clients(conf).images

    @mock.patch('config_tempest.config_tempest._find_image')
    def test_find_or_upload_image_not_found_creation_not_allowed(
            self, mock_find_image):
        mock_find_image.return_value = None
        exc = Exception
        self.assertRaises(exc, tool.find_or_upload_image, client=self.client,
                          image_id=None, image_name=None,
                          allow_creation=False)

    @mock.patch('config_tempest.config_tempest._find_image')
    @mock.patch('config_tempest.config_tempest._download_file')
    @mock.patch('config_tempest.config_tempest._upload_image')
    def test_find_or_upload_image_not_found_creation_allowed_http(
            self, mock_upload_image, mock_download_file, mock_find_image):
        mock_find_image.return_value = None
        mock_upload_image.return_value = {"id": "my_fake_id"}
        image_source = "http://any_random_url"
        image_dest = "my_dest"
        image_name = "my_image"
        disk_format = "my_format"
        image_id = tool.find_or_upload_image(
            client=self.client, image_id=None, image_dest=image_dest,
            image_name=image_name, image_source=image_source,
            allow_creation=True, disk_format=disk_format)
        mock_download_file.assert_called_with(image_source, image_dest)
        mock_upload_image.assert_called_with(self.client,
                                             image_name, image_dest,
                                             disk_format)
        self.assertEqual(image_id, "my_fake_id")

    @mock.patch('config_tempest.config_tempest._find_image')
    @mock.patch('config_tempest.config_tempest._download_file')
    @mock.patch('config_tempest.config_tempest._upload_image')
    def test_find_or_upload_image_not_found_creation_allowed_https(
            self, mock_upload_image, mock_download_file, mock_find_image):
        mock_find_image.return_value = None
        mock_upload_image.return_value = {"id": "my_fake_id"}
        image_source = "https://any_random_url"
        image_dest = "my_dest"
        image_name = "my_image"
        disk_format = "my_format"
        image_id = tool.find_or_upload_image(
            client=self.client, image_id=None, image_dest=image_dest,
            image_name=image_name, image_source=image_source,
            allow_creation=True, disk_format=disk_format)
        mock_download_file.assert_called_with(image_source, image_dest)
        mock_upload_image.assert_called_with(self.client, image_name,
                                             image_dest, disk_format)
        self.assertEqual(image_id, "my_fake_id")

    @mock.patch('shutil.copyfile')
    @mock.patch('config_tempest.config_tempest._find_image')
    @mock.patch('config_tempest.config_tempest._download_file')
    @mock.patch('config_tempest.config_tempest._upload_image')
    def test_find_or_upload_image_not_found_creation_allowed_ftp(
            self, mock_upload_image, mock_download_file, mock_find_image,
            mock_copy):
        mock_find_image.return_value = None
        mock_upload_image.return_value = {"id": "my_fake_id"}
        # image source does not start with http or https
        image_source = "ftp://any_random_url"
        image_dest = "place_on_disk"
        disk_format = "my_format"
        image_name = "my_image"
        image_id = tool.find_or_upload_image(
            client=self.client, image_id=None, image_name=image_name,
            image_source=image_source, image_dest=image_dest,
            allow_creation=True, disk_format=disk_format)
        mock_copy.assert_called_with(image_source, image_dest)
        mock_upload_image.assert_called_with(
            self.client, image_name, image_dest, disk_format)
        self.assertEqual(image_id, "my_fake_id")

    @mock.patch('os.path.isfile')
    @mock.patch('config_tempest.config_tempest._find_image')
    def test_find_or_upload_image_found_downloaded(
            self, mock_find_image, mock_isfile):
        mock_find_image.return_value = \
            {"status": "active", "name": "ImageName", "id": "my_fake_id"}
        mock_isfile.return_value = True
        image_id = tool.find_or_upload_image(
            client=self.client, image_id=None,
            image_name=None, allow_creation=True)
        self.assertEqual(image_id, "my_fake_id")

    @mock.patch('config_tempest.config_tempest._download_image')
    @mock.patch('os.path.isfile')
    @mock.patch('config_tempest.config_tempest._find_image')
    def test_find_or_upload_image_found_not_downloaded(
            self, mock_find_image, mock_isfile, mock_download_image):
        image_id = "my_fake_id"
        mock_find_image.return_value = \
            {"status": "active", "name": "ImageName", "id": image_id}
        mock_isfile.return_value = False
        image_id = tool.find_or_upload_image(
            client=self.client, image_id=None,
            image_name=None, allow_creation=True)
        mock_download_image.assert_called()
        self.assertEqual(image_id, "my_fake_id")


class TestCreateTempestNetworks(base.TestCase):

    FAKE_NETWORK_LIST = {
        'networks': [{
            'provider:physical_network': None,
            'id': '1ea533d7-4c65-4f25',
            'router:external': True,
            'availability_zone_hints': [],
            'availability_zones': [],
            'ipv4_address_scope': None,
            'status': 'ACTIVE',
            'subnets': ['fake_subnet'],
            'label': 'my_fake_label',
            'name': 'tempest-network',
            'admin_state_up': True,
        }]
    }

    NEUTRON_CLIENT_MOCK = ('tempest.lib.services.network.'
                           'networks_client.NetworksClient')
    NOVA_CLIENT_MOCK = ('tempest.lib.services.compute.'
                        'networks_client.NetworksClient')

    def setUp(self):
        super(TestCreateTempestNetworks, self).setUp()
        self.conf = _get_conf("v2.0", "v3")
        self.clients = _get_clients(self.conf)

    def _mock_list_networks(self, client, client_mock, return_value):
        mock_function = mock.Mock(return_value=return_value)
        client_mock = client_mock + '.list_networks'
        self.useFixture(MonkeyPatch(client_mock, mock_function))

    def test_tempest_network_id_not_found(self):
        neutron_client = self.clients.get_neutron_client()
        self._mock_list_networks(neutron_client,
                                 self.NEUTRON_CLIENT_MOCK,
                                 return_value={"networks": []})
        self.assertRaises(ValueError,
                          tool.create_tempest_networks,
                          clients=self.clients,
                          conf=self.conf,
                          has_neutron=True,
                          public_network_id="doesn't_exist")

    def test_create_network_id_supplied_by_user(self):
        neutron_client = self.clients.get_neutron_client()
        self._mock_list_networks(neutron_client,
                                 self.NEUTRON_CLIENT_MOCK,
                                 return_value=self.FAKE_NETWORK_LIST)
        tool.create_tempest_networks(clients=self.clients,
                                     conf=self.conf,
                                     has_neutron=True,
                                     public_network_id='1ea533d7-4c65-4f25')
        self.assertEqual(self.conf.get('network', 'public_network_id'),
                         '1ea533d7-4c65-4f25')

    def test_create_network_auto_discover(self):
        neutron_client = self.clients.get_neutron_client()
        self._mock_list_networks(neutron_client,
                                 self.NEUTRON_CLIENT_MOCK,
                                 return_value=self.FAKE_NETWORK_LIST)
        tool.create_tempest_networks(clients=self.clients,
                                     conf=self.conf,
                                     has_neutron=True,
                                     public_network_id=None)
        self.assertEqual(self.conf.get('network', 'public_network_id'),
                         '1ea533d7-4c65-4f25')
        self.assertEqual(self.conf.get('network', 'floating_network_name'),
                         'tempest-network')

    @mock.patch('config_tempest.config_tempest.LOG')
    def test_create_network_auto_discover_not_found(self, mock_logging):
        neutron_client = self.clients.get_neutron_client()
        # delete subnets => network will not be found
        self.FAKE_NETWORK_LIST['networks'][0]['subnets'] = []
        self._mock_list_networks(neutron_client,
                                 self.NEUTRON_CLIENT_MOCK,
                                 return_value=self.FAKE_NETWORK_LIST)
        tool.create_tempest_networks(clients=self.clients,
                                     conf=self.conf,
                                     has_neutron=True,
                                     public_network_id=None)
        # check if LOG.error was called
        self.assertTrue(mock_logging.error.called)

    def test_network_not_discovered(self):
        exception = Exception
        nova_client = self.clients.get_nova_net_client()
        self._mock_list_networks(nova_client,
                                 self.NOVA_CLIENT_MOCK,
                                 return_value=False)
        self.assertRaises(exception,
                          tool.create_tempest_networks,
                          clients=self.clients,
                          conf=self.conf,
                          has_neutron=False,
                          public_network_id=None)

    def test_create_fixed_network(self):
        nova_client = self.clients.get_nova_net_client()
        self._mock_list_networks(nova_client,
                                 self.NOVA_CLIENT_MOCK,
                                 return_value=self.FAKE_NETWORK_LIST)
        tool.create_tempest_networks(clients=self.clients,
                                     conf=self.conf,
                                     has_neutron=False,
                                     public_network_id=None)
        self.assertEqual(self.conf.get('compute', 'fixed_network_name'),
                         'my_fake_label')
