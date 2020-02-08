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
