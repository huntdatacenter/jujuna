#!/usr/bin/python3

import asyncio
import websockets
import logging
from collections import defaultdict
from jujuna.helper import connect_juju
from juju.errors import JujuError


# create logger
log = logging.getLogger('jujuna.deploy')


async def deploy(
    bundle_file,
    ctrl_name=None,
    model_name=None,
    wait=False,
    endpoint=None,
    username=None,
    password=None
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
    """
    log.info('Reading bundle: {}'.format(bundle_file.name))
    entity_url = 'local:' + bundle_file.name.replace('/bundle.yaml', '')

    controller, model = await connect_juju(
        ctrl_name,
        model_name,
        endpoint=endpoint,
        username=username,
        password=password
    )

    try:
        # Deploy a bundle
        log.info("Deploy: {}".format(entity_url))
        deployed_app = await model.deploy(
            entity_url
        )

        if wait:
            await wait_until(
                model,
                deployed_app,
                loop=model.loop
            )
    except JujuError as e:
        log.info(str(e))
    finally:
        # Disconnect from the api server and cleanup.
        await model.disconnect()
        await controller.disconnect()


async def wait_until(model, deployed_app, log_time=5, timeout=None, wait_period=0.5, loop=None):
    """Blocking with logs.

    Return only after all conditions are true.

    :param model: juju model
    :param deployed_app: juju application
    :param log_time: logging frequency (s)
    :param timeout: blocking timeout (s)
    :param wait_period: waiting time between checks (s)
    :param loop: asyncio event loop
    """
    log_count = 0

    def _disconnected():
        return not (model.is_connected() and model.connection().is_open)

    async def _block(log_count):
        while not _disconnected() and not all(a.status == 'active' for a in deployed_app):
            await asyncio.sleep(wait_period, loop=loop)
            log_count += 0.5
            if log_count % log_time == 0:
                d = defaultdict(int)
                for a in deployed_app:
                    d[a.status] += 1
                log.info('[RUNNING] Machines: {} Apps: {} Stats: {}'.format(
                    len(model.machines),
                    len(model.applications),
                    dict(d)
                ))
    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise websockets.ConnectionClosed(1006, 'no reason')

    d = defaultdict(int)
    for a in deployed_app:
        d[a.status] += 1
    log.info('[DONE] Machines: {} Apps: {} Stats: {}'.format(
        len(model.machines),
        len(model.applications),
        dict(d)
    ))
