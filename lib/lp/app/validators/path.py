# Copyright 2019 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Validators for paths and path functions."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'path_within_repo'
]

import os

from lp.app.validators import LaunchpadValidationError


def path_within_repo(path):
    # We're not working with complete paths, so we need to make them so
    fake_base_path = '/repo'
    # Ensure that we start with a common base
    target_path = os.path.join(fake_base_path, path)
    # Resolve symlinks and such
    real_path = os.path.realpath(target_path)
    # If the paths don't have a common start anymore,
    # we are attempting an escape
    if not os.path.commonprefix((real_path, fake_base_path)) == fake_base_path:
        raise LaunchpadValidationError("Path would escape build directory")
    return True
