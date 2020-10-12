Package module
=================


Notation
--------

::

  package:
    - 'pkg_name1'
    - 'pkg_name2'
    - 'pkg_name3'


Examples
--------

Check if::

  package:
    - 'ceph'
    - 'ceph-common'
    - 'lxd'
    - 'lxd-client'


Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
pkg_name  str      Check package name if installed
========= ======== ========
