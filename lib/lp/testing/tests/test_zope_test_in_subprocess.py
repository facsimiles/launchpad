# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test `lp.testing.ZopeTestInSubProcess`."""

__metaclass__ = type

import functools
import os
import unittest

from lp.testing import ZopeTestInSubProcess


def record_pid(method):
    """Decorator that records the pid at method invocation.

    Will probably only DTRT with class methods or bound instance
    methods.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        setattr(self, 'pid_in_%s' % method.__name__, os.getpid())
        return method(self, *args, **kwargs)
    return wrapper


class TestZopeTestInSubProcessLayer:
    """Helper to test `ZopeTestInSubProcess`.

    Asserts that layers are set up and torn down in the expected way,
    namely that setUp() and tearDown() are called in the parent
    process, and testSetUp() and testTearDown() are called in the
    child process.

    The assertions for tearDown() and testTearDown() must be done here
    because the test case runs before these methods are called. In the
    interests of symmetry and clarity, the assertions for setUp() and
    testSetUp() are done here too.
    """

    @record_pid
    def __init__(self, test):
        self.test = test
        # These are needed to satisfy the requirements of the
        # byzantine Zope layer machinery.
        self.__name__ = self.__class__.__name__
        self.__bases__ = self.__class__.__bases__

    @record_pid
    def setUp(self):
        # Runs in the parent process.
        assert self.pid_in___init__ == self.pid_in_setUp, (
            "layer.setUp() not called in parent process.")

    @record_pid
    def tearDown(self):
        # Runs in the parent process.
        assert self.pid_in___init__ == self.pid_in_tearDown, (
            "layer.tearDown() not called in parent process.")

    @record_pid
    def testSetUp(self):
        # Runs in the child process.
        assert self.pid_in___init__ != self.pid_in_testSetUp, (
            "layer.testSetUp() called in parent process.")

    @record_pid
    def testTearDown(self):
        # Runs in the child process.
        assert self.pid_in_testSetUp == self.pid_in_testTearDown, (
            "layer.testTearDown() not called in same process as testSetUp().")


class TestZopeTestInSubProcess(ZopeTestInSubProcess, unittest.TestCase):
    """Test `ZopeTestInSubProcess`.

    Assert that setUp(), test() and tearDown() are called in the child
    process.
    """

    @record_pid
    def __init__(self, method_name='runTest'):
        # Runs in the parent process.
        super(TestZopeTestInSubProcess, self).__init__(method_name)
        self.layer = TestZopeTestInSubProcessLayer(self)

    @record_pid
    def setUp(self):
        # Runs in the child process.
        super(TestZopeTestInSubProcess, self).setUp()
        self.failUnlessEqual(
            self.layer.pid_in_testSetUp, self.pid_in_setUp,
            "setUp() not called in same process as layer.testSetUp().")

    @record_pid
    def test(self):
        # Runs in the child process.
        self.failUnlessEqual(
            self.pid_in_setUp, self.pid_in_test,
            "test method not run in same process as setUp().")

    @record_pid
    def tearDown(self):
        # Runs in the child process.
        super(TestZopeTestInSubProcess, self).tearDown()
        self.failUnlessEqual(
            self.pid_in_setUp, self.pid_in_tearDown,
            "tearDown() not run in same process as setUp().")


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(
        loader.loadTestsFromTestCase(
            TestZopeTestInSubProcess))
    return suite
