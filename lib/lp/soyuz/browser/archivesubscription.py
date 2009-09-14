# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=F0401

"""Browser views related to archive subscriptions."""

__metaclass__ = type

__all__ = [
    'ArchiveSubscribersView',
    'PersonalArchiveSubscriptionBreadcrumb',
    'PersonArchiveSubscriptionView',
    'PersonArchiveSubscriptionsView',
    'traverse_archive_subscription_for_subscriber'
    ]

import datetime

import pytz

from zope.app.form import CustomWidgetFactory
from zope.app.form.browser import TextWidget
from zope.component import getUtility
from zope.formlib import form
from zope.interface import Interface, implements
from zope.schema import Date, Text

from canonical.cachedproperty import cachedproperty
from canonical.launchpad import _
from canonical.launchpad.fields import ParticipatingPersonChoice
from lp.soyuz.browser.sourceslist import (
    SourcesListEntries, SourcesListEntriesView)
from lp.soyuz.interfaces.archive import IArchiveSet
from lp.soyuz.interfaces.archiveauthtoken import (
    IArchiveAuthTokenSet)
from lp.soyuz.interfaces.archivesubscriber import (
    IArchiveSubscriberSet, IPersonalArchiveSubscription)
from canonical.launchpad.webapp.breadcrumb import Breadcrumb
from canonical.launchpad.webapp.launchpadform import (
    action, custom_widget, LaunchpadFormView, LaunchpadEditFormView)
from canonical.launchpad.webapp.publisher import (
    canonical_url, LaunchpadView, Navigation)
from canonical.widgets import DateWidget
from canonical.widgets.popup import PersonPickerWidget


def archive_subscription_ui_adapter(archive_subscription):
    """Adapt an archive subscriber to the UI interface.

    Since we are only modifying the type of fields that already exist
    on IArchiveSubscriber, we simply return the archive_subscriber record.
    """
    return archive_subscription


class PersonalArchiveSubscription:
    """See `IPersonalArchiveSubscription`."""

    implements(IPersonalArchiveSubscription)

    def __init__(self, subscriber, archive):
        self.subscriber = subscriber
        self.archive = archive

    @property
    def displayname(self):
        """See `IPersonalArchiveSubscription`."""
        return "Access to %s" % self.archive.displayname

    @property
    def title(self):
        """Required for default headings in templates."""
        return self.displayname


class PersonalArchiveSubscriptionNavigation(Navigation):
    """Navigation for `IPersonalArchiveSubscription`.

    Without this, a breadcrumb will not be created for personal
    archive subscription objects.
    """
    usedfor = IPersonalArchiveSubscription

def traverse_archive_subscription_for_subscriber(subscriber, archive_id):
    """Return the subscription for a subscriber to an archive."""
    subscription = None
    archive = getUtility(IArchiveSet).get(archive_id)
    if archive:
        subscription = getUtility(IArchiveSubscriberSet).getBySubscriber(
            subscriber, archive=archive).first()

    if subscription is None:
        return None
    else:
        return PersonalArchiveSubscription(subscriber, archive)


class PersonalArchiveSubscriptionBreadcrumb(Breadcrumb):
    """Builds a breadcrumb for `PersonalArchiveSubscription`."""

    @property
    def text(self):
        return self.context.displayname


class IArchiveSubscriberUI(Interface):
    """A custom interface for user interaction with archive subscriptions.

    IArchiveSubscriber uses a datetime field for date_expires, whereas
    we simply want to use a date field when users create or edit new
    subscriptions.
    """
    subscriber = ParticipatingPersonChoice(
        title=_("Subscriber"), required=True, vocabulary='ValidPersonOrTeam',
        description=_("The person or team to grant access."))

    date_expires = Date(
        title=_("Date of Expiration"), required=False,
        description=_("The date when the access will expire. "
                      "Leave this blank for access that should "
                      "never expire."))

    description = Text(
        title=_("Description"), required=False,
        description=_("Optional notes about this access."))


