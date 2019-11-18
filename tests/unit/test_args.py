"""
Tests for argparse configuration.

"""

from jujuna.__main__ import parse_args
import unittest


class TestArguments(unittest.TestCase):
    """Test argument parsing.

    """

    def test_args_upgrade(self):
        """Testing upgrade parser."""
        action, timeout, args = parse_args(['upgrade', '--dry-run'])
        self.assertEqual(action, 'upgrade')
        self.assertEqual(timeout, 0)

        self.assertFalse(args['upgrade_only'])
        self.assertFalse(args['charms_only'])
        self.assertTrue(args['dry_run'])

        self.assertEqual(args['model_name'], None)
        self.assertEqual(args['ctrl_name'], None)

    def test_args_clean(self):
        """Testing clean parser."""
        action, timeout, args = parse_args(['clean', '--model', 'cloud', '-w'])
        self.assertEqual(action, 'clean')
        self.assertEqual(timeout, 0)

        self.assertFalse(args['dry_run'])
        self.assertTrue(args['wait'])

        self.assertEqual(args['model_name'], 'cloud')
        self.assertEqual(args['ctrl_name'], None)

    def test_kv_parse(self):
        """Testing clean parser."""
        action, timeout, args = parse_args(
            ['upgrade', '-t', '5', '--upgrade-params', 'version=luminuous', '--origin-keys', 'ceph=source']
        )
        self.assertEqual(action, 'upgrade')
        self.assertEqual(timeout, 5)

        self.assertEqual(args['upgrade_params'], {'version': 'luminuous'})
        self.assertEqual(args['origin_keys'], {'ceph': 'source'})
