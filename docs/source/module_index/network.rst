Network module
=================

Network exporter is sourcing `/proc/net/tcp` for information about interfaces and ports attached.

Notation
--------

::

  network:
    port:
      - port_num1
      - port_num2
      - port_num3


Examples
--------

Check if::

  network:
    port:
      - 6789
      - 22

Parameters
----------

========= ======== ========
Parameter Type     Comments
========= ======== ========
port      list     Check list of port numbers (int) whether attached
========= ======== ========
