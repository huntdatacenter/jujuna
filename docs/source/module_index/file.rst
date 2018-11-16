File module
=================

Notation
--------

::

  file:
    'path1':
      param1: value1
      param2: value2
      param3: value3
    'path2':
      param1: value1
      param2: value2


Examples
--------

File `/etc/passwd` exists and is owned by root::

  file:
    '/etc/passwd':
      st_uid: 0
      st_gid: 0
      is_reg: True


Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
st_mode            File type and mode
st_ino
st_dev
st_nlink
st_uid    int      Owners uid
st_gid    int      Owners gid
st_size   int      File size
st_atime
st_mtime
st_ctime
is_dir    Boolean  Is path a dir
is_chrv
is_blk
is_reg    Boolean  Is path a file
is_fifo   Boolean  Is path a fifo
is_lnk    Boolean  Is path a link
is_sock   Boolean  Is path a socket
imode
ifmt
========= ======== ========
