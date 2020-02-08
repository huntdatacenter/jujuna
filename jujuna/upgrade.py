import asyncio
import logging
import yaml
import websockets
import async_timeout

from collections import Counter

from jujuna.helper import cs_name_parse, connect_juju, log_traceback
from jujuna.settings import ORIGIN_KEYS, SERVICES

from juju.errors import JujuError


# create logger
log = logging.getLogger('jujuna.upgrade')


async def upgrade(
    ctrl_name=None,
    model_name=None,
    apps=[],
    origin='',
    ignore_errors=False,
    pause=False,
    evacuate=False,
    charms_only=False,
    upgrade_only=False,
    upgrade_action='',
    upgrade_params={},
    origin_keys={},
    dry_run=False,
    settings=None,
    endpoint='',
    username='',
    password='',
    cacert='',
    **kwargs
):
    """Upgrade applications deployed in the model.

    Handles upgrade of application deployed in the specified model. Focused on openstack upgrade procedures.

    Connection requires juju client configs to be present locally or specification of credentialls:
    endpoint (e.g. 127.0.0.1:17070), username, password, and model uuid as model_name.

    :param ctrl_name: juju controller
    :param model_name: juju model name or uuid
    :param apps: ordered list of application names
    :param origin: target openstack version string e.g. 'cloud:xenial-ocata'
    :param ignore_errors: boolean
    :param pause: boolean
    :param evacuate: boolean
    :param charms_only: boolean
    :param upgrade_only: boolean
    :param upgrade_action: string
    :param upgrade_params: dict
    :param origin_keys: dict
    :param dry_run: boolean
    :param endpoint: string
    :param username: string
    :param password: string
    :param cacert: string
    """

    controller, model = await connect_juju(
        ctrl_name,
        model_name,
        endpoint=endpoint,
        username=username,
        password=password,
        cacert=cacert
    )

    try:
        log.info('Applications present in the current model: {}'.format(
            ', '.join(list(model.applications.keys()))
        ))

        settings_data = {}

        try:
            if settings:
                with open(settings.name, 'r') as stream:
                    if hasattr(yaml, 'full_load'):
                        settings_data = yaml.full_load(stream)
                    else:
                        settings_data = yaml.load(stream)
        except yaml.YAMLError as e:
            log.warn('Failed to load settings file: {}'.format(str(e)))

        origin_keys = settings_data.get('origin_keys', origin_keys if origin_keys else ORIGIN_KEYS)
        services = settings_data.get('services', SERVICES)
        add_services = settings_data.get('add_services', [])

        # If apps are not specified in the order use configuration from settings
        if apps:
            services = apps
            add_services = []

        log.info('Services to upgrade: {}'.format(', '.join(services)))
        if add_services and not upgrade_only:
            log.info('Charms only upgrade: {}'.format(', '.join(add_services)))
        all_services = [cs_name_parse(serv) for serv in services]
        applications = [serv['charm'] for serv in all_services]
        all_services.extend([cs_name_parse(serv) for serv in add_services])

        # Upgrade charm revisions
        if not upgrade_only:
            upgraded, latest_charms = await upgrade_charms(
                model, all_services, dry_run, ignore_errors
            )

        # Ocata upgrade requires additional relation to succeed
        if not charms_only and origin == 'cloud:xenial-ocata' and 'nova-compute' in applications:
            if 'cinder-warmceph' in applications:
                await ocata_relation_patch(model, dry_run, cinder_ceph='cinder-warmceph')
            elif 'cinder-ceph' in applications:
                await ocata_relation_patch(model, dry_run, cinder_ceph='cinder-ceph')

        # Upgrade applications
        if not charms_only:
            await upgrade_services(
                model, applications, origin, origin_keys, upgrade_action, upgrade_params, pause, dry_run
            )

        # Log status values
        d = Counter([a.status for a in model.applications.values()])
        log.info('STATUS: {}'.format(dict(d)))

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
            await wait_until(
                model,
                model.applications.values(),
                timeout=1800,
                loop=model.loop
            )
            log.info('Completed addition of relation')
        except Exception as e:
            if 'already exists' not in str(e):
                log_traceback(e)
                raise e
            else:
                log.warn('Ignored: relation already exists')


