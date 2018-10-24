
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
SERVICES = [
    # Ceph
    'ceph-mon',
    'ceph-mon-nrpe',
    'ceph-osd',
    'ceph-osd-nrpe',
    'ceph-radosgw',
    'ceph-radosgw-hacluster',
    'ceph-radosgw-nrpe',

    # Identity and Image
    'keystone',
    'keystone-hacluster',
    'keystone-nrpe',

    'glance',
    'glance-hacluster',
    'glance-nrpe',

    # Upgrade nova
    'nova-cloud-controller',
    'nova-cloud-controller-hacluster',
    'nova-cloud-controller-nrpe',

    'nova-compute',
    'nova-compute-nrpe',

    # Neutron upgrades
    'neutron-api',
    'neutron-api-hacluster',
    'neutron-api-nrpe',

    'neutron-gateway',
    'neutron-gateway-nrpe',

    'neutron-openvswitch',

    # Backend block-storage upgrade.
    # Note: just upgrade cinder service.
    'cinder',
    'cinder-hacluster',
    'cinder-warmceph',
    'cinder-nrpe',

    # Upgrade dashboard
    'openstack-dashboard',
    'openstack-dashboard-hacluster',
    'openstack-dashboard-nrpe',

    'rabbitmq-server',
    'rabbitmq-server-nrpe',

    'ntp',

    'mysql',
    'mysql-hacluster',
    'mysql-nrpe'
]
