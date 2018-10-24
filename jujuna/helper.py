
from jujuna.settings import MAX_FRAME_SIZE

from juju.controller import Controller
from juju.model import Model

from theblues.charmstore import CharmStore


def cs_name_parse(name, series=None):
    """Charm store name parse.

    """
    try:
        cut = name.split(':', 1)[1]
        arr = cut.split('/') if '/' in cut else ['', cut]
        return {
            'series': arr[0] if arr[0] or not series else series,
            'charm': '-'.join(arr[1].split('-')[:-1]),
            'revision': int(arr[1].split('-')[-1])
        }
    except:  # noqa
        print(name)
        return {}


async def connect_juju(ctrl_name=None, model_name=None, endpoint=None, username=None, password=None):
    controller = Controller(max_frame_size=MAX_FRAME_SIZE)  # noqa

    if ctrl_name:
        if endpoint:
            await controller.connect(endpoint=endpoint, username=username, password=password)
        else:
            await controller.connect(ctrl_name)
    else:
        await controller.connect_current()

    if endpoint:
        model = Model(max_frame_size=MAX_FRAME_SIZE)
        await model.connect(uuid=model_name, endpoint=endpoint, username=username, password=password)
    elif model_name:
        model = await controller.get_model(model_name)
    else:
        model = Model(max_frame_size=MAX_FRAME_SIZE)  # noqa
        await model.connect_current()

    # HACK low unsettable timeout in the model
    model.charmstore._cs = CharmStore(timeout=60)

    return controller, model
