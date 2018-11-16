Mount module
=================



Notation
--------

::

  mount:
    regex:
      - 'path/sda1-[a-z0-9]+-[0-9]+'
      - 'path/sda2-[a-z0-9]+-[0-9]+'
      - 'path/sda3-[a-z0-9]+-[0-9]+'


Examples
--------

Check if `lxd/containers/juju-2g34g34-1` is mounted::

  mount:
    regex:
    - 'lxd/containers/juju-[a-z0-9]+-[0-9]+'


Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
regex     str      Match regex string in mounts
========= ======== ========
