Try our examples
=================

In the `examples` folder you can find a minimal OpenStack bundle (includes
only Keystone and database) and a test suite.

Testing the bundle requires a working juju controller, in case you don't
have one, you can try our vagrant configuration.

I have Juju Controller
----------------------

First you deploy the Openstack bundle, with older version of keystone
(Newton)::

  jujuna deploy minimal-openstack.bundle.yaml -w

When deploy is done, you can try upgrading Keystone to the next version
(Ocata)::

  jujuna upgrade -o cloud:xenial-ocata -p -a keystone


After the upgrade you want to test our services with a test suite::

  jujuna test minimal-openstack.test.yaml

If the tests were successful you can continue in the pipeline with
upgrading to higher versions (Pike, Queens,...) or you can cleanup
the model and remove all the applications::

  jujuna clean -w

I dont't have Juju controller
-----------------------------

If you don't have a working juju controller available. Deploying one locally
on your device can be a choice for you when trying out `jujuna`::

  cd examples && vagrant up

Connect to vagrant::

  vagrant ssh

You can try to run `juju status` to make sure that the lxd controller is
deployed properly.

When you are in vagrant, you can deploy our example Openstack bundle, with
older version of keystone (Newton)::

  jujuna deploy /vagrant/minimal-openstack.bundle.yaml -w

When deploy is done, you can try upgrading Keystone to the next version
(Ocata)::

  jujuna upgrade -o cloud:xenial-ocata -p -a keystone

After the upgrade you want to test our services with a test suite::

  jujuna test /vagrant/minimal-openstack.test.yaml

If the tests were successful you can continue in the pipeline with
upgrading to higher versions (Pike, Queens,...) or you can cleanup
the model and remove all the applications::

  jujuna clean -w

When you are done with testing you can `exit` the vagrant.
