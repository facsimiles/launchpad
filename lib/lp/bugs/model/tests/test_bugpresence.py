# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for the bugpresence model."""

from testtools.testcase import ExpectedException
from zope.security.interfaces import Unauthorized
from zope.security.management import checkPermission

from lp.app.enums import InformationType
from lp.testing import TestCaseWithFactory, admin_logged_in, person_logged_in
from lp.testing.layers import DatabaseFunctionalLayer


class TestBugPresence(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.bug = self.factory.makeBug(
            information_type=InformationType.PRIVATESECURITY
        )
        self.bugpresence = self.factory.makeBugPresence(bug=self.bug)

    def test_view_denied_to_anonymous(self):
        self.assertFalse(checkPermission("launchpad.View", self.bugpresence))
        with ExpectedException(Unauthorized):
            self.assertEqual(self.bugpresence.bug, self.bug)

    def test_view_denied_to_random_user(self):
        with person_logged_in(self.factory.makePerson()):
            self.assertFalse(
                checkPermission("launchpad.View", self.bugpresence)
            )
            with ExpectedException(Unauthorized):
                self.assertEqual(self.bugpresence.bug, self.bug)

    def test_view_allowed_if_bug_visible(self):
        """If user can see a bug, they can see its bug presence"""
        # Subscribe a person to see the bug
        person = self.factory.makePerson()
        with admin_logged_in() as admin:
            self.bug.subscribe(person, admin)

        with person_logged_in(person):
            self.assertTrue(
                checkPermission("launchpad.View", self.bugpresence)
            )
            self.assertEqual(self.bugpresence.bug, self.bug)

    def test_delete_denied_to_anonymous(self):
        """Even if annonymous user can see a bugpresence, they cannot delete
        it"""
        bug = self.factory.makeBug()
        bugpresence = self.factory.makeBugPresence(bug=bug)

        self.assertFalse(checkPermission("launchpad.Delete", bugpresence))
        with ExpectedException(Unauthorized):
            self.bugpresence.destroySelf()

    def test_delete_denied_even_if_bug_visible(self):
        """Even if a user can see a bugpresence, they cannot delete it"""
        person = self.factory.makePerson()
        with admin_logged_in() as admin:
            self.bug.subscribe(person, admin)
        with person_logged_in(person):
            self.assertTrue(
                checkPermission("launchpad.View", self.bugpresence)
            )
            self.assertFalse(
                checkPermission("launchpad.Delete", self.bugpresence)
            )
            with ExpectedException(Unauthorized):
                self.bugpresence.destroySelf()

    def test_delete_allowed_to_admin(self):
        """Admin can delete a bug presence"""
        with admin_logged_in():
            self.assertTrue(
                checkPermission("launchpad.Delete", self.bugpresence)
            )
            self.bugpresence.destroySelf()
