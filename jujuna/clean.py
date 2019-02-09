#!/usr/bin/python3

import asyncio
import websockets
import logging
from jujuna.helper import connect_juju
from juju.errors import JujuError


# create logger
log = logging.getLogger('jujuna.clean')


async def wait_until(model, *conditions, log_time=5, timeout=None, wait_period=0.5, loop=None):
    """Return only after all conditions are true.

    """
    log_count = 0

    def _disconnected():
        return not (model.is_connected() and model.connection().is_open)

    async def _block(log_count):
        while not _disconnected() and not all(c() for c in conditions):
            await asyncio.sleep(wait_period, loop=loop)
            log_count += 0.5
            if log_count % log_time == 0:
                log.info('[RUNNING] Machines: {} {} Apps: {}'.format(
                    len(model.machines),
                    ', '.join(model.machines.keys()),
                    len(model.applications)
                ))
    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise websockets.ConnectionClosed(1006, 'no reason')

    log.info('[DONE] Machines: {} Apps: {}'.format(
        len(model.machines),
        len(model.applications)
    ))


async def clean(
    ctrl_name=None,
    model_name=None,
    ignore=[],
    wait=False,
    force=False,
    dry_run=False,
    endpoint=None,
    username=None,
    password=None
):
    """Destroy applications present in the current or selected model.

    Connection requires juju client configs to be present locally or specification of credentialls:
    endpoint (e.g. 127.0.0.1:17070), username, password, and model uuid as model_name.

    :param ctrl_name: juju controller
    :param model_name: juju model name or uuid
    :param ignore: list of application names
    :param wait: boolean
    :param force: boolean
    :param dry_run: boolean
    :param endpoint: string
    :param username: string
    :param password: string
    """
    controller, model = await connect_juju(
        ctrl_name,
        model_name,
        endpoint=endpoint,
        username=username,
        password=password
    )

    try:
        # Remove all the apps
        for app in model.applications:
            if app in ignore:
                log.info('Ignoring {}'.format(app))
            else:
                log.info('Remove {} from model'.format(app))
                if not dry_run:
                    await model.applications[app].destroy()

        if not ignore and force:
            machines = [m for m in model.machines.values() if 'arch' in m.safe_data['hardware-characteristics']]
            for machine in machines:
                log.info('Remove machine {} from model'.format(machine.entity_id))
                if not dry_run:
                    try:
                        await machine.destroy(force=True)
                    except Exception as e:
                        log.warn('ERROR: {}'.format(e))

        if wait and not ignore and not dry_run:
            await wait_until(
                model,
                lambda: model.applications == {} and model.machines == {},
                loop=model.loop
            )

    except JujuError as e:
        log.info(e.message)
    finally:
        # Disconnect from the api server and cleanup.
        await model.disconnect()
        await controller.disconnect()
