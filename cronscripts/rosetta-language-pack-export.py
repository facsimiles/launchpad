#!/usr/bin/python
# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""Script to export a tarball of translations for a distro release."""

__metaclass__ = type

import optparse
import sys

from canonical.lp import initZopeless
from canonical.launchpad.scripts import execute_zcml_for_scripts
from canonical.launchpad.scripts.rosetta import create_logger, \
    calculate_loglevel
from canonical.launchpad.scripts.language_pack import export_language_pack

def parse_options(args):
    """Parse options for exporting distribution release translations.

    Returns a 3-tuple containing an options object, a distribution name and a
    release name.
    """

    parser = optparse.OptionParser(
        usage='%prog [options] distribution release')
    parser.add_option(
        '--email',
        dest='email_addresses',
        default=[],
        action='append',
        help='An email address to send a notification to.'
        )
    parser.add_option(
        '--output',
        dest='output',
        default=None,
        action='store',
        help='A file to send the generated tarball to, rather than the'
             ' Libraran.'
        )
    parser.add_option(
        '-v',
        '--verbose',
        dest='verbose',
        default=0,
        action='count',
        help='Log more information.'
        )
    parser.add_option(
        '-q',
        '--quiet',
        dest='quiet',
        default=0,
        action='count',
        help='Log less information.'
        )
    parser.add_option(
        '--update',
        dest='update',
        default=False,
        action='store_true'
        )

    options, args = parser.parse_args(args)

    if len(args) != 2:
        parser.error('Wrong number of arguments')

    return options, args[0], args[1]

def main(argv):
    initZopeless()
    execute_zcml_for_scripts()

    options, distribution_name, release_name = parse_options(argv[1:])

    loglevel = calculate_loglevel(options.quiet, options.verbose)
    logger = create_logger('rosetta-language-pack-export', loglevel)
    logger.info('Exporting translations for release %s of distribution %s',
        distribution_name, release_name)

    success = export_language_pack(
        distribution_name=distribution_name,
        release_name=release_name,
        update=options.update,
        output_file=options.output,
        email_addresses=options.email_addresses,
        logger=logger)

    if success:
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))

