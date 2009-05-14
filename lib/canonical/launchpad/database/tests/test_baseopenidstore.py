# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Tests for `BaseStormOpenIDStore`."""

__metaclass__ = type
__all__ = [
    'BaseStormOpenIDStoreTestsMixin',
    ]

import time
import unittest

from openid.association import Association
from openid.store import nonce

from canonical.launchpad.interfaces.lpstorm import IMasterStore
from canonical.launchpad.database.baseopenidstore import (
    BaseStormOpenIDStore)


class BaseStormOpenIDStoreTestsMixin:
    """Tests for `BaseStormOpenIDStore`."""

    def test_Class(self):
        self.assertIsInstance(self.store, BaseStormOpenIDStore)

    def test_storeAssociation(self):
        self.store.storeAssociation('server-url\xC2\xA9', Association(
                'handle', 'secret', 42, 600, 'HMAC-SHA1'))
        db_assoc = IMasterStore(self.store.Association).get(
            self.store.Association, (u'server-url\xA9', u'handle'))
        self.assertEquals(db_assoc.server_url, u'server-url\xA9')
        self.assertEquals(db_assoc.handle, u'handle')
        self.assertEquals(db_assoc.secret, 'secret')
        self.assertEquals(db_assoc.issued, 42)
        self.assertEquals(db_assoc.lifetime, 600)
        self.assertEquals(db_assoc.assoc_type, u'HMAC-SHA1')

    def test_getAssociation(self):
        timestamp = int(time.time())
        self.store.storeAssociation('server-url', Association(
                'handle', 'secret', timestamp, 600, 'HMAC-SHA1'))

        assoc = self.store.getAssociation('server-url', 'handle')
        self.assertIsInstance(assoc, Association)
        self.assertEquals(assoc.handle, 'handle')
        self.assertEquals(assoc.secret, 'secret')
        self.assertEquals(assoc.issued, timestamp)
        self.assertEquals(assoc.lifetime, 600)
        self.assertEquals(assoc.assoc_type, 'HMAC-SHA1')

    def test_getAssociation_unknown(self):
        assoc = self.store.getAssociation('server-url', 'unknown')
        self.assertEquals(assoc, None)

    def test_getAssociation_expired(self):
        lifetime = 600
        timestamp = int(time.time()) - 2 * lifetime
        self.store.storeAssociation('server-url', Association(
                'handle', 'secret', timestamp, lifetime, 'HMAC-SHA1'))
        # The association is not returned because it is out of date.
        # Further more, it is removed from the database.
        assoc = self.store.getAssociation('server-url', 'handle')
        self.assertEquals(assoc, None)

        store = IMasterStore(self.store.Association)
        db_assoc = store.get(
            self.store.Association, (u'server-url', u'handle'))
        self.assertEqual(db_assoc, None)

    def test_getAssociation_no_handle(self):
        timestamp = int(time.time())
        self.store.storeAssociation('server-url', Association(
                'handle1', 'secret', timestamp, 600, 'HMAC-SHA1'))
        self.store.storeAssociation('server-url', Association(
                'handle2', 'secret', timestamp + 1, 600, 'HMAC-SHA1'))

        # The most recent handle is returned.
        assoc = self.store.getAssociation('server-url', None)
        self.assertNotEqual(assoc, None)
        self.assertEqual(assoc.handle, 'handle2')

    def test_removeAssociation(self):
        self.assertEquals(
            self.store.removeAssociation('server-url', 'unknown'),
            False)

        timestamp = int(time.time())
        self.store.storeAssociation('server-url', Association(
                'handle', 'secret', timestamp, 600, 'HMAC-SHA1'))
        self.assertEquals(
            self.store.removeAssociation('server-url', 'handle'), True)
        self.assertEquals(
            self.store.getAssociation('server-url', 'handle'), None)

    def test_useNonce(self):
        timestamp = time.time()
        # The nonce can only be used once.
        self.assertEqual(
            self.store.useNonce('server-url', timestamp, 'salt'), True)
        self.assertEqual(
            self.store.useNonce('server-url', timestamp, 'salt'), False)
        self.assertEqual(
            self.store.useNonce('server-url', timestamp, 'salt'), False)

    def test_useNonce_expired(self):
        timestamp = time.time() - 2 * nonce.SKEW
        self.assertEqual(
            self.store.useNonce('server-url', timestamp, 'salt'), False)

    def test_useNonce_future(self):
        timestamp = time.time() + 2 * nonce.SKEW
        self.assertEqual(
            self.store.useNonce('server-url', timestamp, 'salt'), False)

    def test_cleanupNonces(self):
        timestamp = time.time()
        self.assertEqual(
            self.store.useNonce('server1', timestamp, 'salt1'), True)
        self.assertEqual(
            self.store.useNonce('server2', timestamp, 'salt2'), True)
        self.assertEqual(
            self.store.useNonce('server3', timestamp, 'salt3'), True)
        result = IMasterStore(self.store.Nonce).find(self.store.Nonce)
        self.assertEqual(result.count(), 3)

        self.assertEqual(
            self.store.cleanupNonces(_now=timestamp + 2 * nonce.SKEW), 3)
        result = IMasterStore(self.store.Nonce).find(self.store.Nonce)
        self.assertEqual(result.count(), 0)

        # The nonces have now been cleared:
        self.assertEqual(
            self.store.useNonce('server1', timestamp, 'salt1'), True)
        self.assertEqual(
            self.store.cleanupNonces(_now=timestamp + 2 * nonce.SKEW), 1)
        self.assertEqual(
            self.store.cleanupNonces(_now=timestamp + 2 * nonce.SKEW), 0)

    def test_cleanupAssociations(self):
        timestamp = int(time.time()) - 100
        self.store.storeAssociation('server-url', Association(
                'handle1', 'secret', timestamp, 50, 'HMAC-SHA1'))
        self.store.storeAssociation('server-url', Association(
                'handle2', 'secret', timestamp, 200, 'HMAC-SHA1'))

        self.assertEquals(self.store.cleanupAssociations(), 1)

        # The second (non-expired) association is left behind.
        self.assertNotEqual(
            self.store.getAssociation('server-url', 'handle2'), None)


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
