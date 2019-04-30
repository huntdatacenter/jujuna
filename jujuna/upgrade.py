import asyncio
import logging
import yaml
import websockets
import async_timeout

from collections import defaultdict

from jujuna.helper import cs_name_parse, connect_juju
from jujuna.settings import ORIGIN_KEYS, SERVICES

from juju.errors import JujuError


# create logger
log = logging.getLogger('jujuna.upgrade')


async def upgrade(
    ctrl_name=None,
    model_name=None,
    apps=[],
    origin='cloud:xenial-ocata',
    ignore_errors=False,
    pause=False,
    evacuate=False,
    charms_only=False,
    upgrade_only=False,
    dry_run=False,
    settings=False,
    endpoint=None,
    username=None,
    password=None
):
    """Upgrade applications deployed in the model.

    Handles upgrade of application deployed in the specified model. Focused on openstack upgrade procedures.

    Connection requires juju client configs to be present locally or specification of credentialls:
    endpoint (e.g. 127.0.0.1:17070), username, password, and model uuid as model_name.

    :param ctrl_name: juju controller
    :param model_name: juju model name or uuid
    :param apps: ordered list of application names
    :param origin: target openstack version string
    :param ignore_errors: boolean
    :param pause: boolean
    :param evacuate: boolean
    :param charms_only: boolean
    :param upgrade_only: boolean
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
        log.info('Applications present in the current model: {}'.format(', '.join(list(model.applications.keys()))))

        settings_data = {}

        try:
            if settings:
                with open(settings.name, 'r') as stream:
                    settings_data = yaml.load(stream)
        except yaml.YAMLError as e:
            log.warn('Failed to load settings file: {}'.format(str(e)))

        origin_keys = settings_data['origin_keys'] if 'origin_keys' in settings_data else ORIGIN_KEYS
        services = settings_data['services'] if 'services' in settings_data else SERVICES
        add_services = settings_data['add_services'] if 'add_services' in settings_data else []

        # If apps are not specified in the order use configuration from settings
        if apps:
            services = apps
            add_services = []

        log.info('Services to upgrade: {}'.format(services))
        if add_services:
            log.info('Charms only upgrade: {}'.format(add_services))

        log.info('Upgrading charms')

        # Upgrade charm revisions
        upgraded, latest_charms = await upgrade_charms(model, services + add_services, upgrade_only, dry_run)

        wss = defaultdict(int)
        wsm = defaultdict(int)
        for app in model.applications.values():
            for unit in app.units:
                wss[unit.workload_status] += 1
                if 'ready' not in unit.workload_status_message:
                    wsm[unit.workload_status_message] += 1
        log.info('Status of units after revision upgrade: {}'.format(dict(wss)))
        log.info('Workload messages: {}'.format(dict(wsm)))

        if not ignore_errors and 'error' in wss.keys():
            raise Exception('Errors during upgrading charms to latest revision')

        # Ocata upgrade requires additional relation to succeed
        if not charms_only and origin == 'cloud:xenial-ocata' and 'nova-compute' in services:
            if 'cinder-warmceph' in services:
                await ocata_relation_patch(model, dry_run, cinder_ceph='cinder-warmceph')
            elif 'cinder-ceph' in services:
                await ocata_relation_patch(model, dry_run, cinder_ceph='cinder-ceph')

        # Upgrade services
        if not charms_only:
            await upgrade_services(model, services, origin, origin_keys, pause, dry_run)

        # Log status values
        d = defaultdict(int)
        for a in model.applications.values():
            d[a.status] += 1
        log.info('[STATUS] {}'.format(dict(d)))

    finally:
        await model.disconnect()
        await controller.disconnect()


async def ocata_relation_patch(model, dry_run, cinder_ceph):
    cinder_ceph_rel = '{}:ceph-access'.format(cinder_ceph)
    log.info('Adding relation between nova-compute:ceph-access and {}'.format(cinder_ceph_rel))
    if not dry_run:
        try:
            await model.add_relation('nova-compute:ceph-access', cinder_ceph_rel)
            # TODO add completion check
            await asyncio.sleep(120)
            log.info('Completed addition of relation')
        except Exception as e:
            if 'already exists' not in str(e):
                raise e
            else:
                log.warn('Ignored: relation already exists')

    await wait_until(
        model,
        model.applications.values(),
        timeout=1800,
        loop=model.loop
    )


async def upgrade_services(model, upgraded, origin, origin_keys, pause, dry_run):
    log.info('Upgrading services')

    s_upgrade = 0
    for app_name in upgraded:
        if await is_rollable(model.applications[app_name]):
            await perform_rolling_upgrade(
                model.applications[app_name],
                origin_keys,
                origin=origin,
                pause=pause,
                dry_run=dry_run
            )
            s_upgrade += 1
        else:
            await perform_bigbang_upgrade(
                model.applications[app_name],
                origin_keys,
                origin=origin,
                dry_run=dry_run
            )
            s_upgrade += 1

    await wait_until(
        model,
        model.applications.values(),
        timeout=1800,
        loop=model.loop
    )

    log.info('Upgrade finished ({} upgraded services)'.format(s_upgrade))


async def upgrade_charms(model, apps, upgrade_only, dry_run):
    """Upgrade charm revisions in the model.

    Listed apps will be checked for new revisions in charmstore
    and upgraded to latest revision if available.

    :param model_name: juju model name or uuid
    :param apps: ordered list of application names
    :param origin: target openstack version string
    :param upgrade_only: boolean
    :param dry_run: boolean
    """
    upgraded = []
    latest_charms = []

    for app_name in apps:
        if app_name not in model.applications:
            log.warn('Unable to find application: {}'.format(app_name))
            continue

        # Get charm url and parse current revision
        charm_url = model.applications[app_name].data['charm-url']
        parse = cs_name_parse(charm_url)

        # Charmstore get latest revision
        try:
            charmstore_entity = await model.charmstore.entity(
                charm_url,
                include_stats=False,
                includes=['revision-info']
            )
            latest = charmstore_entity['Meta']['revision-info']['Revisions'][0]
            latest_revision = cs_name_parse(latest)
            attemp_update = False
        except Exception:
            log.warn('Failed loading information from charmstore: {}'.format(charm_url))
            latest_revision = {'revision': 0}
            attemp_update = True

        # Update if not newest or attempt to update if failed to find charmstore latest revision
        if (
            not upgrade_only and
            parse['revision'] < latest_revision['revision'] or
            attemp_update
        ):
            log.info('Upgrade {} from: {} to: {}'.format(app_name, parse['revision'], latest_revision['revision']))
            try:
                if not dry_run:
                    await model.applications[app_name].upgrade_charm()
                    await asyncio.sleep(30)
                upgraded.append(app_name)
            except JujuError:
                log.warn('Not upgrading: {}'.format(app_name))
        else:
            latest_charms.append(app_name)

    log.info('Upgraded: {} charms'.format(len(upgraded)))

    await wait_until(
        model,
        model.applications.values(),
        timeout=1800,
        loop=model.loop
    )

    log.info('Collecting final workload status')
    if not dry_run and upgraded:
        await asyncio.sleep(30)

    return upgraded, latest_charms


async def wait_until(model, apps, log_time=10, timeout=None, wait_period=0.5, loop=None):
    """Blocking with logs.

    Return only after all conditions are true.
    Waiting for maintenance units to become active.

    :param model: juju model
    :param apps: list of juju applications
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
        while not _disconnected() and any(u.workload_status in blockable for a in apps for u in a.units):
            await asyncio.sleep(wait_period, loop=loop)
            log_count += 0.5
            if log_count % log_time == 0:
                wss = defaultdict(int)
                for app in model.applications.values():
                    for unit in app.units:
                        wss[unit.workload_status] += 1
                log.info('[WAITING] Charm workload status: {}'.format(dict(wss)))
    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise websockets.ConnectionClosed(1006, 'no reason')


