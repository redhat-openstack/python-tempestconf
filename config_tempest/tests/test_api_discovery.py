# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
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

from config_tempest import api_discovery as api
from config_tempest.tests import base
import json
import mock
from oslotest import mockpatch


class BaseServiceTest(base.TestCase):

    FAKE_TOKEN = "s6d5f45sdf4s564f4s6464sdfsd514"
    FAKE_HEADERS = {
        'Accept': 'application/json', 'X-Auth-Token': FAKE_TOKEN
    }
    FAKE_URL = "http://10.200.16.10:8774/"
    FAKE_VERSIONS = (
        {
            "versions": [{
                "status": "SUPPORTED",
                "updated": "2011-01-21T11:33:21Z",
                "links": [{
                    "href": "http://10.200.16.10:8774/v2 / ",
                    "rel": "self "
                }],
                "min_version": "",
                "version": "",
                "id": "v2.0",
                "values": [
                    {"id": u'v3.8'}
                ]
            }, {
                "status": "CURRENT",
                "updated": "2013-07-23T11:33:21Z",
                "links": [{
                    "href": "http://10.200.16.10:8774/v2.1/",
                    "rel": "self"
                }],
                "min_version": "2.1",
                "version": "2.41",
                "id": "v2.1",
                "values": [
                    {"id": u'v2.0'}
                ]
            }]
        }
    )
    FAKE_IDENTITY_VERSIONS = (
        {
            'versions': {
                'values': [{
                    'status': 'stable',
                    'id': 'v3.8',
                }, {
                    'status': 'deprecated',
                    'id': 'v2.0',
                }]
            }
        }
    )
    FAKE_EXTENSIONS = (
        {
            "extensions": [{
                "updated": "2014-12-03T00:00:00Z",
                "name": "Multinic",
                "namespace": "http://docs.openstack.org/compute/ext/fake_xml",
                "alias": "NMN",
                "description": "Multiple network support."
            }, {
                "updated": "2014-12-03T00:00:00Z",
                "name": "DiskConfig",
                "namespace": "http://docs.openstack.org/compute/ext/fake_xml",
                "alias": "OS-DCF",
                "description": "Disk Management Extension."
            }]
        }
    )
    FAKE_IDENTITY_EXTENSIONS = (
        {
            "extensions": {
                'values': [{
                    'alias': 'OS-DCF',
                    'id': 'v3.8',
                }, {
                    'alias': 'NMN',
                    'id': 'v2.0',
                }]
            }
        }
    )
    FAKE_STORAGE_EXTENSIONS = (
        {
            "formpost": {},
            "methods": ["GET", "HEAD", "PUT", "POST", "DELETE"],
            "ratelimit": {
                "account_ratelimit": 0.0,
                "max_sleep_time_seconds": 60.0,
                "container_ratelimits": []
            },
            "account_quotas": {},
            "swift": {
                "container_listing_limit": 10000,
                "allow_account_management": True,
                "max_container_name_length": 256
            }
        }
    )

    class FakeRequestResponse(object):
        URL = 'http://docs.openstack.org/api/openstack-identity/3/ext/'
        FAKE_V3_EXTENSIONS = (
            {
                'resources': {
                    URL + 'OS-INHERIT/1.0/rel/domain_user_'
                        + 'role_inherited_to_projects': "",
                    URL + 'OS-SIMPLE-CERT/1.0/rel/ca_certificate': "",
                    URL + 'OS-EP-FILTER/1.0/rel/endpoint_group_to_'
                        + 'project_association': "",
                    URL + 'OS-EP-FILTER/1.0/rel/project_endpoint': "",
                    URL + 'OS-OAUTH1/1.0/rel/user_access_token_roles': ""
                }
            }
        )

        def __init__(self):
            self.content = json.dumps(self.FAKE_V3_EXTENSIONS)

    def _fake_do_get(self, fake_data):
        function2mock = 'config_tempest.api_discovery.Service.do_get'
        do_get_output = json.dumps(fake_data)
        self.useFixture(mockpatch.Patch(function2mock,
                                        return_value=do_get_output))

    def _test_get_service_class(self, service, cls):
        resp = api.get_service_class(service)
        self.assertEqual(resp, cls)

    def _get_extensions(self, service, expected_resp, fake_data):
        self._fake_do_get(fake_data)
        resp = service.get_extensions()
        self.assertEqual(resp, expected_resp)

    def _test_deserialize_versions(self, service, expected_resp, fake_data):
        resp = service.deserialize_versions(fake_data)
        self.assertEqual(resp, expected_resp)


class TestService(BaseServiceTest):
    def setUp(self):
        super(TestService, self).setUp()
        self.Service = api.Service("ServiceName",
                                   self.FAKE_URL,
                                   self.FAKE_TOKEN,
                                   disable_ssl_validation=False)

    def _mocked_do_get(self, mock_urllib3):
        mock_http = mock_urllib3.PoolManager()
        expected_resp = mock_http.request('GET',
                                          self.FAKE_URL,
                                          self.FAKE_HEADERS)
        return expected_resp.data

    @mock.patch('config_tempest.api_discovery.urllib3')
    def test_do_get(self, mock_urllib3):
        resp = self.Service.do_get(self.FAKE_URL)
        expected_resp = self._mocked_do_get(mock_urllib3)
        self.assertEqual(resp, expected_resp)

    def test_service_headers(self):
        self.assertEqual(self.Service.headers, self.FAKE_HEADERS)