class ArchiveSubscribersView(LaunchpadFormView):
    """A view for listing and creating archive subscribers."""

    schema = IArchiveSubscriberUI
    field_names = ['subscriber', 'date_expires', 'description']
    custom_widget('description', TextWidget, displayWidth=40)
    custom_widget('date_expires', CustomWidgetFactory(DateWidget))
    custom_widget('subscriber', PersonPickerWidget,
        header="Select the subscriber")

    def initialize(self):
        """Ensure that we are dealing with a private archive."""
        # If this archive is not private, then we should not be
        # managing the subscribers.
        if not self.context.private:
            self.request.response.addNotification(
                "Only private archives can have subscribers.")
            self.request.response.redirect(
                canonical_url(self.context))
            return

        super(ArchiveSubscribersView, self).initialize()

    @property
    def subscriptions(self):
        """Return all the subscriptions for this archive."""
        return getUtility(IArchiveSubscriberSet).getByArchive(
            self.context)

    @cachedproperty
    def has_subscriptions(self):
        """Return whether this archive has any subscribers."""
        # XXX noodles 20090212 bug=246200: use bool() when it gets fixed
        # in storm.
        return self.subscriptions.any() is not None

    def validate_new_subscription(self, action, data):
        """Ensure the subscriber isn't already subscribed.

        Also ensures that the expiry date is in the future.
        """
        form.getWidgetsData(self.widgets, 'field', data)
        subscriber = data.get('subscriber')
        date_expires = data.get('date_expires')

        if subscriber is not None:
            subscriber_set = getUtility(IArchiveSubscriberSet)
            current_subscription = subscriber_set.getBySubscriber(
                subscriber, archive=self.context)

            # XXX noodles 20090212 bug=246200: use bool() when it gets fixed
            # in storm.
            if current_subscription.any() is not None:
                self.setFieldError('subscriber',
                    "%s is already subscribed." % subscriber.displayname)

        if date_expires:
            if date_expires < datetime.date.today():
                self.setFieldError('date_expires',
                    "The expiry date must be in the future.")

    @action(u"Add", name="add",
            validator="validate_new_subscription")
    def create_subscription(self, action, data):
        """Create a subscription for the supplied user."""
        # As we present a date selection to the user for expiry, we
        # need to convert the value into a datetime with UTC:
        date_expires = data['date_expires']
        if date_expires:
            date_expires = datetime.datetime(
                date_expires.year,
                date_expires.month,
                date_expires.day,
                tzinfo=pytz.timezone('UTC'))
        self.context.newSubscription(
            data['subscriber'],
            self.user,
            description=data['description'],
            date_expires=date_expires)

        subscriber_individuals = data['subscriber'].displayname
        if data['subscriber'].is_team:
            subscriber_individuals = "Members of " + subscriber_individuals

        notification = (
            "You have granted access for %(subscriber)s to install "
            "software from %(archive)s. "
            "%(subscriber_individuals)s will be notified of the access "
            " via email."
            ) % {
                'subscriber': data['subscriber'].displayname,
                'archive': self.context.displayname,
                'subscriber_individuals': subscriber_individuals,
                }

        self.request.response.addNotification(notification)

        # Just ensure a redirect happens (back to ourselves).
        self.next_url = str(self.request.URL)


