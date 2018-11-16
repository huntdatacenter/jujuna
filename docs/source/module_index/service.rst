Service module
=================

Systemd services. Works with `dbus` python module.

Notation
--------

::

  service:
    service-name:
      status: 'running'


Examples
--------

Check if::

  service:
    ceph-mon:
      status: 'running'


Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
name      str      Match service status
========= ======== ========
