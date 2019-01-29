#!/usr/bin/python3

import sys
import logging
import argparse
import argcomplete
import async_timeout

from juju import loop

from jujuna.deploy import deploy  # noqa
from jujuna.upgrade import upgrade  # noqa
from jujuna.tests import test  # noqa
from jujuna.clean import clean  # noqa


logger = logging.getLogger('jujuna')
logger.setLevel(logging.DEBUG)

# Double logging cleanup
while logger.handlers:
    logger.handlers.pop()

logHandler = logging.StreamHandler(sys.stdout)
logHandler.setLevel(logging.DEBUG)
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler.setFormatter(logFormatter)
logger.addHandler(logHandler)


def get_parser():
    parser = argparse.ArgumentParser(
        # formatter_class=utils.ParagraphDescriptionFormatter,
        description="Deploy a local bundle, execute upgrade procedure, "
                    "run the deployment through a suite of tests to ensure "
                    "that it can handle the types of operations and failures "
                    "that are common for all deployments.",
    )

    subparsers = parser.add_subparsers(dest='action', help='Action to be executed')
    subparsers.required = True

    p_deploy = subparsers.add_parser('deploy', help="Deploy a local bundle to the current or selected model")
    p_deploy.add_argument('bundle_file', type=argparse.FileType('r'),
                          help="Path to bundle file (i.e. bundle.yaml)")
    p_deploy.add_argument("-c", "--controller", default=None, dest="ctrl_name", help="Controller (def: current)")
    p_deploy.add_argument("-m", "--model", default=None, dest="model_name", help="Model to use instead of current")
    p_deploy.add_argument("-w", "--wait", action='store_true', help="Wait for deploy to finish")
    p_deploy.add_argument("-t", "--timeout", default=0, type=int, help="Timeout after N seconds.")
    p_deploy.add_argument("--endpoint", default=None, dest="endpoint",
                          help="Juju endpoint (requires model uuid instead of name)")
    p_deploy.add_argument("--username", default=None, dest="username", help="Juju username")
    p_deploy.add_argument("--password", default=None, dest="password", help="Juju password")

    p_upgrade = subparsers.add_parser('upgrade', help="Upgrade applications deployed in the current or selected model")
    p_upgrade.add_argument("-c", "--controller", default=None, dest="ctrl_name", help="Controller (def: current)")
    p_upgrade.add_argument("-m", "--model", default=None, dest="model_name", help="Model to use instead of current")
    p_upgrade.add_argument("-o", "--origin", default='cloud:xenial-ocata', dest="origin",
                           help="""Openstack origin:
                                   cloud:xenial-newton,
                                   cloud:xenial-ocata (default),
                                   cloud:xenial-pike,
                                   cloud:xenial-queens,
                                   cloud:bionic-rocky
                                """)
    p_upgrade.add_argument("-a", "--apps", nargs='*', default=[], help="Apps to be upgraded (ordered)")
    p_upgrade.add_argument("-i", "--ignore-errors", action='store_true', dest='ignore_errors',
                           help="Ignore errors during charms upgrade and continue with upgrade procedure")
    p_upgrade.add_argument("-p", "--pause", action='store_true', help="Pause unit before upgrade (incl. HA)")
    p_upgrade.add_argument("-e", "--evacuate", action='store_true', help="Evacuate nova-compute nodes during upgrade")
    p_upgrade.add_argument("--upgrade-only", action='store_true', dest="upgrade_only",
                           help="Upgrade using upgrade hooks without changing the revision")
    p_upgrade.add_argument("--charms-only", action='store_true',
                           help="Upgrade only charms without running upgrade hooks")
    p_upgrade.add_argument("--dry-run", action='store_true', dest="dry_run",
                           help="Dry run - only show changes without upgrading")
    p_upgrade.add_argument("-t", "--timeout", default=0, type=int, help="Timeout after N seconds.")
    p_upgrade.add_argument("-s", "--settings", type=argparse.FileType('r'),
                           help="Path to settings file that overrides default settings (i.e. settings.yaml)")
    p_upgrade.add_argument("--endpoint", default=None, dest="endpoint",
                           help="Juju endpoint (requires model uuid instead of name)")
    p_upgrade.add_argument("--username", default=None, dest="username", help="Juju username")
    p_upgrade.add_argument("--password", default=None, dest="password", help="Juju password")

    p_test = subparsers.add_parser('test', help="Test applications in the current or selected model")
    p_test.add_argument("test_suite", type=argparse.FileType('r'),
                        help="Path to test suite (i.e. ceph/suite.yaml)")
    p_test.add_argument("-c", "--controller", default=None, dest="ctrl_name", help="Controller (def: current)")
    p_test.add_argument("-m", "--model", default=None, dest="model_name", help="Model to use instead of current")
    p_test.add_argument("-t", "--timeout", default=0, type=int, help="Timeout after N seconds.")
    p_test.add_argument("--endpoint", default=None, dest="endpoint",
                        help="Juju endpoint (requires model uuid instead of name)")
    p_test.add_argument("--username", default=None, dest="username", help="Juju username")
    p_test.add_argument("--password", default=None, dest="password", help="Juju password")

    p_clean = subparsers.add_parser(
        'clean',
        help="Clean the model by removing all applications present in the current or selected model"
    )
    p_clean.add_argument("-c", "--controller", default=None, dest="ctrl_name", help="Controller (def: current)")
    p_clean.add_argument("-m", "--model", default=None, dest="model_name", help="Model to use instead of current")
    p_clean.add_argument("-w", "--wait", action='store_true', help="Wait for deploy to finish")
    p_clean.add_argument("-f", "--force", action='store_true', help="Force cleanup (remove all machines in the model).")
    p_clean.add_argument("-i", "--ignore", nargs='*', default=[], help="Apps to be ignored during removal")
    p_clean.add_argument("--dry-run", action='store_true', dest="dry_run",
                         help="Dry run - only show changes without removing applications")
    p_clean.add_argument("-t", "--timeout", default=0, type=int, help="Timeout after N seconds.")
    p_clean.add_argument("--endpoint", default=None, dest="endpoint",
                         help="Juju endpoint (requires model uuid instead of name)")
    p_clean.add_argument("--username", default=None, dest="username", help="Juju username")
    p_clean.add_argument("--password", default=None, dest="password", help="Juju password")

    argcomplete.autocomplete(parser)
    # options = add_bundle_opts(options, parser)

    # if not utils.valid_bundle_or_spell(options.path):
    #     parser.error('Invalid bundle directory: %s' % options.path)

    # configLogging(options)
    return parser


doc_arg_parser = get_parser()  # To be included in documentation


async def run_action(action, timeout, args):
    """Run request action.

    """
    selected_action = globals()[action]

    # Remove used vars
    del vars(args)['action']
    if 'timeout' in vars(args):
        del vars(args)['timeout']

    if timeout:
        at = None
        try:
            async with async_timeout.timeout(timeout) as at:
                return await selected_action(**vars(args))
        except Exception:
            # Exit with timeout code if expired
            if at and at.expired:
                logger.warn('Operation timed out!')
                return 124
            else:
                raise
    else:
        return await selected_action(**vars(args))


def action(args):
    try:
        if hasattr(args, 'action'):
            return loop.run(run_action(args.action, args.timeout, args))
    except Exception as e:
        logger.warn(e)
        return 1

    return 255


def parse_args(args):
    parser = get_parser()
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])

    ret = action(args)

    sys.exit(ret)


if __name__ == '__main__':
    main()
