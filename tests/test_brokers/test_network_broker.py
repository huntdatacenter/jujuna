"""
Tests for brokers.

"""

import unittest
from unittest.mock import patch
from .asyncio_mocks import AsyncClassMock
from .asyncio_mocks import loop
from jujuna.brokers.network import Network


class TestNetworkBroker(unittest.TestCase):
    """Test network broker.

    """

    @patch('jujuna.brokers.network.Network', new=AsyncClassMock('run'))
    @patch('jujuna.exporters.Exporter')
    def test_network_broker(self, exporter):
        """Testing network broker."""
        fb = Network()
        var = loop(
            fb.run({}, 'app-unit/0', 0)
        )
        self.assertEqual(var, [], var)
