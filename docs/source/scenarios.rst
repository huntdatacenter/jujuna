Scenarios
=================

Describing 3 major cases of jujuna usage.

Deploy juju bundle -> Upgrade -> Test -> Improve

Case 1: CI
----------

Test on configuration changed (part of bundle repo CI). Everytime the bundle is
changed it can be automatically tested using jujuna.

Case 2: Revision upgrade
------------------------

Test on update - new charm revisions (even nightlies). You can regularly run
jujuna to test new or nightly release of charm revisions.

Case 3: Service upgrade
-----------------------

Test before upgrade. Whenever there is a need to upgrade production, you can
easily redeploy development/testing stack.
