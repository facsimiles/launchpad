# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Glues the codehosting SSH daemon together."""

__metaclass__ = type
__all__ = [
    'ACCESS_LOG_NAME',
    'CodehostingAvatar',
    'get_key_path',
    'get_portal',
    'LOG_NAME',
    'make_portal',
    'PRIVATE_KEY_FILE',
    'PUBLIC_KEY_FILE',
    ]

import os

from twisted.conch.interfaces import ISession
from twisted.conch.ssh import filetransfer
from twisted.cred.portal import IRealm, Portal
from twisted.python import components
from twisted.web.xmlrpc import Proxy

from zope.interface import implements

from canonical.config import config
from lp.codehosting import sftp
from lp.codehosting.sshserver.auth import (
    LaunchpadAvatar, PublicKeyFromLaunchpadChecker)
from lp.codehosting.sshserver.session import launch_smart_server


# The names of the key files of the server itself. The directory itself is
# given in config.codehosting.host_key_pair_path.
PRIVATE_KEY_FILE = 'ssh_host_key_rsa'
PUBLIC_KEY_FILE = 'ssh_host_key_rsa.pub'

OOPS_CONFIG_SECTION = 'codehosting'
LOG_NAME = 'codehosting'
ACCESS_LOG_NAME = 'codehosting.access'


class CodehostingAvatar(LaunchpadAvatar):
    """An SSH avatar specific to codehosting.

    :ivar branchfs_proxy: A Twisted XML-RPC client for the authserver. The
        server must implement `IBranchFileSystem`.
    """

    def __init__(self, user_dict, branchfs_proxy):
        LaunchpadAvatar.__init__(self, user_dict)
        self.branchfs_proxy = branchfs_proxy


components.registerAdapter(launch_smart_server, CodehostingAvatar, ISession)

components.registerAdapter(
    sftp.avatar_to_sftp_server, CodehostingAvatar, filetransfer.ISFTPServer)


class Realm:
    implements(IRealm)

    def __init__(self, authentication_proxy, branchfs_proxy):
        self.authentication_proxy = authentication_proxy
        self.branchfs_proxy = branchfs_proxy

    def requestAvatar(self, avatar_id, mind, *interfaces):
        # Fetch the user's details from the authserver
        deferred = mind.lookupUserDetails(
            self.authentication_proxy, avatar_id)

        # Once all those details are retrieved, we can construct the avatar.
        def got_user_dict(user_dict):
            avatar = CodehostingAvatar(user_dict, self.branchfs_proxy)
            return interfaces[0], avatar, avatar.logout

        return deferred.addCallback(got_user_dict)


def get_portal(authentication_proxy, branchfs_proxy):
    """Get a portal for connecting to Launchpad codehosting."""
    portal = Portal(Realm(authentication_proxy, branchfs_proxy))
    portal.registerChecker(
        PublicKeyFromLaunchpadChecker(authentication_proxy))
    return portal


def get_key_path(key_filename):
    key_directory = config.codehosting.host_key_pair_path
    return os.path.join(config.root, key_directory, key_filename)


def make_portal():
    """Create and return a `Portal` for the SSH service.

    This portal accepts SSH credentials and returns our customized SSH
    avatars (see `lp.codehosting.sshserver.auth.CodehostingAvatar`).
    """
    authentication_proxy = Proxy(
        config.codehosting.authentication_endpoint)
    branchfs_proxy = Proxy(config.codehosting.branchfs_endpoint)
    return get_portal(authentication_proxy, branchfs_proxy)
