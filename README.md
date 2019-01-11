# Jujuna

[![Build Status](https://travis-ci.org/huntdatacenter/jujuna.svg?branch=master)](https://travis-ci.org/huntdatacenter/jujuna)
[![Documentation Status](https://readthedocs.org/projects/jujuna/badge/?version=latest)](https://jujuna.readthedocs.io/en/latest/?badge=latest)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jujuna.svg)](https://pypi.org/project/jujuna/)

Continuous deployment, upgrade and testing for Juju.

At [HUNT Cloud](https://www.ntnu.edu/huntgenes/hunt-cloud) we run our scientific services based on OpenStack orchestrated by Juju. Such cloud deployments rely on a large set of collaborative softwares, and upgrades can sometimes cause considerable pain. We are therefore introducing Jujuna - a tool to simplify the validation of Juju-based OpenStack upgrades.

New to [Juju](https://jujucharms.com/)? Juju is a cool controller and agent based tool from Canonical to easily deploy and manage applications (called Charms) on different clouds and environments (see [how it works](https://jujucharms.com/how-it-works) for more details).

## Installation

Easy to install using:

```
pip3 install jujuna
```

May require installation of `libssl-dev` package or equivalent if not present in the system.

Run command `jujuna --help` to get the help menu. You can also check the usage in [the documentation](https://jujuna.readthedocs.io/en/latest/usage.html).

## Usage

Running Jujuna requires a working deployment of Juju controller. Juju configs `~/.local/share/juju/` have to be present or credentials have to be specified using params.

```
# Deploy Ceph bundle into ceph model
jujuna deploy openstack/bundle.yaml -m test-cloud -w

# Upgrade apps in ceph model_name
jujuna upgrade -m test-cloud

# Test apps in the model after upgrade
jujuna test tests/openstack-ocata.yaml -t 1800 -m test-cloud

# Destroy apps within a model, without destroying the model
jujuna clean -m test-cloud -w -f -t 1800

```

If you don't have any bundle or just need to try jujuna with some simple example, you can follow our [example guide](https://jujuna.readthedocs.io/en/latest/examples.html).

## Testing Jujuna

How to make sure jujuna and your feature works before pushing out new version.

Testing jujuna with python environments:
```
tox -e lint
tox -e py35
tox -e py36
tox -e py37
```

Testing specific feature:

```
py.test -k test_feature
```

## Deploy to docker registry:

Build image:

```
docker build -t registry.example.com/group/jujuna:0.2.1 -t registry.example.com/group/jujuna:latest .
```

Push to registry:

```
docker push registry.example.com/group/jujuna
```
