import asyncio
import logging
import traceback
from collections import Counter
from websockets import ConnectionClosed

from jujuna.settings import MAX_FRAME_SIZE

from juju.controller import Controller
from juju.model import Model

from theblues.charmstore import CharmStore


class ApperrorTimeout(Exception):
    """Raised when an application stays too long in error state."""

    def __init__(self):
        self.message = 'Timed out with application in error state'


def log_traceback(ex, prefix=''):
    if prefix and isinstance(prefix, str):
        prefix = '{} - '.format(prefix.strip())
    ex_traceback = ex.__traceback__
    for line in traceback.format_exception(
        ex.__class__, ex, ex_traceback
    ):
        logging.error('{}{}'.format(prefix, line.rstrip('\n')))


def cs_name_parse(name, series=None):
    """Charm store name parse.

    Parse charm name, series, and revision.
    Charmstore variable differs source from local charm.

    :param name string: charm name or url e.g. cs:xenial/glance-35
    :param series string: series name e.g. bionic
    :return dict: with keys series, charm, revision, and charmstore
    """
    try:
        cscode, csuri = name.split(':', 1) if ':' in name else ['cs', name]
        is_path = (cscode == 'local') or csuri.startswith('/') or csuri.startswith('./')
        uri_series, csuri = csuri.split('/', 1) if (
            '/' in csuri and not is_path
        ) else ['', csuri]
        items = csuri.split('-')
        revision = int(items[-1]) if items[-1].isdigit() else None
        return {
            'series': uri_series if uri_series and not series else series,
            'charm': '-'.join(items if revision is None else items[:-1]),
            'revision': revision,
            'charmstore': False if is_path else True
        }
    except Exception:
        logging.warning('Failed to parse Charm name: {}'.format(name))
        return {
            'series': None,
            'charm': name,
            'revision': None,
            'charmstore': False
        }


async def connect_juju(ctrl_name=None, model_name=None, endpoint=None, username=None, password=None, cacert=None):
    controller = Controller(max_frame_size=MAX_FRAME_SIZE)  # noqa

    if endpoint:
        await controller.connect(endpoint=endpoint, username=username, password=password, cacert=cacert)
    else:
        await controller.connect(ctrl_name)

    if endpoint:
        model = Model(max_frame_size=MAX_FRAME_SIZE)
        await model.connect(uuid=model_name, endpoint=endpoint, username=username, password=password, cacert=cacert)
    elif model_name:
        model = await controller.get_model(model_name)
    else:
        model = Model(max_frame_size=MAX_FRAME_SIZE)  # noqa
        await model.connect()

    # HACK low unsettable timeout in the model
    model.charmstore._cs = CharmStore(timeout=60)

    return controller, model


async def wait_until(model, apps, logger, log_time=5, timeout=None, wait_period=0.5, error_timeout=None, loop=None):
    """Blocking with log messages.

    Return only after all conditions are true.

    :param model: juju model
    :param apps: juju application
    :param logger: logger instance
    :param log_time: logging frequency (s)
    :param timeout: blocking timeout (s)
    :param error_timeout: timeout if app persists in error state for set time (s)
    :param wait_period: waiting time between checks (s)
    :param loop: asyncio event loop
    """
    log_count = 0

    def _disconnected():
        return not (model.is_connected() and model.connection().is_open)

    async def _block(log_count):
        blockable = ['maintenance', 'blocked', 'waiting', 'error']
        success_counter = 0
        errors = 0
        # 10 consecutive success checks to pass
        while success_counter < 5:
            success_counter += 1
            while (
                not _disconnected() and
                (
                    any(a.status != 'active' for a in apps) or
                    any(u.workload_status in blockable for a in apps for u in a.units)
                )
            ):
                success_counter = 0  # checks not successful - start again at 0
                log_count += 0.5
                if any(a.status == 'error' for a in apps):
                    errors += wait_period
                if error_timeout and errors >= max(error_timeout, 20):
                    log_workload(
                        logger, model, apps,
                        label='FAILED', error_status=True, status=False, workload=False
                    )
                    raise ApperrorTimeout()
                await asyncio.sleep(wait_period, loop=loop)
                if log_count % log_time == 0:
                    log_workload(logger, model, apps)
            if success_counter != 0:
                # Log if increasing consecutive check count
                if all(a.status != 'error' for a in apps):
                    errors = 0
                await asyncio.sleep(2, loop=loop)
                log_workload(logger, model, apps)

    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise ConnectionClosed(1006, 'no reason')
    else:
        log_workload(logger, model, apps, label='DEPLOYED')


def log_workload(
    logger, model, apps, label='PROGRESS', status=True, workload=True, error_status=False, unit_status=False
):
    if status:
        ass = dict(Counter([a.status if a.status else 'none' for a in apps]))
        ass = 'Status: {}'.format(','.join([
            '{}={}'.format(k, v) for k, v in ass.items()
        ])) if ass else 'Status: None'
    else:
        ass = ''
    if workload:
        wss = Counter([
            unit.workload_status if unit.workload_status else 'none' for a in apps for unit in a.units
        ])
        wss = 'Workload: {}'.format(','.join([
            '{}={}'.format(k, v) for k, v in wss.items()
        ])) if wss else 'Workload: None'
    else:
        wss = ''

    if error_status:
        asm = dict(Counter([a.status_message for a in apps if a.status == 'error']))
        asm = 'Errors: {}'.format(','.join(asm.keys())) if asm else 'Errors: None'
    else:
        asm = ''
    if unit_status:
        wsm = dict(Counter([
            (
                u.workload_status_message if 'ready' not in u.workload_status_message else 'ready'
            ) for a in apps for u in a.units
        ]))
        wsm = 'Units: {}'.format('{}={}'.format(k, v) for k, v in wsm.items()) if wsm else 'Units: None'
    else:
        wsm = ''
    msg = ' '.join([x for x in [ass, wss, asm, wsm] if x])
    logger.info('{} - Machines {} - Apps {} {}'.format(
        label,
        len(model.machines),
        len(model.applications),
        '- {}'.format(msg) if msg else ''
    ))