async def is_rollable(application):
    """Define whether the application is rollable.

    Application is considered rollable if it provides openstack-upgrade action, is deployed with more than 1 units,
    is not ceph and successfuly applies action-managed-upgrade config.

    :param application: juju application
    """
    actions = await enumerate_actions(application)

    if 'openstack-upgrade' not in actions:
        return False

    if len(application.units) <= 1:
        return False

    if application.name.lower().count('ceph') > 0:
        log.info('Ceph is not rollable.')
        return False

    if not await application.set_config({'action-managed-upgrade': 'True'}):
        log.warn('Failed to enable action-managed-upgrade mode.')
        return False

    return True


def get_hacluster_subordinate_pairs(application):
    """Get hacluster subordinate pairs.

    Match hacluster subordinates into unit pairs, as they are respectively deployed.

    :param application: juju application
    """
    # TODO get app or unit? How are the relations described?
    # unit to unit relation missing in libjuju?!
    for relation in application.relations:
        if relation.is_subordinate and relation.provides.interface == 'hacluster':
            sub = relation.provides.application
            sub_pairs = {}
            # HACK (matus) only matching relation is IP address of unit and its subordinate
            # TODO machine id is not provided for subordinates in libjuju
            for unit in application.units:
                for sub_unit in sub.units:
                    if unit.data['public-address'] == sub_unit.data['public-address']:
                        sub_pairs[unit.name] = sub_unit
            return sub_pairs

    return None


async def enumerate_actions(application):
    """Enumerate available actions for the applications.

    Returns a list of actions.

    :param application: juju application
    """
    actions = await application.get_actions()
    return actions.keys()


