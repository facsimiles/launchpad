# Copyright 2007 Canonical Ltd.  All rights reserved.

"""Tests confirming that changing isolation levels does what we expect."""

__metaclass__ = type
__all__ = []

import unittest

from canonical.database.sqlbase import (
        cursor, SERIALIZABLE_ISOLATION, READ_COMMITTED_ISOLATION,
        AUTOCOMMIT_ISOLATION,
        )
from canonical.testing.layers import LaunchpadZopelessLayer

class TestIsolation(unittest.TestCase):
    layer = LaunchpadZopelessLayer

    def setUp(self):
        self.txn = LaunchpadZopelessLayer.txn

    def getCurrentIsolation(self):
        cur = cursor()
        cur.execute("SELECT * FROM Person")
        cur.execute("SHOW transaction_isolation")
        return cur.fetchone()[0]

    def test_autocommit(self):
        self.txn.set_isolation_level(AUTOCOMMIT_ISOLATION)
        # There is no actual 'autocommit' mode in PostgreSQL. psycopg
        # implements this feature by using read committed isolation and
        # issuing commit() statements after every query.
        self.failUnlessEqual(self.getCurrentIsolation(), 'read committed')

        # So we need to confirm we are actually in autocommit mode
        # by seeing if we an roll back
        con = self.txn.conn()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM Person WHERE password IS NULL")
        self.failIfEqual(cur.fetchone()[0], 0)
        cur.execute("UPDATE Person SET password=NULL")
        con.rollback()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM Person WHERE password IS NOT NULL")
        self.failUnlessEqual(cur.fetchone()[0], 0)

    def test_readCommitted(self):
        self.txn.set_isolation_level(READ_COMMITTED_ISOLATION)
        self.failUnlessEqual(self.getCurrentIsolation(), 'read committed')

    def test_serializable(self):
        self.txn.set_isolation_level(SERIALIZABLE_ISOLATION)
        self.failUnlessEqual(self.getCurrentIsolation(), 'serializable')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIsolation))
    return suite

