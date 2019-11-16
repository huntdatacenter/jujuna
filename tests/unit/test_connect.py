"""
Tests for upgrade action.

"""

from unittest.mock import patch
from unittest import TestCase
from .asyncio_mocks import AsyncClassMock
from .asyncio_mocks import loop
from jujuna.helper import connect_juju


class TestConnect(TestCase):
    """Test connection helper.

    """

    @patch('jujuna.helper.Controller', new=AsyncClassMock('connect'))
    @patch('jujuna.helper.Model', new=AsyncClassMock('connect'))
    def test_remote_connection(self):
        """Testing remote connection."""
        from jujuna.helper import Controller
        from jujuna.helper import Model

        ctrl_name = 'test_controller'
        uuid = '11188111-1111-2222-a0bf-a00777888999'
        endpoint = '127.0.0.1:17070'
        username = 'user'
        password = 'badpassword'
        cacert = 'PKcert'
        loop(connect_juju(
            ctrl_name,
            uuid,
            endpoint=endpoint,
            username=username,
            password=password,
            cacert=cacert
        ))
        Controller.connect.mock.assert_called_once_with(
            endpoint=endpoint,
            username=username,
            password=password,
            cacert=cacert
        )
        Model.connect.mock.assert_called_once_with(
            uuid=uuid,
            endpoint=endpoint,
            username=username,
            password=password,
            cacert=cacert
        )

    @patch('jujuna.helper.Controller', new=AsyncClassMock('connect', 'get_model'))
    def test_local_connection(self):
        """Testing local connection."""
        from jujuna.helper import Controller

        ctrl_name = 'test_controller'
        uuid = '11188111-1111-2222-a0bf-a00777888999'
        loop(connect_juju(
            ctrl_name,
            uuid
        ))

        Controller.connect.mock.assert_called_once_with(ctrl_name)
        Controller.get_model.mock.assert_called_once_with(uuid)

    @patch('jujuna.helper.Controller', new=AsyncClassMock('connect'))
    @patch('jujuna.helper.Model', new=AsyncClassMock('connect'))
    def test_local_connection_model(self):
        """Testing local connection."""
        from jujuna.helper import Controller
        from jujuna.helper import Model

        ctrl_name = 'test_controller'
        loop(connect_juju(
            ctrl_name
        ))

        Controller.connect.mock.assert_called_once_with(ctrl_name)
        Model.connect.mock.assert_called_once()
