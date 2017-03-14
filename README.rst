===============================
python-tempestconf
===============================

## Overview

python-tempestconf will automatically generate the tempest configuration based on your cloud.

* Free software: Apache license
* Documentation: https://github.com/redhat-openstack/python-tempestconf/blob/master/README.rst
* Source: https://github.com/redhat-openstack/python-tempestconf
* Bugs: https://github.com/redhat-openstack/python-tempestconf/issues

## Usage

### Git
[1.] Clone and change to the directory:

    $ git clone https://github.com/redhat-openstack/python-tempestconf
    $ cd python-tempestconf

[2.] Install requirements using tox:

    $ tox -epy27

[3.] Source the newly created virtual environment:

    $ source .tox/py27/bin/activate

[4.] Source cloud credentials, for example:

    (py27) $ source cloudrc

[5.] Run python-tempestconf to generate tempest configuration file:

    (py27) $ config_tempest/config_tempest.py --debug identity.uri $OS_AUTH_URL \
                identity.admin_password  $OS_PASSWORD --create

After this, `./etc/tempest.conf` is generated.


### RPM Installation

[1.] python-tempestconf is installed together with openstack-tempest, as a new dependency

    $ yum -y install openstack-tempest

[2.] Source cloud credentials, initialize tempest and run the discovery tool:

    $ source cloud_rc
    $ tempest init testingdir
    $ cd testingdir
    $ discover-tempest-config --debug identity.uri $OS_AUTH_URL \
          identity.admin_password  $OS_PASSWORD --create

*Note:* `discover-tempest-config` is the new name of the **old** `config_tempest.py` script and it **accepts the same parameters.** More about new features can be found [here](https://www.rdoproject.org/blog/2017/02/testing-rdo-with-tempest-new-features-in-ocata/)


