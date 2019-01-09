.. Jujuna documentation master file, created by
   sphinx-quickstart on Wed Sep 26 16:04:49 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Jujuna's documentation!
==================================

Continuous integration of Juju bundles that provides deployment, upgrade and
testing options.

At `HUNT Cloud <https://www.ntnu.edu/huntgenes/hunt-cloud>`_, we run our
scientific services based on OpenStack orchestrated by Juju. Such cloud
deployments rely on a large set of collaborative softwares, and upgrades can
sometimes cause considerable pain. We are therefore introducing Jujuna - a tool
to simplify the validation of Juju-based OpenStack upgrades.

New to `Juju <https://jujucharms.com/>`_? Juju is a cool controller and agent
based tool from Canonical to easily deploy and manage applications (called
Charms) on different clouds and environments (see
`how it works <https://jujucharms.com/how-it-works>`_ for more details).

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
   examples
   usecases
   test_writing/index

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
