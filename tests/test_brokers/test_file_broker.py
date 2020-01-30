"""
Tests for brokers.

"""

import unittest
from unittest.mock import patch
from .asyncio_mocks import AsyncClassMock
from .asyncio_mocks import loop
from jujuna.brokers.file import File


class TestFileBroker(unittest.TestCase):
    """Test file broker.

    """

    @patch('jujuna.brokers.file.File', new=AsyncClassMock('run'))
    @patch('jujuna.exporters.Exporter')
    def test_file_broker(self, exporter):
        """Testing file broker."""
        fb = File()
        var = loop(
            fb.run({}, 'app-unit/0', 0)
        )
        self.assertEqual(var, [], var)
