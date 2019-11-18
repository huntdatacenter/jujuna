#!/usr/bin/python3

import asyncio
import websockets
import logging
from collections import Counter
from jujuna.helper import connect_juju, log_traceback
from juju.errors import JujuError


# create logger
log = logging.getLogger('jujuna.deploy')


async def deploy(
    bundle_file,
    ctrl_name='',
    model_name='',
    wait=False,
    endpoint='',
    username='',
    password='',
    cacert='',
    **kwargs
):
    """Deploy a local juju bundle.

    Handles deployment of a bundle file to the current or selected model.

    Connection requires juju client configs to be present locally or specification of credentialls:
    endpoint (e.g. 127.0.0.1:17070), username, password, and model uuid as model_name.

    :param bundle_file: juju bundle file
    :param ctrl_name: juju controller
    :param model_name: juju model name or uuid
    :param wait: boolean
    :param endpoint: string
    :param username: string
    :param password: string
    :param cacert: string
    """
    log.info('Reading bundle: {}'.format(bundle_file.name))
    entity_url = 'local:' + bundle_file.name.replace('/bundle.yaml', '')

    controller, model = await connect_juju(
        ctrl_name,
        model_name,
        endpoint=endpoint,
        username=username,
        password=password,
        cacert=cacert
    )

    try:
        # Deploy a bundle
        log.info("Deploy: {}".format(entity_url))
        deployed_apps = await model.deploy(
            entity_url
        )

        if wait:
            await wait_until(
                model,
                deployed_apps,
                loop=model.loop
            )
        try:
            d = Counter([a.status for a in deployed_apps])
        except Exception:
            log.error('Collecting status failed')
            d = {}
        log.info('{} - Machines: {} Apps: {} Stats: {}'.format(
            'DEPLOYED' if wait else 'CURRENT',
            len(model.machines),
            len(model.applications),
            dict(d)
        ))

    except JujuError as e:
        log.error('JujuError during deploy')
        log_traceback(e)
    finally:
        # Disconnect from the api server and cleanup.
        await model.disconnect()
        await controller.disconnect()


async def wait_until(model, apps, log_time=5, timeout=None, wait_period=0.5, loop=None):
    """Blocking with logs.

    Return only after all conditions are true.

    :param model: juju model
    :param apps: juju application
    :param log_time: logging frequency (s)
    :param timeout: blocking timeout (s)
    :param wait_period: waiting time between checks (s)
    :param loop: asyncio event loop
    """
    log_count = 0

    def _disconnected():
        return not (model.is_connected() and model.connection().is_open)

    async def _block(log_count):
        blockable = ['maintenance', 'blocked', 'waiting', 'error']
        while (
            not _disconnected() and
            any(a.status != 'active' for a in apps) and
            any(u.workload_status in blockable for a in apps for u in a.units)
        ):
            await asyncio.sleep(wait_period, loop=loop)
            log_count += 0.5
            if log_count % log_time == 0:
                ass = Counter([
                    a.status for a in apps
                ])
                wss = Counter([
                    unit.workload_status for a in apps for unit in a.units
                ])
                log.info('PROGRESS - Machines: {} Apps: {} Stats: {} Workload: {}'.format(
                    len(model.machines),
                    len(model.applications),
                    dict(ass),
                    dict(wss)
                ))
    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise websockets.ConnectionClosed(1006, 'no reason')
