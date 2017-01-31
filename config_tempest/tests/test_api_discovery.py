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

from config_tempest import api_discovery
from config_tempest.tests import base
import json
import mock


class TestService(base.TestCase):

    FAKE_TOKEN = "s6d5f45sdf4s564f4s6464sdfsd514"
    FAKE_HEADERS = {
        'Accept': 'application/json', 'X-Auth-Token': FAKE_TOKEN
    }
    FAKE_URL = "http://fake_url:5000"

    def setUp(self):
        super(TestService, self).setUp()
        disable_ssl_validation = False
        self.Service = api_discovery.Service("Identity",
                                             self.FAKE_URL,
                                             self.FAKE_TOKEN,
                                             disable_ssl_validation)
        self.VersionedService = \
            api_discovery.VersionedService("Identity",
                                           self.FAKE_URL,
                                           self.FAKE_TOKEN,
                                           disable_ssl_validation)

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
