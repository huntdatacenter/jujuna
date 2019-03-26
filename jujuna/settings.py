
# Juju requires higher frame size for large models
MAX_FRAME_SIZE = 2**26

# Not all charms use the openstack-origin. The openstack specific
# charms do, but some of the others use an alternate origin key
# depending on who the author was.
ORIGIN_KEYS = {
    'ceph': 'source',
    'ceph-osd': 'source',
    'ceph-mon': 'source',
    'ceph-radosgw': 'source',
}

# Default list of services, used in upgrade if apps not specified in params
# Services are upgraded in the order specified
# The order of services is based on:
# https://github.com/openstack-charmers/openstack-charms-tools/blob/master/os-upgrade.py
# https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/app-upgrade-openstack.html
SERVICES = [
    # Identity
    'keystone',

    # Ceph
    'ceph-mon',
    'ceph-osd',
    'ceph-radosgw',

    # Image
    'glance',

    # Upgrade nova
    'nova-cloud-controller',

    'nova-compute',

    # Neutron upgrades
    'neutron-api',

    'neutron-gateway',

    'neutron-openvswitch',

    # Backend block-storage upgrade.
    # Note: just upgrade cinder service.
    'cinder',
    'cinder-ceph',

    # Upgrade dashboard
    'openstack-dashboard',

    'rabbitmq-server',
]
