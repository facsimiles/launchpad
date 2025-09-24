# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test harness for mailinglist views unit tests."""

import transaction
from zope.component import getUtility

from lp.services.messages.interfaces.message import IMessageSet
from lp.testing import TestCaseWithFactory, login_person, person_logged_in
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.pages import find_tag_by_id
from lp.testing.views import create_view


class MailingListTestCase(TestCaseWithFactory):
    """Verify the content in +mailing-list-portlet."""

    def makeTeamWithMailingList(self, name=None, owner=None, visibility=None):
        if owner is None:
            owner = self.factory.makePerson()
        team = self.factory.makeTeam(
            name=name, owner=owner, visibility=visibility
        )
        login_person(owner)
        self.factory.makeMailingList(team=team, owner=owner)
        return team

    def makeHeldMessage(self, team, sender=None):
        # Requires LaunchpadFunctionalLayer.
        if sender is None:
            sender = self.factory.makePerson(
                email="him@eg.dom", name="him", displayname="Him"
            )
        raw = "\n".join(
            [
                "From: Him <him@eg.dom>",
                "To: %s" % team.mailing_list.address,
                "Subject: monkey",
                "Message-ID: <monkey>",
                "Date: Fri, 01 Aug 2000 01:09:00 -0000",
                "",
                "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
            ]
        ).encode("ASCII")
        message_set = getUtility(IMessageSet)
        message = message_set.fromEmail(raw)
        transaction.commit()
        held_message = team.mailing_list.holdMessage(message)
        return sender, message, held_message


class MailingListSubscriptionControlsTestCase(TestCaseWithFactory):
    """Verify the team index subscribe/unsubscribe to mailing list content."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.a_team = self.factory.makeTeam(name="a")
        self.b_team = self.factory.makeTeam(name="b", owner=self.a_team)
        self.b_team_list = self.factory.makeMailingList(
            team=self.b_team, owner=self.b_team.teamowner
        )
        self.user = self.factory.makePerson()
        with person_logged_in(self.a_team.teamowner):
            self.a_team.addMember(self.user, self.a_team.teamowner)

    def test_subscribe_control_renders(self):
        login_person(self.user)
        view = create_view(
            self.b_team,
            name="+index",
            principal=self.user,
            server_url="http://launchpad.test",
            path_info="/~%s" % self.b_team.name,
        )
        content = view.render()
        link_tag = find_tag_by_id(content, "link-list-subscribe")
        self.assertIsNone(link_tag)

    def test_subscribe_control_doesnt_render_for_non_member(self):
        other_person = self.factory.makePerson()
        login_person(other_person)
        view = create_view(
            self.b_team,
            name="+index",
            principal=other_person,
            server_url="http://launchpad.test",
            path_info="/~%s" % self.b_team.name,
        )
        content = view.render()
        self.assertNotEqual("", content)
        link_tag = find_tag_by_id(content, "link-list-subscribe")
        self.assertEqual(None, link_tag)
