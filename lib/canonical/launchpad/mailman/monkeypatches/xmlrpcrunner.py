# Copyright 2007 Canonical Ltd.  All rights reserved.

"""XMLRPC runner for querying Launchpad."""

__all__ = [
    'XMLRPCRunner',
    ]

import os
import sys
import shutil
import tarfile
import traceback
import xmlrpclib

from cStringIO import StringIO

from Mailman import mm_cfg
from Mailman.Logging.Syslog import syslog
from Mailman.MailList import MailList
from Mailman.Queue.Runner import Runner

COMMASPACE = ', '


# Mapping from modifiable attributes as they are named by the xmlrpc
# interface, to the attribute names on the MailList instances.
attrmap = {
    'welcome_message'   : 'welcome_msg',
    }


def logexc():
    out_file = StringIO()
    traceback.print_exc(file=out_file)
    syslog('xmlrpc', out_file.getvalue())


class XMLRPCRunner(Runner):
    def __init__(self, slice=None, numslices=1):
        self.SLEEPTIME = mm_cfg.XMLRPC_SLEEPTIME
        # Instead of calling the superclass's __init__() method, just
        # initialize the two attributes that are actually used.  The reason
        # for this is that the XMLRPCRunner doesn't have a queue so it
        # shouldn't be trying to create a Switchboard instance.  Still, it
        # needs a dummy _kids and _stop attributes for the rest of the runner
        # to work.  We're using runners in a more general sense than Mailman 2
        # is designed for.
        self._kids = {}
        self._stop = False

    def _oneloop(self):
        # See if Launchpad has anything for us to do.
        proxy = xmlrpclib.ServerProxy(mm_cfg.XMLRPC_URL)
        try:
            actions = proxy.getPendingActions()
        except xmlrpclib.ProtocolError, e:
            syslog('xmlrpc', 'Cannot talk to Launchpad:\n%s', e)
            return 0
        if actions:
            syslog('xmlrpc', 'Got some things to do: %s',
                   COMMASPACE.join(actions.keys()))
        else:
            # Always return 0 so self._snooze() will sleep for a while.
            syslog('xmlrpc', 'Nothing to do')
            return 0
        # There are three actions that can currently be taken.  A create
        # action creates a mailing list, possibly with some defaults, a modify
        # changes the settings on some existing mailing list, and a deactivate
        # means that the list should be deactivated.  This latter doesn't have
        # a directly corresponding semantic at the Mailman layer -- if a
        # mailing list exists, it's activated.  We'll take it to mean that the
        # list should be deleted, but its archives should remain.
        statuses = {}
        if 'create' in actions:
            self._create(actions['create'], statuses)
            del actions['create']
        if 'modify' in actions:
            self._modify(actions['modify'], statuses)
            del actions['modify']
        if 'deactivate' in actions:
            self._deactivate(actions['deactivate'], statuses)
            del actions['deactivate']
        # Any other keys should be ignored because they specify actions that
        # we know nothing about.  We'll log them to Mailman's log files
        # though.
        if actions:
            syslog('xmlrpc', 'Invalid xmlrpc action keys: %s',
                   COMMASPACE.join(actions.keys()))
        # Report the statuses to Launchpad.
        proxy.reportStatus(statuses)
        # Snooze for a while.
        return 0

    def _create(self, actions, statuses):
        for team_name, initializer in actions:
            # This is a set of attributes defining the defaults for lists
            # created under Launchpad's control.  XXX Figure out other
            # defaults and where to keep them -- in Launchpad's configuration
            # files?  Probably not.
            list_defaults = {}
            # Verify that the initializer variables are what we expect.
            for key in attrmap:
                if key in initializer:
                    list_defaults[attrmap[key]] = initializer[key]
                    del initializer[key]
            if initializer:
                # Reject this list creation request.
                statuses[team_name] = 'failure'
                syslog('xmlrpc', 'Unexpected create settings: %s',
                       COMMASPACE.join(initializer.keys()))
                continue
            # Create the mailing list and set the defaults.
            mlist = MailList()
            try:
                # Use a fake list admin password; Mailman will never be
                # administered from its web u/i.  Nor will the mailing list
                # require an owner that's different from the site owner.  Also
                # by default, only English is supported.
                try:
                    mlist.Create(team_name,
                                 mm_cfg.SITE_LIST_OWNER,
                                 ' no password ')
                # We have to use a bare except here because of the legacy
                # string exceptions that Mailman can raise.
                except:
                    syslog('xmlrpc',
                           'List creation error for team: %s', team_name)
                    logexc()
                    statuses[team_name] = 'failure'
                else:
                    # Apply defaults.
                    for key, value in list_defaults.items():
                        setattr(mlist, key, value)
                    # Do MTA specific creation steps.
                    if mm_cfg.MTA:
                        modname = 'Mailman.MTA.' + mm_cfg.MTA
                        __import__(modname)
                        sys.modules[modname].create(mlist, quiet=True)
                    statuses[team_name] = 'success'
                    syslog('xmlrpc', 'Successfully created list: %s',
                           team_name)
                    mlist.Save()
            finally:
                mlist.Unlock()

    def _modify(self, actions, statuses):
        for team_name, modifications in actions:
            # First, validate the modification keywords.
            list_settings = {}
            for key in attrmap:
                if key in modifications:
                    list_settings[attrmap[key]] = modifications[key]
                    del modifications[key]
            if modifications:
                statuses[team_name] = 'failure'
                syslog('xmlrpc', 'Unexpected modify settings: %s',
                       COMMASPACE.join(initializer.keys()))
                continue
            try:
                try:
                    mlist = MailList(team_name)
                    for key, value in list_settings.items():
                        setattr(mlist, key, value)
                    mlist.Save()
                finally:
                    mlist.Unlock()
            # We have to use a bare except here because of the legacy string
            # exceptions that Mailman can raise.
            except:
                syslog('xmlrpc',
                       'List modification error for team: %s', team_name)
                logexc()
                statuses[team_name] = 'failure'
            else:
                syslog('xmlrpc', 'Successfully modified list: %s',
                       team_name)
                statuses[team_name] = 'success'

    def _deactivate(self, actions, statuses):
        for team_name in actions:
            try:
                mlist = MailList(team_name, lock=False)
                if mm_cfg.MTA:
                    modname = 'Mailman.MTA.' + mm_cfg.MTA
                    __import__(modname)
                    sys.modules[modname].remove(mlist, quiet=True)
                # We're keeping the archives, so all we need to do is delete
                # the 'lists/team_name' directory.  However, to be extra
                # specially paranoid, create a gzip'd tarball of the directory
                # for safe keeping, just in case we screwed up.
                list_dir = os.path.join(mm_cfg.VAR_PREFIX, 'lists', team_name)
                # XXX BarryWarsaw 02-Aug-2007 Should we watch out for
                # collisions on the tar file name?  This can only happen if
                # the team is resurrected but the old archived tarball backup
                # wasn't removed.
                tgz_file_name = os.path.join(
                    mm_cfg.VAR_PREFIX, 'backups', team_name + '.tgz')
                tgz_file = tarfile.open(tgz_file_name, 'w:gz')
                try:
                    # .add() works recursively by default.
                    tgz_file.add(list_dir)
                finally:
                    tgz_file.close()
                # Now delete the list's directory.
                shutil.rmtree(list_dir)
            # We have to use a bare except here because of the legacy string
            # exceptions that Mailman can raise.
            except:
                syslog('xmlrpc', 'List deletion error for team: %s', team_name)
                logexc()
                statuses[team_name] = 'failure'
            else:
                syslog('xmlrpc', 'Successfully deleted list: %s', team_name)
                statuses[team_name] = 'success'
