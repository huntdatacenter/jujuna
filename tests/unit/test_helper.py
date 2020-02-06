"""
Tests for helper lib.

"""

from jujuna.helper import cs_name_parse
import unittest


class TestArguments(unittest.TestCase):
    """Test argument parsing.

    """

    def test_simple_name_charm(self):
        """Testing upgrade parser."""
        charm_id = cs_name_parse('glance')

        self.assertNotEqual(charm_id, {})
        self.assertEqual(charm_id['series'], None)
        self.assertEqual(charm_id['charm'], 'glance')
        self.assertEqual(charm_id['revision'], None)
        self.assertEqual(charm_id['charmstore'], True)

    def test_cs_name_charm_null(self):
        """Testing upgrade parser."""
        charm_id = cs_name_parse('cs:bionic/glance-0')

        self.assertNotEqual(charm_id, {})
        self.assertEqual(charm_id['series'], 'bionic')
        self.assertEqual(charm_id['charm'], 'glance')
        self.assertEqual(charm_id['revision'], 0)
        self.assertEqual(charm_id['charmstore'], True)

    def test_cs_name_charm(self):
        """Testing upgrade parser."""
        charm_id = cs_name_parse('cs:bionic/glance-301')

        self.assertNotEqual(charm_id, {})
        self.assertEqual(charm_id['series'], 'bionic')
        self.assertEqual(charm_id['charm'], 'glance')
        self.assertEqual(charm_id['revision'], 301)
        self.assertEqual(charm_id['charmstore'], True)

    def test_local_name_charm(self):
        """Testing upgrade parser."""
        charm_id = cs_name_parse('local:/tmp/glance-build')

        self.assertNotEqual(charm_id, {})
        self.assertEqual(charm_id['series'], None)
        self.assertEqual(charm_id['charm'], '/tmp/glance-build')
        self.assertEqual(charm_id['revision'], None)
        self.assertEqual(charm_id['charmstore'], False)
