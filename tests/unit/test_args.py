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
        args = parse_args(['upgrade', '--dry-run'])
        self.assertEqual(args.action, 'upgrade')

        self.assertFalse(args.upgrade_only)
        self.assertFalse(args.charms_only)
        self.assertTrue(args.dry_run)

        self.assertEqual(args.model_name, None)
        self.assertEqual(args.ctrl_name, None)

    def test_args_clean(self):
        """Testing clean parser."""
        args = parse_args(['clean', '--model', 'cloud', '-w'])
        self.assertEqual(args.action, 'clean')

        self.assertFalse(args.dry_run)
        self.assertTrue(args.wait)

        self.assertEqual(args.model_name, 'cloud')
        self.assertEqual(args.ctrl_name, None)
