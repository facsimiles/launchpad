# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for the bugnotificationrecipients module."""

__metaclass__ = type

import unittest

from canonical.testing import DatabaseFunctionalLayer

from lp.bugs.mail.bugnotificationrecipients import (
    BugNotificationRecipientReason)
from lp.testing import TestCaseWithFactory


class BugNotificationRecipientReasonTestCase(TestCaseWithFactory):
    """A TestCase for the `BugNotificationRecipientReason` class."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(BugNotificationRecipientReasonTestCase, self).setUp()
        self.person = self.factory.makePerson()
        self.team = self.factory.makeTeam(owner=self.person)

    def _assertReasonAndHeaderAreCorrect(self, recipient_reason,
                                         expected_reason, expected_header):
        self.assertEqual(expected_header, recipient_reason.mail_header)
        self.assertEqual(expected_reason, recipient_reason.getReason())

    def test_forDupeSubscriber(self):
        duplicate_bug = self.factory.makeBug()
        reason = BugNotificationRecipientReason.forDupeSubscriber(
            self.person, duplicate_bug)

        expected_header = (
            'Subscriber to Duplicate via Bug %s' % duplicate_bug.id)
        expected_reason = (
            'You received this bug notification because you are a direct '
            'subscriber to duplicate bug %s.' % duplicate_bug.id)
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forDupeSubscriber_for_team(self):
        duplicate_bug = self.factory.makeBug()
        reason = BugNotificationRecipientReason.forDupeSubscriber(
            self.team, duplicate_bug)

        expected_header = 'Subscriber to Duplicate @%s via Bug %s' % (
            self.team.name, duplicate_bug.id)
        expected_reason = (
            'You received this bug notification because your team %s is '
            'a direct subscriber to duplicate bug %s.' % (
                self.team.displayname, duplicate_bug.id))
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forDirectSubscriber(self):
        reason = BugNotificationRecipientReason.forDirectSubscriber(
            self.person)

        expected_header = "Subscriber"
        expected_reason = (
            "You received this bug notification because you are a direct "
            "subscriber to the bug.")
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forDirectSubscriber_for_team(self):
        reason = BugNotificationRecipientReason.forDirectSubscriber(
            self.team)

        expected_header = "Subscriber @%s" % self.team.name
        expected_reason = (
            "You received this bug notification because your team %s is "
            "a direct subscriber to the bug." % self.team.displayname)
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forAssignee(self):
        reason = BugNotificationRecipientReason.forAssignee(self.person)

        expected_header = "Assignee"
        expected_reason = (
            "You received this bug notification because you are a bug "
            "assignee.")

        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forAssignee_for_team(self):
        reason = BugNotificationRecipientReason.forAssignee(self.team)

        expected_header = "Assignee @%s" % self.team.name
        expected_reason = (
            "You received this bug notification because your team %s is "
            "a bug assignee." % self.team.displayname)

        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forDistroBugSupervisor(self):
        distro = self.factory.makeDistribution()
        reason = BugNotificationRecipientReason.forDistroBugSupervisor(
            self.person, distro)

        expected_header = "Bug Supervisor (%s)" % distro.displayname
        expected_reason = (
            "You received this bug notification because you are the bug "
            "supervisor for %s." % distro.displayname)
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forDistroBugSupervisor_for_team(self):
        distro = self.factory.makeDistribution()
        reason = BugNotificationRecipientReason.forDistroBugSupervisor(
            self.team, distro)

        expected_header = "Bug Supervisor (%s) @%s" % (
            distro.displayname, self.team.name)
        expected_reason = (
            "You received this bug notification because your team %s is the "
            "bug supervisor for %s." %
                (self.team.displayname, distro.displayname))
        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)

    def test_forStructuralSubscriber(self):
        target = self.factory.makeProduct()
        reason = BugNotificationRecipientReason.forStructuralSubscriber(
            self.person, target)

        expected_header = "Subscriber (%s)" % target.displayname
        expected_reason = (
            "You received this bug notification because you are subscribed "
            "to %s." % target.displayname)

        self._assertReasonAndHeaderAreCorrect(
            reason, expected_reason, expected_header)


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
