#!/usr/bin/python3

import logging
from jujuna.helper import connect_juju, log_traceback, ApperrorTimeout, wait_until
from juju.errors import JujuError
from websockets import ConnectionClosed


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
    error_timeout=None,
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
    ret = 0
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
        if not isinstance(deployed_apps, list):
            deployed_apps = [deployed_apps]

        if wait:
            await wait_until(
                model,
                deployed_apps,
                log,
                loop=model.loop,
                error_timeout=error_timeout
            )
        else:
            log.info('{} - Apps: {}'.format(
                'DEPLOYED',
                len(deployed_apps)
            ))

    except ApperrorTimeout:
        ret = 124
        log.error('FAILED - Application too long in error state')
    except ConnectionClosed as e:
        ret = 1
        log.error('FAILED - Connection closed')
        log_traceback(e)
    except JujuError as e:
        ret = 1
        log.error('JujuError during deploy')
        log_traceback(e)
    finally:
        # Disconnect from the api server and cleanup.
        await model.disconnect()
        await controller.disconnect()
    return ret