async def order_units(name, units):
    """Determing order of units.

    Returns a list of units beginning with leader.

    :param name: string
    :param units: list of juju units
    """
    log.info('Determining ordering for service: {}'.format(name))
    ordered = []

    is_leader_data = []
    for unit in units:
        is_leader_data.append(await unit.run('is-leader'))

    leader_info = filter(
        lambda u: u.data['results']['Stdout'].strip() == 'True',
        is_leader_data
    )
    leader_unit = [x.data['receiver'] for x in leader_info][0]

    for unit in units:
        if unit.name == leader_unit:
            ordered.insert(0, unit)
        else:
            ordered.append(unit)

    log.info('Upgrade order is: {} Leader: {}'.format(
        ', '.join([unit.name for unit in ordered]),
        leader_unit
    ))
    return ordered


async def perform_rolling_upgrade(
    application,
    origin_keys,
    dry_run=False,
    evacuate=False,
    pause=False,
    origin='cloud:xenial-ocata'
):
    """Perform rolling upgrade.

    Rolling upgrade is performed on the rollable application.

    :param application: juju application
    :param dry_run: boolean
    :param evacuate: boolean
    :param pause: boolean
    :param origin: origin string
    """

    actions = await enumerate_actions(application)
    if not dry_run:
        config_key = origin_keys.get(application.name, 'openstack-origin')
        await application.set_config({config_key: origin})

    ordered_units = await order_units(application.name, application.units)
    hacluster_pairs = get_hacluster_subordinate_pairs(application)  # TODO see fx

    for unit in ordered_units:
        if hacluster_pairs:
            hacluster_unit = hacluster_pairs.get(unit.name, None)
        else:
            hacluster_unit = None

        if evacuate and application.name == 'nova-compute':
            # NOT IMPLEMENTED
            log.warn('Nova evacuation is not implemented and will be skipped')

        if pause and hacluster_unit:
            # TODO this will pause all the units for hacluster subordinates
            log.info('Pausing service on hacluster subordinate: {}'.format(hacluster_unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await hacluster_unit.run_action('pause')
                    await application.model.wait_for_action(action.entity_id)
            log.info('Service on hacluster subordinate {} is paused'.format(hacluster_unit.name))

        if pause and 'pause' in actions:
            log.info('Pausing service on unit: {}'.format(unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await unit.run_action('pause')
                    await application.model.wait_for_action(action.entity_id)
            log.info('Service on unit {} is paused'.format(unit.name))

        if 'openstack-upgrade' in actions:
            log.info('Upgrading OpenStack for unit: {}'.format(unit.name))
            if not dry_run:
                action = await unit.run_action('openstack-upgrade')
                await application.model.wait_for_action(action.entity_id)
            log.info('Completed upgrade for unit: {}'.format(unit.name))

        if pause and 'resume' in actions:
            log.info('Resuming service on unit: {}'.format(unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await unit.run_action('resume')
                    await application.model.wait_for_action(action.entity_id)
            log.info('Service on unit {} has resumed'.format(unit.name))

        if pause and hacluster_unit:
            # TODO this will resume all the units for hacluster subordinates
            log.info('Resuming service on hacluster subordinate: {}'.format(hacluster_unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await hacluster_unit.run_action('resume')
                    await application.model.wait_for_action(action.entity_id)
            log.info('Service on hacluster subordinate {} has resumed'.format(hacluster_unit.name))

        log.info('Unit {} has finished the upgrade'.format(unit.name))


async def perform_bigbang_upgrade(
    application,
    origin_keys,
    dry_run=False,
    pause=False,
    origin='cloud:xenial-ocata'
):
    """Perform bigbang upgrade.

    Bigbang upgrade is performed on units of the application at once.

    :param application: juju application
    :param dry_run: boolean
    :param pause: boolean
    :param origin: origin string
    """
    log.info('Performing a big-bang upgrade for service: {}'.format(application.name))
    if not dry_run:
        config_key = origin_keys.get(application.name, 'openstack-origin')
        if config_key not in await application.get_config():
            log.warn('Unable to set source/origin during big-bang upgrade for service: {}'.format(application.name))
            log.info('Skipping upgrade for service: {}'.format(application.name))
            return

        log.info('Set {} config {}={}'.format(application.name, config_key, origin))
        await application.set_config({config_key: origin})
        await asyncio.sleep(15)

        upgrade_in_progress = True
        while upgrade_in_progress:
            # service = Juju.current().get_service(service.name)
            # unit_uip = [u.is_upgrading() for u in service.units()]
            unit_uip = [u.workload_status.lower().find('upgrad') >= 0 for u in application.units]
            upgrade_in_progress = any(unit_uip)
            if upgrade_in_progress:
                await asyncio.sleep(5)
