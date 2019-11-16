import logging
import traceback

from jujuna.settings import MAX_FRAME_SIZE

from juju.controller import Controller
from juju.model import Model

from theblues.charmstore import CharmStore


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

    """
    try:
        cscode, csuri = name.split(':', 1)
        items = csuri.split('/') if '/' in csuri else ['', csuri]
        return {
            'series': items[0] if items[0] or not series else series,
            'charm': '-'.join(items[1].split('-')[:-1]),
            'revision': int(items[1].split('-')[-1]),
            'charmstore': False if cscode == 'local' else True
        }
    except Exception:
        logging.warn('Failed to parse Charm name: {}'.format(name))
        return {}


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
