# Copyright 2004-2007 Canonical Ltd.  All rights reserved.

__metaclass__ = type

import os

from canonical.launchpad.testing.systemdocs import LayeredDocFileSuite


# The setUp() and tearDown() functions ensure that this doctest is not umask
# dependent.
def setUp(testobj):
    testobj._old_umask = os.umask(022)


def tearDown(testobj):
    os.umask(testobj._old_umask)


def test_suite():
    return LayeredDocFileSuite(
        "filesystem.txt",
        setUp=setUp, tearDown=tearDown, stdout_logging=False)
