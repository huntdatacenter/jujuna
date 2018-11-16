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
        - 'glance-api'
      network:
        port:
          - 9292
    mysql-db:
      service:
        mysql:
          status: 'running'
