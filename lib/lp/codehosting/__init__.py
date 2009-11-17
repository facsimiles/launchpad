# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Launchpad code-hosting system.

NOTE: Importing this package will load any system Bazaar plugins, as well as
all plugins in the bzrplugins/ directory underneath the rocketfuel checkout.
"""

__metaclass__ = type
__all__ = [
    'get_bzr_path',
    'get_bzr_plugins_path',
    'iter_list_chunks',
    'load_optional_plugin',
    ]


import os

import bzrlib
from bzrlib import hooks
from bzrlib.plugin import load_plugins

from canonical.config import config


def iter_list_chunks(a_list, size):
    """Iterate over `a_list` in chunks of size `size`.

    I'm amazed this isn't in itertools (mwhudson).
    """
    for i in range(0, len(a_list), size):
        yield a_list[i:i+size]


def get_bzr_path():
    """Find the path to the copy of Bazaar for this rocketfuel instance"""
    bzr_in_egg_path = os.path.join(
        os.path.dirname(os.path.dirname(bzrlib.__file__)),
        'EGG-INFO/scripts/bzr')
    if os.path.exists(bzr_in_egg_path):
        return bzr_in_egg_path
    else:
        return os.path.join(
            os.path.dirname(os.path.dirname(bzrlib.__file__)),
            'bzr')


def get_bzr_plugins_path():
    """Find the path to the Bazaar plugins for this rocketfuel instance"""
    return os.path.join(config.root, 'bzrplugins')


os.environ['BZR_PLUGIN_PATH'] = get_bzr_plugins_path()

# We want to have full access to Launchpad's Bazaar plugins throughout the
# codehosting package.
load_plugins([get_bzr_plugins_path()])


def load_optional_plugin(plugin_name):
    """Load the plugin named `plugin_name` from optionalbzrplugins/."""
    from bzrlib import plugins

    if plugin_name == 'svn':
        # This is utterly, utterly gross.  Yes.
        class FuncTools:
            @staticmethod
            def partial(*args, **kw):
                return None
        import sys
        sys.modules['functools'] = FuncTools
        from dulwich.misc import defaultdict
        import collections
        collections.defaultdict = defaultdict

    optional_plugin_dir = os.path.join(config.root, 'optionalbzrplugins')
    if optional_plugin_dir not in plugins.__path__:
        plugins.__path__.append(optional_plugin_dir)
    __import__("bzrlib.plugins.%s" % plugin_name)


def remove_hook(self, hook):
    """Remove the hook from the HookPoint"""
    self._callbacks.remove(hook)
    for name, value in self._callback_names.iteritems():
        if value is hook:
            del self._callback_names[name]


# Monkeypatch: Branch.hooks is a list in bzr 1.13, so it supports remove.
# It is a HookPoint in bzr 1.14, so add HookPoint.remove.
hooks.HookPoint.remove = remove_hook
