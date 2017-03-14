===============================
python-tempestconf
===============================

Overview
--------
python-tempestconf will automatically generate the tempest configuration based on your cloud.

Usage
------

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

