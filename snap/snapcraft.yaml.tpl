name: jujuna
base: core20
version: "${SNAPCRAFT_PROJECT_VERSION}"
summary: Jujuna, continuous deployment, upgrade and testing for Juju.
description: |
  Jujuna, continuous deployment, upgrade and testing for Juju.

grade: devel
confinement: strict

parts:
  jujuna:
    plugin: python
    requirements:
      - ./requirements.txt
    source: .
apps:
  jujuna:
    command: bin/jujuna
    plugs:
      - network
      - home