class TestVersionedService(BaseServiceTest):
    def setUp(self):
        super(TestVersionedService, self).setUp()
        self.Service = api.VersionedService("ServiceName",
                                            self.FAKE_URL,
                                            self.FAKE_TOKEN,
                                            disable_ssl_validation=False)

    def test_get_versions(self):
        expected_resp = [u'v2.0', u'v2.1']
        self._fake_do_get(self.FAKE_VERSIONS)
        resp = self.Service.get_versions()
        self.assertEqual(resp, expected_resp)

    def test_deserialize_versions(self):
        expected_resp = [u'v2.0', u'v2.1']
        self._test_deserialize_versions(self.Service,
                                        expected_resp,
                                        self.FAKE_VERSIONS)


class TestComputeService(BaseServiceTest):
    def setUp(self):
        super(TestComputeService, self).setUp()
        self.Service = api.ComputeService("ServiceName",
                                          self.FAKE_URL,
                                          self.FAKE_TOKEN,
                                          disable_ssl_validation=False)

    def test_get_extensions(self):
        expected_resp = [u'NMN', u'OS-DCF']
        self._get_extensions(self.Service, expected_resp, self.FAKE_EXTENSIONS)

    def test_get_service_class(self):
        self._test_get_service_class('compute', api.ComputeService)


class TestImageService(BaseServiceTest):
    def setUp(self):
        super(TestImageService, self).setUp()

    def test_get_service_class(self):
        self._test_get_service_class('image', api.ImageService)


class TestNetworkService(BaseServiceTest):
    def setUp(self):
        super(TestNetworkService, self).setUp()
        self.Service = api.NetworkService("ServiceName",
                                          self.FAKE_URL,
                                          self.FAKE_TOKEN,
                                          disable_ssl_validation=False)

    def test_get_extensions(self):
        expected_resp = [u'NMN', u'OS-DCF']
        self._get_extensions(self.Service, expected_resp, self.FAKE_EXTENSIONS)

    def test_get_service_class(self):
        self._test_get_service_class('network', api.NetworkService)


class TestVolumeService(BaseServiceTest):
    def setUp(self):
        super(TestVolumeService, self).setUp()
        self.Service = api.VolumeService("ServiceName",
                                         self.FAKE_URL,
                                         self.FAKE_TOKEN,
                                         disable_ssl_validation=False)

    def test_get_extensions(self):
        expected_resp = [u'NMN', u'OS-DCF']
        self._get_extensions(self.Service, expected_resp, self.FAKE_EXTENSIONS)

    def test_get_service_class(self):
        self._test_get_service_class('volume', api.VolumeService)


class TestIdentityService(BaseServiceTest):
    def setUp(self):
        super(TestIdentityService, self).setUp()
        self.Service = api.IdentityService("ServiceName",
                                           self.FAKE_URL,
                                           self.FAKE_TOKEN,
                                           disable_ssl_validation=False)

    def test_get_extensions(self):
        expected_resp = [u'OS-DCF', u'NMN']
        self._get_extensions(self.Service, expected_resp,
                             self.FAKE_IDENTITY_EXTENSIONS)

    def test_deserialize_versions(self):
        expected_resp = ['v3.8', 'v2.0']
        self._test_deserialize_versions(self.Service,
                                        expected_resp,
                                        self.FAKE_IDENTITY_VERSIONS)

    def test_get_service_class(self):
        self._test_get_service_class('identity', api.IdentityService)


class TestObjectStorageService(BaseServiceTest):
    def setUp(self):
        super(TestObjectStorageService, self).setUp()
        self.Service = api.ObjectStorageService("ServiceName",
                                                self.FAKE_URL,
                                                self.FAKE_TOKEN,
                                                disable_ssl_validation=False)

    def test_get_extensions(self):
        expected_resp = [u'formpost', u'ratelimit',
                         u'methods', u'account_quotas']
        self._get_extensions(self.Service, expected_resp,
                             self.FAKE_STORAGE_EXTENSIONS)

    def test_get_service_class(self):
        self._test_get_service_class('object-store',
                                     api.ObjectStorageService)


class TestApiDiscoveryMethods(BaseServiceTest):
    def setUp(self):
        super(TestApiDiscoveryMethods, self).setUp()

    def test_get_identity_v3_extensions(self):
        v3_url = 'http://172.16.52.151:5000/v3'
        expected_resp = ['OS-INHERIT', 'OS-OAUTH1',
                         'OS-SIMPLE-CERT', 'OS-EP-FILTER']
        fake_resp = self.FakeRequestResponse()
        self.useFixture(mockpatch.Patch('requests.get',
                                        return_value=fake_resp))
        resp = api.get_identity_v3_extensions(v3_url)
        self.assertEqual(resp, expected_resp)

    def test_discover(self):
        pass
