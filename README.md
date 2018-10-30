# Jujuna

[![Build Status](https://travis-ci.org/huntdatacenter/jujuna.svg?branch=master)](https://travis-ci.org/huntdatacenter/jujuna)
[![Documentation Status](https://readthedocs.org/projects/jujuna/badge/?version=latest)](https://jujuna.readthedocs.io/en/latest/?badge=latest)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jujuna.svg)](https://pypi.org/project/jujuna/)

Continuous deployment, upgrade and testing for Juju.

Maintaining OpenStack deployment is a demanding task. Considerably frequent releases can cause some pain even when using Juju. It is therefore advised to test new releases and upgrade scenarios on a separate but somewhat similar infrastructures in order to discover any issues before doing upgrade on production.

Using Jujuna in your CI pipeline enables you to automate deployment and upgrade scenarios and run specific tests.

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
