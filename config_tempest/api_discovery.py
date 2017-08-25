#!/usr/bin/env python

# Copyright 2013 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import logging
import re
import requests
import urllib3
import urlparse

LOG = logging.getLogger(__name__)
MULTIPLE_SLASH = re.compile(r'/+')


class ServiceError(Exception):
    pass


class Service(object):
    def __init__(self, name, service_url, token, disable_ssl_validation):
        self.name = name
        self.service_url = service_url
        self.headers = {'Accept': 'application/json', 'X-Auth-Token': token}
        self.disable_ssl_validation = disable_ssl_validation

    def do_get(self, url, top_level=False, top_level_path=""):
        u = urllib3.util.parse_url(url)

        # NOTE: endpoint URL has at least 3 formats:
        #   1. The classic (legacy) endpoint:
        #       http://{host}:{port}/v{1 or 2 or 3}/{project-id}
        #       http://{host}:{port}/v{1 or 2 or 3}
        #   2. The same as 1. but port is optional
        #   3. Under wsgi:
        #       http://{host}:{optional_port}/volume/v{1 or 2 or 3}
        url = None
        try:
            # check if url contains a version
            for ver in ['v1', 'v2', 'v3']:
                # if it's top level url crop it
                if ("/{0}".format(ver) in u.path) and top_level:
                    # path is the path of url starting with version
                    path = u.path[:u.path.rfind(ver)]
                    # if top_level_path was defined, use it
                    # otherwise use existing path
                    if len(top_level_path) > 0:
                        path = "/" + top_level_path
                    url = '%s://%s%s' % (u.scheme, u.netloc, path)
                    break
        except TypeError:
            # url contains no path (u is None), use top level one
            #  * http://{host}:{optional_port}
            path = "/" + top_level_path
            url = '%s://%s%s' % (u.scheme, u.netloc, path)

        if not url:
            # NOTE:
            #  * url contains a path, but top_level is False
            #  * url contains a path (at least "/") without version
            # EXAMPLE: probably, it is one of the next cases:
            #  * https://example.com:{optional_port}/compute/v2.1
            #  * https://volume.example.com:{optional_port}/
            # leave as is without cropping
            url = str(u)

        # remove occurrence of double "/" that may have occurred
        parts = list(urlparse.urlparse(url))
        parts[2] = MULTIPLE_SLASH.sub('/', parts[2])
        url = urlparse.urlunparse(parts)

        try:
            if self.disable_ssl_validation:
                urllib3.disable_warnings()
                http = urllib3.PoolManager(cert_reqs='CERT_NONE')
            else:
                http = urllib3.PoolManager()
            r = http.request('GET', url, headers=self.headers)
        except Exception as e:
            LOG.error("Request on service '%s' with url '%s' failed",
                      (self.name, url))
            raise e
        if r.status >= 400:
            raise ServiceError("Request on service '%s' with url '%s' failed"
                               " with code %d" % (self.name, url, r.status))
        return r.data

    def get_extensions(self):
        return []

    def get_versions(self):
        return []


class VersionedService(Service):
    def get_versions(self):
        body = self.do_get(self.service_url, top_level=True)
        body = json.loads(body)
        return self.deserialize_versions(body)

    def deserialize_versions(self, body):
        return map(lambda x: x['id'], body['versions'])


class ComputeService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class ImageService(VersionedService):
    pass


class NetworkService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/v2.0/extensions.json')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class VolumeService(VersionedService):
    def get_extensions(self):
        body = self.do_get(self.service_url + '/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions'])


class IdentityService(VersionedService):
    def get_extensions(self):
        # NOTE(mkopec): temporary hack, when --v3-only is used, all clients
        # use their v3 version except identity client - it still uses v2.0,
        # even in devstack environment
        self.service_url = self.service_url.replace("v3", "")
        if 'v2.0' in self.service_url:
            body = self.do_get(self.service_url + '/extensions')
        else:
            body = self.do_get(self.service_url + '/v2.0/extensions')
        body = json.loads(body)
        return map(lambda x: x['alias'], body['extensions']['values'])

    def deserialize_versions(self, body):
        return map(lambda x: x['id'], body['versions']['values'])


class ObjectStorageService(Service):
    def get_extensions(self):
        body = self.do_get(self.service_url, top_level=True,
                           top_level_path="info")
        body = json.loads(body)
        # Remove Swift general information from extensions list
        body.pop('swift')
        return body.keys()


service_dict = {'compute': ComputeService,
                'image': ImageService,
                'network': NetworkService,
                'object-store': ObjectStorageService,
                'volumev3': VolumeService,
                'identity': IdentityService}


def get_service_class(service_name):
    return service_dict.get(service_name, Service)


def get_identity_v3_extensions(keystone_v3_url):
    """Returns discovered identity v3 extensions

    As keystone V3 uses a JSON Home to store the extensions,
    this method is kept  here just for the sake of functionality, but it
    implements a different discovery method.

    :param keystone_v3_url: Keystone V3 auth url
    :return: A list with the discovered extensions
    """
    try:
        r = requests.get(keystone_v3_url,
                         verify=False,
                         headers={'Accept': 'application/json-home'})
    except requests.exceptions.RequestException as re:
        LOG.error("Request on service '%s' with url '%s' failed",
                  'identity', keystone_v3_url)
        raise re
    ext_h = 'http://docs.openstack.org/api/openstack-identity/3/ext/'
    res = [x for x in json.loads(r.content)['resources'].keys()]
    ext = [ex for ex in res if 'ext' in ex]
    return list(set([str(e).replace(ext_h, '').split('/')[0] for e in ext]))


def discover(auth_provider, region, object_store_discovery=True,
             api_version=2, disable_ssl_certificate_validation=True):
    """Returns a dict with discovered apis.

    :param auth_provider: An AuthProvider to obtain service urls.
    :param region: A specific region to use. If the catalog has only one region
    then that region will be used.
    :return: A dict with an entry for the type of each discovered service.
        Each entry has keys for 'extensions' and 'versions'.
    """
    token, auth_data = auth_provider.get_auth()
    services = {}
    service_catalog = 'serviceCatalog'
    public_url = 'publicURL'
    identity_port = urlparse.urlparse(auth_provider.auth_url).port
    if identity_port is None:
        identity_port = ""
    else:
        identity_port = ":" + str(identity_port)
    identity_version = urlparse.urlparse(auth_provider.auth_url).path
    if api_version == 3:
        service_catalog = 'catalog'
        public_url = 'url'
    for entry in auth_data[service_catalog]:
        name = entry['type']
        services[name] = dict()
        for _ep in entry['endpoints']:
            if _ep['region'] == region:
                ep = _ep
                break
        else:
            ep = entry['endpoints'][0]
        if 'identity' in ep[public_url]:
            services[name]['url'] = ep[public_url].replace(
                "/identity", "{0}{1}".format(
                    identity_port, identity_version))
        else:
            services[name]['url'] = ep[public_url]
        service_class = get_service_class(name)
        service = service_class(name, services[name]['url'], token,
                                disable_ssl_certificate_validation)
        if name == 'object-store' and not object_store_discovery:
            services[name]['extensions'] = []
        elif 'v3' not in ep[public_url]:  # is not v3 url
            services[name]['extensions'] = service.get_extensions()
        services[name]['versions'] = service.get_versions()
    return services
