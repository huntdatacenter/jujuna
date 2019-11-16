"""
Tests for upgrade action.

"""

from jujuna.upgrade import perform_upgrade
from unittest.mock import patch
from unittest import TestCase
from collections import namedtuple
from .asyncio_mocks import AsyncMock, AsyncClassMock, loop
from jujuna.upgrade import logging
logging.disable(logging.CRITICAL)


def unit_mock(**kwargs):
    namedtuple('Unit', ['name'])


class TestUpgrade(TestCase):
    """Test upgrade action.

    """

    @patch('asyncio.sleep', new=AsyncMock())
    @patch('jujuna.upgrade.wait_until', new=AsyncMock())
    @patch('jujuna.upgrade.enumerate_actions', new=AsyncMock(return_value=['openstack-upgrade']))
    def test_perform_upgrade_simple(
        self  # , get_hacluster_subordinate_pairs
    ):
        """Testing upgrade parser."""
        from jujuna.upgrade import wait_until
        from jujuna.upgrade import enumerate_actions

        origin_previous = 'cloud:xenial-newton'
        origin = 'cloud:xenial-ocata'
        upgrade_action = 'openstack-upgrade'
        ORIGIN_CONFIG = [{'openstack-origin': {'value': origin}}, {'openstack-origin': {'value': origin_previous}}]

        def func(*args, **kwargs):
            return ORIGIN_CONFIG.pop()

        unit = AsyncClassMock(static=['run_action'], props={'name': 'test/0'})
        app = AsyncClassMock(
            static=['set_config', 'get_config'],
            props={'name': 'test', 'units': [unit], 'relations': []}
        )
        model = AsyncClassMock(props={'applications': {'test': app}, 'loop': None})

        app.get_config.mock.side_effect = func
        unit.run_action.mock.return_value = AsyncClassMock(
            static=['wait', 'status'],
            props={'results': 'results'}
        )

        loop(perform_upgrade(
            model,
            app,
            {},
            upgrade_action,
            {},
            dry_run=False,
            evacuate=False,
            rollable=False,
            pause=True,
            origin=origin
        ))
        app.set_config.mock.assert_called_once_with({'openstack-origin': origin})
        enumerate_actions.mock.assert_called_once_with(app)
        unit.run_action.mock.assert_called_once_with(upgrade_action)
        wait_until.mock.assert_called_once_with(model, list(model.applications.values()), loop=None, timeout=1800)

    @patch('asyncio.sleep', new=AsyncMock())
    @patch('jujuna.upgrade.get_hacluster_subordinate_pairs')
    @patch('jujuna.upgrade.wait_until', new=AsyncMock())
    @patch('jujuna.upgrade.order_units', new=AsyncMock())
    @patch('jujuna.upgrade.enumerate_actions', new=AsyncMock(return_value=['openstack-upgrade', 'pause', 'resume']))
    def test_perform_upgrade_rolling(
        self, get_hacluster_subordinate_pairs
    ):
        """Testing upgrade parser."""
        from jujuna.upgrade import wait_until
        from jujuna.upgrade import order_units
        from jujuna.upgrade import enumerate_actions

        origin_previous = 'cloud:xenial-newton'
        origin = 'cloud:xenial-ocata'
        upgrade_action = 'openstack-upgrade'
        ORIGIN_CONFIG = [{'openstack-origin': {'value': origin}}, {'openstack-origin': {'value': origin_previous}}]

        def func(*args, **kwargs):
            return ORIGIN_CONFIG.pop()

        unit = AsyncClassMock(static=['run_action'], props={'name': 'test/0'})
        app = AsyncClassMock(
            static=['set_config', 'get_config'],
            props={'name': 'test', 'units': [unit], 'relations': []}
        )
        model = AsyncClassMock(props={'applications': {'test': app}, 'loop': None})

        get_hacluster_subordinate_pairs.return_value = {}
        app.get_config.mock.side_effect = func
        order_units.mock.return_value = [unit]
        unit.run_action.mock.return_value = AsyncClassMock(
            static=['wait', 'status'],
            props={'results': 'results'}
        )

        loop(perform_upgrade(
            model,
            app,
            {},
            upgrade_action,
            {},
            dry_run=False,
            evacuate=False,
            rollable=True,
            pause=True,
            origin=origin
        ))
        app.set_config.mock.assert_called_once_with({'openstack-origin': origin})
        enumerate_actions.mock.assert_called_once_with(app)
        order_units.mock.assert_called_once_with(app.name, app.units)
        unit.run_action.mock.assert_any_call('pause')
        unit.run_action.mock.assert_any_call(upgrade_action)
        unit.run_action.mock.assert_called_with('resume')
        wait_until.mock.assert_called_once_with(model, list(model.applications.values()), loop=None, timeout=1800)

    @patch('asyncio.sleep', new=AsyncMock())
    @patch('jujuna.upgrade.get_hacluster_subordinate_pairs')
    @patch('jujuna.upgrade.wait_until', new=AsyncMock())
    @patch('jujuna.upgrade.order_units', new=AsyncMock())
    @patch('jujuna.upgrade.enumerate_actions', new=AsyncMock(return_value=['openstack-upgrade', 'pause', 'resume']))
    def test_perform_upgrade_rolling_ha(
        self, get_hacluster_subordinate_pairs
    ):
        """Testing upgrade parser."""
        from jujuna.upgrade import wait_until
        from jujuna.upgrade import order_units
        from jujuna.upgrade import enumerate_actions

        origin_previous = 'cloud:xenial-newton'
        origin = 'cloud:xenial-ocata'
        upgrade_action = 'openstack-upgrade'
        ORIGIN_CONFIG = [{'openstack-origin': {'value': origin}}, {'openstack-origin': {'value': origin_previous}}]

        def func(*args, **kwargs):
            return ORIGIN_CONFIG.pop()

        unit0 = AsyncClassMock(static=['run_action'], props={'name': 'test/0'})
        unit1 = AsyncClassMock(static=['run_action'], props={'name': 'test/1'})
        unit2 = AsyncClassMock(static=['run_action'], props={'name': 'test/2'})

        unit0.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})
        unit1.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})
        unit2.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})

        unit0_ha = AsyncClassMock(static=['run_action'], props={'name': 'test-hacluster/0'})
        unit1_ha = AsyncClassMock(static=['run_action'], props={'name': 'test-hacluster/1'})
        unit2_ha = AsyncClassMock(static=['run_action'], props={'name': 'test-hacluster/2'})

        unit0_ha.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})
        unit1_ha.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})
        unit2_ha.run_action.mock.return_value = AsyncClassMock(static=['wait', 'status'], props={'results': 'results'})

        units = [unit0, unit1, unit2]
        units_ha = [unit0_ha, unit1_ha, unit2_ha]

        app = AsyncClassMock(
            static=['set_config', 'get_config'],
            props={'name': 'test', 'units': units, 'relations': []}
        )
        apps = {'test': app}
        model = AsyncClassMock(props={'applications': apps, 'loop': None})

        app.get_config.mock.side_effect = func
        order_units.mock.return_value = units
        get_hacluster_subordinate_pairs.return_value = {
            'test/0': unit1_ha, 'test/1': unit2_ha, 'test/2': unit0_ha,
        }

        loop(perform_upgrade(
            model,
            app,
            {},
            upgrade_action,
            {},
            dry_run=False,
            evacuate=False,
            rollable=True,
            pause=True,
            origin=origin
        ))
        app.set_config.mock.assert_called_once_with({'openstack-origin': origin})
        enumerate_actions.mock.assert_called_once_with(app)
        order_units.mock.assert_called_once_with(app.name, app.units)
        get_hacluster_subordinate_pairs.assert_called_once_with(app)

        for unit in units:
            unit.run_action.mock.assert_any_call('pause')
            unit.run_action.mock.assert_any_call(upgrade_action)
            unit.run_action.mock.assert_called_with('resume')

        for unit_ha in units_ha:
            unit_ha.run_action.mock.assert_any_call('pause')
            unit_ha.run_action.mock.assert_called_with('resume')

        wait_until.mock.assert_called_with(model, list(model.applications.values()), loop=None, timeout=1800)
