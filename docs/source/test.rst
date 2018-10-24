Tests
=================

Jujuna tests are designed to validate configuration of infrastructure in a fast
way. It is able to discover many common issues, that do not appear in Juju
status or during upgrade procedure.


Test suite is a declarative config of infrastructure. Status is declared by
referencing brokers and their variables.

Brokers are modules that are using exporters to extract specific information
from units. They represent important system values.
Exporters are modules that read and export information from units to brokers.
There the information is evaluated.

Test brokers/exporters (named respectively):

- api
- file
- mount
- network
- package
- process
- service
- user

.. automodule:: jujuna.tests
   :members: test
