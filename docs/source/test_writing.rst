Writing tests
=================

Examples and guides on how to write test suites for jujuna.

Format: `yaml`

Example 1 - Service module::

    glance:
      service:
        glance-api:
          status: 'running'
        glance-registry:
          status: 'running'
