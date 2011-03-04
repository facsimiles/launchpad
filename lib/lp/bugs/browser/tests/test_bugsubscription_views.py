# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for BugSubscription views."""

__metaclass__ = type

from canonical.launchpad.ftests import LaunchpadFormHarness
from canonical.testing.layers import LaunchpadFunctionalLayer

from lp.bugs.browser.bugsubscription import (
    BugPortletSubcribersIds,
    BugSubscriptionListView,
    BugSubscriptionSubscribeSelfView,
    )
from lp.bugs.enum import BugNotificationLevel
from lp.testing import (
    feature_flags,
    person_logged_in,
    set_feature_flag,
    TestCaseWithFactory,
    )


class BugSubscriptionAdvancedFeaturesTestCase(TestCaseWithFactory):

    layer = LaunchpadFunctionalLayer

    def setUp(self):
        super(BugSubscriptionAdvancedFeaturesTestCase, self).setUp()
        with feature_flags():
            set_feature_flag(u'malone.advanced-subscriptions.enabled', u'on')

    def test_subscribe_uses_bug_notification_level(self):
        # When a user subscribes to a bug using the advanced features on
        # the Bug +subscribe page, the bug notification level they
        # choose is taken into account.
        bug = self.factory.makeBug()
        # We unsubscribe the bug's owner because if we don't there will
        # be two COMMENTS-level subscribers.
        with person_logged_in(bug.owner):
            bug.unsubscribe(bug.owner, bug.owner)

        # We don't display BugNotificationLevel.NOTHING as an option.
        # This is tested below.
        with feature_flags():
            displayed_levels = [
                level for level in BugNotificationLevel.items
                if level != BugNotificationLevel.NOTHING]
            for level in displayed_levels:
                person = self.factory.makePerson()
                with person_logged_in(person):
                    harness = LaunchpadFormHarness(
                        bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                    form_data = {
                        'field.subscription': person.name,
                        'field.bug_notification_level': level.title,
                        }
                    harness.submit('continue', form_data)

                subscription = bug.getSubscriptionForPerson(person)
                self.assertEqual(
                    level, subscription.bug_notification_level,
                    "Bug notification level of subscription should be %s, is "
                    "actually %s." % (
                        level.title,
                        subscription.bug_notification_level.title))

    def test_nothing_is_not_a_valid_level(self):
        # BugNotificationLevel.NOTHING isn't considered valid when
        # someone is trying to subscribe.
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                level = BugNotificationLevel.NOTHING
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                form_data = {
                    'field.subscription': person.name,
                    'field.bug_notification_level': level.title,
                    }
                harness.submit('continue', form_data)
                self.assertTrue(harness.hasErrors())
                self.assertEqual(
                    'Invalid value',
                    harness.getFieldError('bug_notification_level'),
                    "The view should treat BugNotificationLevel.NOTHING "
                    "as an invalid value.")

    def test_user_can_update_subscription(self):
        # A user can update their bug subscription using the
        # BugSubscriptionSubscribeSelfView.
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                bug.subscribe(person, person, BugNotificationLevel.COMMENTS)
                # Now the person updates their subscription so they're
                # subscribed at the METADATA level.
                level = BugNotificationLevel.METADATA
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                form_data = {
                    'field.subscription': 'update-subscription',
                    'field.bug_notification_level': level.title,
                    }
                harness.submit('continue', form_data)
                self.assertFalse(harness.hasErrors())

        subscription = bug.getSubscriptionForPerson(person)
        self.assertEqual(
            BugNotificationLevel.METADATA,
            subscription.bug_notification_level,
            "Bug notification level of subscription should be METADATA, is "
            "actually %s." % subscription.bug_notification_level.title)

    def test_user_can_unsubscribe(self):
        # A user can unsubscribe from a bug using the
        # BugSubscriptionSubscribeSelfView.
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                bug.subscribe(person, person)
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                form_data = {
                    'field.subscription': person.name,
                    }
                harness.submit('continue', form_data)

        subscription = bug.getSubscriptionForPerson(person)
        self.assertIs(
            None, subscription,
            "There should be no BugSubscription for this person.")

    def test_field_values_set_correctly_for_existing_subscriptions(self):
        # When a user who is already subscribed to a bug visits the
        # BugSubscriptionSubscribeSelfView, its bug_notification_level
        # field will be set according to their current susbscription
        # level.
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                # We subscribe using the harness rather than doing it
                # directly so that we don't have to commit() between
                # subscribing and checking the default value.
                level = BugNotificationLevel.METADATA
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                form_data = {
                    'field.subscription': person.name,
                    'field.bug_notification_level': level.title,
                    }
                harness.submit('continue', form_data)

                # The default value for the bug_notification_level field
                # should now be the same as the level used to subscribe
                # above.
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                bug_notification_level_widget = (
                    harness.view.widgets['bug_notification_level'])
                default_notification_level_value = (
                    bug_notification_level_widget._getDefault())
                self.assertEqual(
                    BugNotificationLevel.METADATA,
                    default_notification_level_value,
                    "Default value for bug_notification_level should be "
                    "METADATA, is actually %s"
                    % default_notification_level_value)

    def test_update_subscription_fails_if_user_not_subscribed(self):
        # If the user is not directly subscribed to the bug, trying to
        # update the subscription will fail (since you can't update a
        # subscription that doesn't exist).
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                level = BugNotificationLevel.METADATA
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                subscription_field = (
                    harness.view.form_fields['subscription'].field)
                # The update-subscription option won't appear.
                self.assertNotIn(
                    'update-subscription',
                    subscription_field.vocabulary.by_token)

    def test_update_subscription_fails_for_users_subscribed_via_teams(self):
        # If the user is not directly subscribed, but is subscribed via
        # a team, they will not be able to use the "Update my
        # subscription" option.
        bug = self.factory.makeBug()
        person = self.factory.makePerson()
        team = self.factory.makeTeam(owner=person)
        with feature_flags():
            with person_logged_in(person):
                bug.subscribe(team, person)
                level = BugNotificationLevel.METADATA
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                subscription_field = (
                    harness.view.form_fields['subscription'].field)
                # The update-subscription option won't appear.
                self.assertNotIn(
                    'update-subscription',
                    subscription_field.vocabulary.by_token)

    def test_bug_673288(self):
        # If the user is not directly subscribed, but is subscribed via
        # a team and via a duplicate, they will not be able to use the
        # "Update my subscription" option.
        # This is a regression test for bug 673288.
        bug = self.factory.makeBug()
        duplicate = self.factory.makeBug()
        person = self.factory.makePerson()
        team = self.factory.makeTeam(owner=person)
        with feature_flags():
            with person_logged_in(person):
                duplicate.markAsDuplicate(bug)
                duplicate.subscribe(person, person)
                bug.subscribe(team, person)

                level = BugNotificationLevel.METADATA
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                subscription_field = (
                    harness.view.form_fields['subscription'].field)
                # The update-subscription option won't appear.
                self.assertNotIn(
                    'update-subscription',
                    subscription_field.vocabulary.by_token)

    def test_bug_notification_level_field_hidden_for_dupe_subs(self):
        # If the user is subscribed to the bug via a duplicate, the
        # bug_notification_level field won't be visible on the form.
        bug = self.factory.makeBug()
        duplicate = self.factory.makeBug()
        person = self.factory.makePerson()
        with feature_flags():
            with person_logged_in(person):
                duplicate.markAsDuplicate(bug)
                duplicate.subscribe(person, person)
                harness = LaunchpadFormHarness(
                    bug.default_bugtask, BugSubscriptionSubscribeSelfView)
                self.assertFalse(
                    harness.view.widgets['bug_notification_level'].visible)


class BugPortletSubcribersIdsTests(TestCaseWithFactory):

    layer = LaunchpadFunctionalLayer

    def test_content_type(self):
        bug = self.factory.makeBug()

        person = self.factory.makePerson()
        with person_logged_in(person):
            harness = LaunchpadFormHarness(
                bug.default_bugtask, BugPortletSubcribersIds)
            harness.view.render()

        self.assertEqual(
            harness.request.response.getHeader('content-type'),
            'application/json')


class BugSubscriptionsListViewTestCase(TestCaseWithFactory):
    """Tests for the BugSubscriptionsListView."""

    layer = LaunchpadFunctionalLayer

    def setUp(self):
        super(BugSubscriptionsListViewTestCase, self).setUp()
        self.product = self.factory.makeProduct(
            name='widgetsrus', displayname='Widgets R Us')
        self.bug = self.factory.makeBug(product=self.product)
        self.subscriber = self.factory.makePerson()

    def getView(self):
        harness = LaunchpadFormHarness(
            self.bug.default_bugtask, BugSubscriptionListView)
        return harness.view

    def test_identify_structural_subscriptions(self):
        # This shows simply that we can identify the structural
        # subscriptions for the page.  The content will come later.
        view = self.getView()
        with person_logged_in(self.subscriber):
            sub = self.product.addBugSubscription(
                self.subscriber, self.subscriber)
            self.assertEqual(
                list(view.structural_subscriptions), [sub])

    def test_is_directly_subscribed(self):
        # Is the user directly subscribed to the bug.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.assertFalse(view.is_directly_subscribed)
            self.bug.subscribe(self.subscriber, self.subscriber)
            self.assertTrue(view.is_directly_subscribed)

    def test_is_directly_subscribed_team_is_not(self):
        # Subscription through team membership is not
        # a direct subscription.
        team = self.factory.makeTeam(owner=self.subscriber)
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(team, self.subscriber)
            self.assertFalse(view.is_directly_subscribed)

    def test_is_reporter(self):
        # Bug owner is the actual reporter of the bug.
        view = self.getView()
        with person_logged_in(self.bug.owner):
            self.assertTrue(view.is_reporter)

    def test_is_reporter_not(self):
        # A person different from a bug owner is not the reporter.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.assertFalse(view.is_reporter)

    def test_is_from_duplicate(self):
        # Is a person subscribed through a duplicate.
        duplicate = self.factory.makeBug()
        with person_logged_in(self.bug.owner):
            duplicate.markAsDuplicate(self.bug)

        view = self.getView()
        with person_logged_in(self.subscriber):
            duplicate.subscribe(self.subscriber, self.subscriber)
            self.assertTrue(view.is_from_duplicate)

    def test_is_from_duplicate_no(self):
        # A person is not subscribed through a duplicate
        # with a direct subscription.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(self.subscriber, self.subscriber)
            self.assertFalse(view.is_from_duplicate)

    def test_is_from_duplicate_team(self):
        # Is a person subscribed through a duplicate
        # when it is but through team membership.
        team = self.factory.makeTeam(members=[self.subscriber])
        duplicate = self.factory.makeBug()
        with person_logged_in(self.bug.owner):
            duplicate.markAsDuplicate(self.bug)

        view = self.getView()
        with person_logged_in(self.subscriber):
            duplicate.subscribe(team, self.subscriber)
            self.assertTrue(view.is_from_duplicate)

    def test_is_through_team_no(self):
        # A person is not subscribed through team
        # if they have a direct subscription.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(self.subscriber, self.subscriber)
            self.assertFalse(view.is_through_team)

    def test_is_through_team(self):
        # A person is subscribed through team if they are
        # part of a team that is directly subscribed.
        team = self.factory.makeTeam(members=[self.subscriber])
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(team, self.subscriber)
            self.assertTrue(view.is_through_team)

    def test_is_through_team_duplicate(self):
        # A person is subscribed through team if they are
        # part of a team that is subscribed to a duplicate.
        team = self.factory.makeTeam(members=[self.subscriber])
        duplicate = self.factory.makeBug()
        with person_logged_in(self.bug.owner):
            duplicate.markAsDuplicate(self.bug)

        view = self.getView()
        with person_logged_in(self.subscriber):
            duplicate.subscribe(team, self.subscriber)
            self.assertTrue(view.is_through_team)

    def test_is_team_admin_no_team(self):
        # A person is not a team admin if they have a direct subscription.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(self.subscriber, self.subscriber)
            self.assertFalse(view.is_team_admin)

    def test_is_team_admin_no(self):
        # A person is not a team admin if they are just a regular
        # team member.
        team = self.factory.makeTeam(members=[self.subscriber])
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.bug.subscribe(team, self.subscriber)
            self.assertFalse(view.is_team_admin)

    def test_is_team_admin(self):
        # A person is a team admin if they are a team admin.
        team = self.factory.makeTeam()
        view = self.getView()
        with person_logged_in(team.teamowner):
            self.bug.subscribe(team, team.teamowner)
            self.assertTrue(view.is_team_admin)

    def test_is_team_admin_duplicate(self):
        # A person is a team admin if they admin the team
        # that is subscribed to the duplicate.
        team = self.factory.makeTeam()
        duplicate = self.factory.makeBug()
        with person_logged_in(self.bug.owner):
            duplicate.markAsDuplicate(self.bug)

        view = self.getView()
        with person_logged_in(team.teamowner):
            duplicate.subscribe(team, team.teamowner)
            self.assertTrue(view.is_team_admin)

    def test_is_target_owner_no(self):
        # A person is a target owner if they are owner for
        # any of the targets of any of the bug tasks.
        view = self.getView()
        with person_logged_in(self.subscriber):
            self.assertFalse(view.is_target_owner)

    def test_is_target_owner(self):
        # A person is a target owner if they are owner for
        # any of the targets of any of the bug tasks.
        # In this case, we are logged in as the default
        # bug task target owner.
        target = self.bug.default_bugtask.target
        view = self.getView()
        with person_logged_in(target.owner):
            self.assertTrue(view.is_target_owner)

    def test_is_target_owner_mixed(self):
        # A person is a target owner if they are owner for
        # any of the targets of any of the bug tasks:
        # in this "mixed" case, we are logged in as
        # the non-default bug task target owner.
        bugtask = self.factory.makeBugTask(bug=self.bug)
        target = bugtask.target
        view = self.getView()
        with person_logged_in(target.owner):
            self.assertTrue(view.is_target_owner)
