Process module
=================

Listing `/proc` for running processes.

Notation
--------

::

  process:
  - '/usr/bin/service'


Examples
--------

Check if::

  process:
  - '/usr/bin/ceph-mon'


Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
service   str      Check process name if running
========= ======== ========
