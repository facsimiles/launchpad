# Copyright 2004 Canonical Ltd.  All rights reserved.

import unittest
from zope.testing.doctestunit import DocTestSuite
import canonical.pidfile

def test_suite():
    suite = DocTestSuite(canonical.pidfile)
    return suite

if __name__ == "__main__":
    DEFAULT = test_suite()
    unittest.main(defaultTest='DEFAULT')

