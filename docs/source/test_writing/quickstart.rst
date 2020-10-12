Quickstart
=================


Format: `yaml`

Example 1 - Bundle of glance and openstack::

    glance:
      service:
        glance-api:
          status: 'running'
        glance-registry:
          status: 'running'
      process:
        glance-api: True
      network:
        port:
          '9292': True
    mysql-db:
      service:
        mysql:
          status: 'running'
