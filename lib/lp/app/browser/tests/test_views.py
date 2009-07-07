# Copyright 2009 Canonical Ltd.  All rights reserved.
"""
Run the view tests.
"""

import logging
import os
import unittest

from canonical.launchpad.testing.systemdocs import (
    LayeredDocFileSuite, setUp, tearDown)
from canonical.testing import DatabaseFunctionalLayer


here = os.path.dirname(os.path.realpath(__file__))

# The default layer of view tests is the DatabaseFunctionalLayer. Tests
# that require something special like the librarian or mailman must run
# on a layer that sets those services up.
special_test_layer = {}


def test_suite():
    suite = unittest.TestSuite()
    testsdir = os.path.abspath(here)

    # Add tests using default setup/teardown
    filenames = [filename
                 for filename in os.listdir(testsdir)
                 if filename.endswith('.txt')]
    # Sort the list to give a predictable order.
    filenames.sort()
    for filename in filenames:
        path = filename
        if path in special_test_layer:
            layer = special_test_layer[path]
        else:
            layer = DatabaseFunctionalLayer
        one_test = LayeredDocFileSuite(
            path, setUp=setUp, tearDown=tearDown, layer=layer,
            stdout_logging_level=logging.WARNING
            )
        suite.addTest(one_test)

    return suite
