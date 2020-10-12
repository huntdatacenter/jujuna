"""
Tests for brokers.

"""

import unittest
from unittest.mock import patch
from .asyncio_mocks import AsyncClassMock
from .asyncio_mocks import loop
from jujuna.brokers.mount import Mount


class TestMountBroker(unittest.TestCase):
    """Test mount broker.

    """

    @patch('jujuna.brokers.mount.Mount', new=AsyncClassMock('run'))
    @patch('jujuna.exporters.Exporter')
    def test_mount_broker(self, exporter):
        """Testing file broker."""
        fb = Mount()
        var = loop(
            fb.run({}, 'app-unit/0', 0)
        )
        self.assertEqual(var, [], var)
