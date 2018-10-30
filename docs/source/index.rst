.. Jujuna documentation master file, created by
   sphinx-quickstart on Wed Sep 26 16:04:49 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Jujuna's documentation!
==================================

Continuous integration of Juju bundles that provides deployment, upgrade and
testing options.

Maintaining OpenStack deployment is a demanding task. Considerably frequent
releases can cause some pain even when using Juju. It is therefore advised
to test new releases and upgrade scenarios on a separate but somewhat similar
infrastructures in order to discover any issues before undergoing upgrade
of production services.

Using Jujuna in your CI pipeline enables you to automate deployment and upgrade
scenarios and run specific tests.


Quickstart
==========

.. _installation-guide:

Installation
------------

To install Jujuna, open an interactive shell and run:

.. code::

    pip3 install jujuna

.. note::

    It is **very** important to install Jujuna on the Python 3.5 (or higher),
    you need it to be installed at least on 3.5 because of the main features
    used in Jujuna and it's dependencies.


.. toctree::
   :maxdepth: 2

   usage
   scenarios
   test_writing

.. toctree::
   :maxdepth: 2
   :caption: Modules:

   deploy
   upgrade
   test
   clean


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
