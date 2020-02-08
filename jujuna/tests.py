import time  # noqa
import yaml
import json
import logging
import async_timeout
from collections import defaultdict
from juju.errors import JujuError
from jujuna.helper import connect_juju, log_traceback

from jujuna.brokers.api import Api as ApiBroker
from jujuna.brokers.file import File as FileBroker
from jujuna.brokers.mount import Mount as MountBroker
from jujuna.brokers.network import Network as NetworkBroker
from jujuna.brokers.package import Package as PackageBroker
from jujuna.brokers.process import Process as ProcessBroker
from jujuna.brokers.service import Service as ServiceBroker
from jujuna.brokers.user import User as UserBroker


# create logger
log = logging.getLogger('jujuna.tests')


async def test(
    test_suite='',
    ctrl_name='',
    model_name='',
    endpoint='',
    username='',
    password='',
    cacert='',
    **kwargs
):
    """Run a test suite against applications deployed in the current or selected model.

    Applications are tested with declarative parameters specified in the test suite using the available brokers.

    Connection requires juju client configs to be present locally or specification of credentialls:
    endpoint (e.g. 127.0.0.1:17070), username, password, and model uuid as model_name.

    :param test_suite: suite file (Yaml)
    :param ctrl_name: juju controller
    :param model_name: juju model name or uuid
    :param endpoint: string
    :param username: string
    :param password: string
    :param cacert: string
    """
    log.info('Load tests')
    if test_suite:
        with open(test_suite.name, 'r') as stream:
            try:
                if hasattr(yaml, 'full_load'):
                    suite = yaml.full_load(stream)
                else:
                    suite = yaml.load(stream)
                suite_apps = suite.keys()
            except yaml.YAMLError as exc:
                log.error(exc)
                suite_apps = []

    log.info('Applications: {}'.format(', '.join(suite_apps)))

    controller, model = await connect_juju(
        ctrl_name,
        model_name,
        endpoint=endpoint,
        username=username,
        password=password,
        cacert=cacert
    )

    model_passed, model_failed = 0, 0
    failed_units = set()

    try:
        for app_name, app in model.applications.items():
            if suite and app_name in suite:
                app_passed, app_failed = 0, 0
                try:
                    test_cases = len([
                        key for x in suite[app_name].values() for y in x.values() if isinstance(x, dict) for key in y
                    ])
                except Exception:
                    test_cases = 0
                log.info('{} - {} - {} units - {} tests - {} {}'.format(
                    "----", app_name, len(app.units), test_cases, app.status, app.alive
                ))
                for idx, unit in enumerate(app.units):
                    async with async_timeout.timeout(60):
                        passed, failed = await execute_brokers(suite[app_name], unit, idx)
                        app_passed += passed
                        app_failed += failed
                        if app.status in ['error', 'maintenance', 'blocked'] or failed:
                            failed_units.add(unit.name)
                model_passed += app_passed
                model_failed += app_failed
                log.info('{} - {}: Passed tests: {}'.format("====", app_name, app_passed))
                log.info('{} - {}: Failed tests: {}'.format("====", app_name, app_failed))

        alive = defaultdict(int)
        status = defaultdict(int)
        for app in model.applications.values():
            alive[app.alive] += 1
            status[app.status] += 1

        if (
            False not in alive and
            all(s in ['active', 'waiting'] for s in status.keys())
        ):
            log.info('All juju apps state to be alive and active.')
        else:
            log.warning('Finished with errors')
            log.warning('Alive: {}'.format(dict(alive)))
            log.warning('Status: {}'.format(dict(status)))

        log.info('{}: {}'.format("Passed tests", model_passed))
        if model_failed:
            log.warning('{}: {}'.format("Failed tests", model_failed))
        else:
            log.info('{}: {}'.format("Failed tests", model_failed))

    except JujuError as e:
        log.error('JujuError during tests')
        log_traceback(e)
    finally:
        # Disconnect from the api server and cleanup.
        await model.disconnect()
        await controller.disconnect()

    if failed_units:
        log.error('Failed units: {}'.format(', '.join(sorted(failed_units))))
        return 1


def python3(file):
    return 'python3 {}'.format(file)


def load_output(results):
    """Load json result from broker.

    """
    if results['Code'] == '0':
        try:
            var = json.loads(results['Stdout'])
        except Exception as e:
            raise Exception('JSON load failed: {}'.format(e))
    else:
        raise Exception('Operation failed: {}'.format(results['Stderr']))
    return var


async def execute_brokers(app_test_suite, unit, idx):
    """Iterate brokers and acquire results.

    """
    broker_map = {
        'api': ApiBroker,
        'file': FileBroker,
        'mount': MountBroker,
        'network': NetworkBroker,
        'package': PackageBroker,
        'process': ProcessBroker,
        'service': ServiceBroker,
        'user': UserBroker,
    }
    passed = 0
    failed = 0

    for test_case in app_test_suite.keys():
        if test_case in broker_map.keys():
            # log.info('{} - {}: {}'.format("unit", unit.entity_id, test_case))
            rows = await broker_map[test_case]().run(app_test_suite[test_case], unit, idx)
            for row in rows:
                if row[2]:
                    log.info('{} - {}: {} {}'.format("PASS", unit.entity_id, test_case, row[1]))
                    passed += 1
                else:
                    log.info('{} - {}: {} {}'.format("FAIL", unit.entity_id, test_case, row[1]))
                    failed += 1
        else:
            log.warning("TEST: Skipped (Broker '{}' not registered)".format(test_case))
    return passed, failed
