User module
=================


Notation
--------

::

  user:
    user1:
      group: 'user1'
      dir: '/home/user1'


Examples
--------

Check if::

  user:
    ceph:
      group: 'ceph'
      dir: '/var/lib/ceph'


Parameters
----------

========== ======== ========
Parameter  Type     Comments
========== ======== ========
user       str      User existing in pwd file
uid        int      User's uid
gid        int      User's gid
group      str      User's group name
dir        str      Path to user's homedir
gecos      str      A general information about the account
shell      str      User's shell
========== ======== ========
