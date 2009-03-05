# Copyright 2004-2007 Canonical Ltd.  All rights reserved.

"""Launchpad code-hosting system.

NOTE: Importing this package will load any system Bazaar plugins, as well as
all plugins in the bzrplugins/ directory underneath the rocketfuel checkout.
"""

__metaclass__ = type
__all__ = [
    'get_bzr_path',
    'get_bzr_plugins_path',
    'load_optional_plugin',
    ]


import os
from bzrlib.plugin import load_plugins

from canonical.config import config


def get_bzr_path():
    """Find the path to the copy of Bazaar for this rocketfuel instance"""
    return os.path.join(config.root, 'sourcecode', 'bzr', 'bzr')


def get_bzr_plugins_path():
    """Find the path to the Bazaar plugins for this rocketfuel instance"""
    return os.path.join(config.root, 'bzrplugins')


os.environ['BZR_PLUGIN_PATH'] = get_bzr_plugins_path()

# We want to have full access to Launchpad's Bazaar plugins throughout the
# codehosting package.
load_plugins([get_bzr_plugins_path()])

def load_optional_plugin(plugin_name):
    from bzrlib import plugins
    optional_plugin_dir = os.path.join(config.root, 'optionalbzrplugins')
    if optional_plugin_dir not in plugins.__path__:
        plugins.__path__.append(optional_plugin_dir)
    __import__("bzrlib.plugins.%s" % plugin_name)