class ArchiveSubscriptionEditView(LaunchpadEditFormView):
    """A view for editing and canceling an archive subscriber."""

    schema = IArchiveSubscriberUI
    field_names = ['date_expires', 'description']
    custom_widget('description', TextWidget, displayWidth=40)
    custom_widget('date_expires', CustomWidgetFactory(DateWidget))

    def validate_update_subscription(self, action, data):
        """Ensure that the date of expiry is not in the past."""
        form.getWidgetsData(self.widgets, 'field', data)
        date_expires = data.get('date_expires')

        if date_expires:
            if date_expires < datetime.date.today():
                self.setFieldError('date_expires',
                    "The expiry date must be in the future.")

    @action(
        u'Save', name='update', validator="validate_update_subscription")
    def update_subscription(self, action, data):
        """Update the context subscription with the new data."""
        # As we present a date selection to the user for expiry, we
        # need to convert the value into a datetime with UTC:
        date_expires = data['date_expires']

        if date_expires:
            data['date_expires'] = datetime.datetime(
                date_expires.year,
                date_expires.month,
                date_expires.day,
                tzinfo=pytz.timezone('UTC'))

        self.updateContextFromData(data)

        notification = "The access for %s has been updated." % (
            self.context.subscriber.displayname)
        self.request.response.addNotification(notification)

    @action(u'Cancel access', name='cancel')
    def cancel_subscription(self, action, data):
        """Cancel the context subscription."""
        self.context.cancel(self.user)

        notification = "You have cancelled %s's subscription to %s." % (
            self.context.subscriber.displayname,
            self.context.archive.displayname)
        self.request.response.addNotification(notification)

    @property
    def next_url(self):
        """Calculate and return the url to which we want to redirect."""
        return canonical_url(self.context.archive) + "/+subscriptions"

    @property
    def cancel_url(self):
        """Return the url to which we want to go to if user cancels."""
        return self.next_url


class PersonArchiveSubscriptionsView(LaunchpadView):
    """A view for displaying a persons archive subscriptions."""

    # XXX Michael Nelson 20090911 bug=417089. This should be removed
    # when bug 417089 lands.
    page_title = "Private PPA access"

    @cachedproperty
    def subscriptions_with_tokens(self):
        """Return all the persons archive subscriptions with the token
        for each.

        The result is formatted as a list of dicts to make the TALS code
        cleaner.
        """
        subscriber_set = getUtility(IArchiveSubscriberSet)
        subs_with_tokens = subscriber_set.getBySubscriberWithActiveToken(
            self.context)

        # Turn the result set into a list of dicts so it can be easily
        # accessed in TAL:
        return [
            dict(subscription=PersonalArchiveSubscription(self.context,
                                                          subscr.archive),
                 token=token)
            for subscr, token in subs_with_tokens]


class PersonArchiveSubscriptionView(LaunchpadView):
    """Display a user's archive subscription and relevant info.

    This includes the current sources.list entries (if the subscription
    has a current token), and the ability to generate and re-generate
    tokens.
    """

    @property
    def label(self):
        """Return the label used for the main heading."""
        return self.context.title

    def initialize(self):
        """Process any posted actions."""
        super(PersonArchiveSubscriptionView, self).initialize()

        # If an activation was requested and there isn't a currently
        # active token, then create a token, provided a notification
        # and redirect.
        if self.request.form.get('activate') and not self.active_token:
            token = self.context.archive.newAuthToken(self.context.subscriber)

            self.request.response.redirect(self.request.getURL())

        # Otherwise, if a regeneration was requested and there is an
        # active token, then cancel the old token, create a new one,
        # provide a notification and redirect.
        elif self.request.form.get('regenerate') and self.active_token:
            self.active_token.deactivate()

            token = self.context.archive.newAuthToken(self.context.subscriber)

            self.request.response.addNotification(
                "Launchpad has generated the new password you requested "
                "for your access to the archive %s. Please follow "
                "the instructions below to update your custom "
                "\"sources.list\"." % self.context.archive.displayname)

            self.request.response.redirect(self.request.getURL())

    @cachedproperty
    def sources_list_entries(self):
        """Setup and return the sources list entries widget."""
        if self.active_token is None:
            return None

        comment = "Personal access of %s to %s" % (
            self.context.subscriber.displayname,
            self.context.archive.displayname)

        entries = SourcesListEntries(
            self.context.archive.distribution,
            self.active_token.archive_url,
            self.context.archive.series_with_sources)

        return SourcesListEntriesView(entries, self.request, comment=comment)

    @cachedproperty
    def active_token(self):
        """Returns the corresponding current token for this subscription."""
        token_set = getUtility(IArchiveAuthTokenSet)
        return token_set.getActiveTokenForArchiveAndPerson(
            self.context.archive, self.context.subscriber)