def get_service_list(model, upgraded):
    return [(name, get_service_version(model.applications[name])) for name in upgraded if name in model.applications]


def get_service_version(application):
    try:
        serv_version = application.safe_data.get('workload-version', '')
    except Exception:
        serv_version = ''
    return serv_version


async def upgrade_services(model, upgraded, origin, origin_keys, upgrade_action, upgrade_params, pause, dry_run):
    sl_before = get_service_list(model, upgraded)
    log.info('Application upgrade order: {}'.format(
        ', '.join(['{} ({})'.format(name, version) for name, version in sl_before])
    ))

    s_upgrade = 0
    # upgrade_action is none by default, otherwise enforcing perform_upgrade
    use_action = upgrade_action if upgrade_action else 'openstack-upgrade'
    for app_name in upgraded:
        if app_name not in model.applications:
            continue
        rollable_app = await is_rollable(model.applications[app_name], use_action)
        if upgrade_action or rollable_app:
            await perform_upgrade(
                model,
                model.applications[app_name],
                origin_keys,
                use_action,
                upgrade_params,
                rollable=rollable_app,
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

    sl_after = get_service_list(model, upgraded)
    log.info('Application upgrade order: {}'.format(
        ', '.join(['{} ({}=>{})'.format(before[0], before[1], after[1]) for before, after in zip(sl_before, sl_after)])
    ))
    log.info('Upgrade finished ({} upgraded services)'.format(s_upgrade))


async def upgrade_charms(model, apps, dry_run, ignore_errors):
    """Upgrade charm revisions in the model.

    Listed apps will be checked for new revisions in charmstore
    and upgraded to latest revision if available.

    :param model_name: juju model name or uuid
    :param apps: ordered list of application names
    :param dry_run: boolean
    :param ignore_errors: boolean
    """
    log.info('Upgrading charms')
    upgraded = []
    latest_charms = []
    failed_upgrade = False

    for app_name in apps:
        attemp_update = False
        target_revision = None

        if app_name['charm'] not in model.applications:
            log.warning('Unable to find application: {}'.format(app_name['charm']))
            continue

        # Get charm url and parse current revision
        charm_url = model.applications[app_name['charm']].data['charm-url']
        parse = cs_name_parse(charm_url)
        current_revision = parse['revision'] if parse['revision'] else 0
        app = model.applications[app_name['charm']]

        # Charmstore get latest revision
        if parse.get('charmstore', False):
            try:
                if app_name.get('revision') is None:
                    charmstore_entity = await model.charmstore.entity(
                        parse['charm'], include_stats=False, includes=['revision-info']
                    )
                    # latest = charmstore_entity['Meta']['revision-info']['Revisions'][0]
                    charm_id = cs_name_parse(charmstore_entity['Id'])
                    target_revision = charm_id['revision']
                else:
                    target_revision = app_name['revision']
            except Exception:
                log.warning('Failed loading information from charmstore: {}'.format(charm_url))
                attemp_update = True
        else:
            log.info('Not upgrading local charm: {}'.format(charm_url))

        # Update if not newest or attempt to update if failed to find charmstore latest revision
        if (target_revision is not None and current_revision < target_revision) or attemp_update:
            log.info('Upgrade {} from: {} to: {}'.format(
                app_name['charm'], current_revision,
                'latest' if target_revision is None else target_revision
            ))
            try:
                if not dry_run:
                    await app.upgrade_charm(
                        revision=target_revision
                    )
                    await asyncio.sleep(30)
                upgraded.append(app_name['charm'])
            except JujuError:
                log.warning('Not upgrading: {}'.format(app_name['charm']))
            except Exception:
                log.error('Failed upgrading: {}'.format(app_name['charm']))
                if not ignore_errors:
                    failed_upgrade = True
                    break
        else:
            latest_charms.append(app_name['charm'])

    log.info('Upgraded: {} charms'.format(len(upgraded)))

    if not dry_run and upgraded:
        await asyncio.sleep(20)
        await wait_until(
            model,
            list(model.applications.values()),
            timeout=1800,
            loop=model.loop
        )

    log.info('Collecting final workload status')
    await asyncio.sleep(20)

    wss = Counter()
    wsm = Counter()
    for app in model.applications.values():
        if app.name in apps:
            wss += Counter([u.workload_status for u in app.units])
            wsm += Counter([
                u.workload_status_message for u in app.units if 'ready' not in u.workload_status_message
            ])
    log.info('Status of units after revision upgrade: {}'.format(dict(wss)))
    log.info('Workload messages: {}'.format(dict(wsm)))

    if not ignore_errors and (failed_upgrade or 'error' in wss.keys()):
        raise Exception('Errors during upgrade of charm revisions')
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
                wss = Counter([
                    unit.workload_status for a in apps for unit in a.units
                ])
                log.info('[WAITING] Charm workload status: {}'.format(dict(wss)))

    await asyncio.sleep(2)
    await asyncio.wait_for(_block(log_count), timeout, loop=loop)

    if _disconnected():
        raise websockets.ConnectionClosed(1006, 'no reason')


async def is_rollable(application, upgrade_action):
    """Define whether the application is rollable.

    Application is considered rollable if it provides upgrade action
    (e.g. openstack-upgrade), is deployed with more than 1 units,
    is not ceph and successfuly applies action-managed-upgrade config.

    :param application: juju application
    """
    actions = await enumerate_actions(application)

    if (not upgrade_action) or (upgrade_action not in actions):
        log.warn('Upgrade action "{}" not in actions.'.format(
            upgrade_action
        ))
        return False

    if len(application.units) <= 1:
        return False

    if application.name.lower().count('ceph') > 0:
        log.info('Ceph is not rollable.')
        return False

    if upgrade_action == 'openstack-upgrade' and not await application.set_config(
        {'action-managed-upgrade': 'True'}
    ):
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

    return {}


async def enumerate_actions(application):
    """Enumerate available actions for the applications.

    Returns a list of actions.

    :param application: juju application
    """
    actions = await application.get_actions()
    return actions.keys()


async def order_units(label, units):
    """Determing order of units.

    Returns a list of units beginning with leader.

    :param label: string
    :param units: list of juju units
    """
    log.info('{} - Determining order of units'.format(label))
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

    log.info('{} - Upgrade order is: {} (leader){}{}'.format(
        label,
        leader_unit,
        ', ' if len(ordered) > 1 else '',
        ', '.join([unit.name for unit in ordered if unit.name != leader_unit]),
    ))
    return ordered


async def perform_upgrade(
    model,
    application,
    origin_keys,
    upgrade_action,
    upgrade_params,
    dry_run=False,
    evacuate=False,
    rollable=False,
    pause=False,
    origin='cloud:xenial-ocata'
):
    """Perform upgrade.

    Rolling upgrade is performed on the rollable application.

    :param application: juju application
    :param dry_run: boolean
    :param evacuate: boolean
    :param rollable: boolean
    :param pause: boolean
    :param origin: origin string
    """
    label = application.name.upper()
    log.info('{} - Begin rolling upgrade'.format(label))

    actions = await enumerate_actions(application)
    if origin and not dry_run:
        config_key = origin_keys.get(application.name, 'openstack-origin')
        config = await application.get_config()
        previous = config.get(config_key, {}).get('value', '')

        if previous == origin:
            current = previous
        else:
            await application.set_config({config_key: origin})
            config_timeout = 60
            config_is_set = False
            while config_timeout > 0 and not config_is_set:
                config_timeout = config_timeout - 1
                await asyncio.sleep(5)
                config = await application.get_config()
                current = config.get(config_key, {}).get('value', '')
                config_is_set = current == origin
                log.info('{} - Setting config {} = {} => {}'.format(label, config_key, previous, current))
        log.info('{} - Config {} = {}'.format(label, config_key, current))

    ordered_units = await order_units(label, application.units) if rollable else application.units
    hacluster_pairs = get_hacluster_subordinate_pairs(application) if (rollable and pause) else {}  # TODO see fx

    for unit in ordered_units:
        hacluster_unit = hacluster_pairs.get(unit.name, False)

        if evacuate and application.name == 'nova-compute':
            # NOT IMPLEMENTED
            log.warn('{} - Nova evacuation is not implemented, app will be skipped'.format(label))
            break

        if pause and hacluster_unit:
            # TODO this will pause all the units for hacluster subordinates
            log.info('{} - Pausing service on hacluster subordinate: {}'.format(label, hacluster_unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await hacluster_unit.run_action('pause')
                    await action.wait()
                    log.debug('{} - Service action: {} on unit: {} status: {}'.format(
                        label, unit.name, 'pause', action.status
                    ))
            log.info('{} - Service on hacluster subordinate {} is paused'.format(label, hacluster_unit.name))

        if pause and 'pause' in actions:
            log.info('{} - Pausing service on unit: {}'.format(label, unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await unit.run_action('pause')
                    await action.wait()
                    log.debug('{} - Service action: {} on unit: {} status: {}'.format(
                        label, unit.name, 'pause', action.status
                    ))
            log.info('{} - Service on unit {} is paused'.format(label, unit.name))

        if upgrade_action in actions:
            log.info('{} - Upgrading service for unit: {}'.format(label, unit.name))
            if not dry_run:
                action = await unit.run_action(upgrade_action, **upgrade_params)
                await action.wait()
                log.debug('{} - Service action: {} on unit: {} status: {}'.format(
                    label, unit.name, upgrade_action, action.status
                ))
            log.info('{} - Completed upgrade for unit: {}'.format(label, unit.name))

        if pause and 'resume' in actions:
            log.info('{} - Resuming service on unit: {}'.format(label, unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await unit.run_action('resume')
                    await action.wait()
                    log.debug('{} - Service action: {} on unit: {} status: {}'.format(
                        label, unit.name, 'resume', action.status
                    ))
            log.info('{} - Service on unit {} has resumed'.format(label, unit.name))

        if pause and hacluster_unit:
            # TODO this will resume all the units for hacluster subordinates
            log.info('{} - Resuming service on hacluster subordinate: {}'.format(label, hacluster_unit.name))
            if not dry_run:
                async with async_timeout.timeout(300):
                    action = await hacluster_unit.run_action('resume')
                    await action.wait()
                    log.debug('{} - Service action: {} on unit: {} status: {}'.format(
                        label, unit.name, 'resume', action.status
                    ))
            log.info('{} - Service on hacluster subordinate {} has resumed'.format(label, hacluster_unit.name))

        await wait_until(
            model,
            list(model.applications.values()),
            timeout=1800,
            loop=model.loop
        )
        log.info('{} - Unit {} has finished the upgrade'.format(label, unit.name))
    log.info('{} - Finish rolling upgrade'.format(label))


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
    log.info('Big-bang upgrade: {}'.format(application.name))
    if origin and not dry_run:
        config_key = origin_keys.get(application.name, 'openstack-origin')
        if config_key not in await application.get_config():
            log.warn('Unable to set source/origin during big-bang upgrade for service: {}'.format(application.name))
            log.info('Skipping upgrade for service: {}'.format(application.name))
            return

        log.info('Set {} config {}={}'.format(application.name, config_key, origin))
        await application.set_config({config_key: origin})
        await asyncio.sleep(15)

    if not dry_run:
        upgrade_in_progress = True
        while upgrade_in_progress:
            if any(
                [u.workload_status.lower().find('upgrad') >= 0 for u in application.units]
            ):
                await asyncio.sleep(5)
            else:
                upgrade_in_progress = False
