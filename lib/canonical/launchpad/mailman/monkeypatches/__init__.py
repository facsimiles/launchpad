# Copyright 2007 Canonical Ltd.  All rights reserved.

import os

HERE = os.path.dirname(__file__)


def monkey_patch(mailman_path, config):
    """Monkey-patch an installed Mailman 2.1 tree.

    Rather than maintain a forked tree of Mailman 2.1, we apply a set of
    changes to an installed Mailman tree.  This tree can be found rooted at
    mailman_path.

    This should usually mean just copying a file from this directory into
    mailman_path.  Rather than build a lot of process into the mix, just hard
    code each transformation here.
    """
    # Hook Mailman to Launchpad by writing a custom mm_cfg.py file which adds
    # the top of our Launchpad tree to Mailman's sys.path.  The mm_cfg.py file
    # won't do much more than set up sys.path and do an from-import-* to get
    # everything that doesn't need to be dynamically calculated at run-time.
    # Things that can only be calculated at run-time are written to mm_cfg.py
    # now.  It's okay to simply overwrite any existing mm_cfg.py, since we'll
    # provide everything Mailman needs.
    #
    # Remember, don't rely on Launchpad's config object in the mm_cfg.py file
    # or in the canonical.mailman.monkeypatches.defaults module because
    # Mailman will not be able to initialize Launchpad's configuration system.
    # Instead, anything that's needed from config should be written to the
    # mm_cfg.py file now.
    #
    # Calculate the parent directory of the canonical package.  This directory
    # will get appended to Mailman's sys.path.
    import canonical
    launchpad_top = os.path.dirname(os.path.dirname(canonical.__file__))
    # Read the email footer template for all Launchpad messages.
    from canonical.launchpad.helpers import get_email_template
    footer = get_email_template('mailinglist-footer.txt')
    # Write the mm_cfg.py file, filling in the dynamic values now.
    host, port = config.mailman.smtp
    owner_address, owner_password = config.mailman.build.site_list_owner
    config_path = os.path.join(mailman_path, 'Mailman', 'mm_cfg.py')
    config_file = open(config_path, 'w')
    try:
        print >> config_file, """\
# Automatically generated by runlaunchpad.py

# Set up Mailman's sys.path to pick up the top of Launchpad's tree
import sys
sys.path.insert(0, '%(launchpad_top)s')

# Pick up Launchpad static overrides.  This will also pick up the standard
# Mailman.Defaults.* variables.
from canonical.launchpad.mailman.monkeypatches.defaults import *

# Our dynamic overrides of all the static defaults.
SMTPHOST = '%(smtp_host)s'
SMTPPORT = %(smtp_port)d

# The endpoint for Launchpad XMLRPC calls.
XMLRPC_URL = '%(xmlrpc_url)s'
XMLRPC_SLEEPTIME = %(xmlrpc_sleeptime)s

# RFC 2369 header information
LIST_HELP_HEADER = '%(list_help_header)s'
LIST_SUBSCRIPTION_HEADERS = '%(list_subscription_headers)s'
LIST_ARCHIVE_HEADER_TEMPLATE = '%(archive_url_template)s'
LIST_OWNER_HEADER_TEMPLATE = '%(list_owner_header_template)s'

SITE_LIST_OWNER = '%(site_list_owner)s'

# Modify the global pipeline to add some handlers for Launchpad specific
# functionality.
# - ensure posters are Launchpad members.
GLOBAL_PIPELINE.insert(0, 'LaunchpadMember')
# - insert our own RFC 2369 and RFC 5064 headers; this must appear after
#   CookHeaders
index = GLOBAL_PIPELINE.index('CookHeaders')
GLOBAL_PIPELINE.insert(index + 1, 'LaunchpadHeaders')

DEFAULT_MSG_FOOTER = '''_______________________________________________
%(footer)s'''
""" % dict(
    launchpad_top=launchpad_top,
    smtp_host=host,
    smtp_port=port,
    xmlrpc_url=config.mailman.xmlrpc_url,
    xmlrpc_sleeptime=config.mailman.xmlrpc_runner_sleep,
    site_list_owner=owner_address,
    list_help_header=config.mailman.list_help_header,
    list_subscription_headers=config.mailman.list_subscription_headers,
    archive_url_template=config.mailman.archive_url_template,
    list_owner_header_template=config.mailman.list_owner_header_template,
    footer=footer,
    )
    finally:
        config_file.close()
    # Mailman's qrunner system requires runner modules to live in the
    # Mailman.Queue package.  Set things up so that there's a hook module in
    # there for the XMLRPCRunner.
    runner_path = os.path.join(mailman_path,
                               'Mailman', 'Queue', 'XMLRPCRunner.py')
    runner_file = open(runner_path, 'w')
    try:
        print >> runner_file, (
            'from canonical.launchpad.mailman.monkeypatches.xmlrpcrunner '
            'import *')
    finally:
        runner_file.close()
    # Mailman needs an additional handler at the front of the global pipeline
    # to determine whether the poster is a Launchpad member or not.
    handler_path = os.path.join(
        mailman_path, 'Mailman', 'Handlers', 'LaunchpadMember.py')
    handler_file = open(handler_path, 'w')
    try:
        print >> handler_file, (
            'from canonical.launchpad.mailman.monkeypatches.lphandler '
            'import *')
    finally:
        handler_file.close()
    # We also need a handler to insert RFC 2369 and RFC 5064 headers specific
    # to Launchpad's mailing list architecture.
    handler_path = os.path.join(
        mailman_path, 'Mailman', 'Handlers', 'LaunchpadHeaders.py')
    handler_file = open(handler_path, 'w')
    try:
        print >> handler_file, (
            'from canonical.launchpad.mailman.monkeypatches.lpheaders '
            'import *')
    finally:
        handler_file.close()
