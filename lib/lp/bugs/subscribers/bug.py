# Copyright 2009, 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = [
    'add_bug_change_notifications',
    'get_bug_delta',
    'get_bugtask_indirect_subscribers',
    'notify_bug_added',
    'notify_bug_attachment_added',
    'notify_bug_attachment_removed',
    'notify_bug_comment_added',
    'notify_bug_modified',
    'notify_bug_subscription_added',
    'send_bug_details_to_new_bug_subscribers',
    ]


import datetime
from operator import attrgetter

from zope.component import getUtility

from canonical.config import config
from canonical.database.sqlbase import block_implicit_flushes
from canonical.launchpad.helpers import get_contact_email_addresses
from canonical.launchpad.mail import (
    format_address,
    sendmail,
    )
from canonical.launchpad.webapp.publisher import canonical_url
from lp.bugs.adapters.bugchange import (
    BugDuplicateChange,
    BugTaskAssigneeChange,
    get_bug_changes,
    )
from lp.bugs.adapters.bugdelta import BugDelta
from lp.bugs.interfaces.bugchange import IBugChange
from lp.bugs.interfaces.bugtask import IBugTaskSet
from lp.bugs.mail.bugnotificationbuilder import BugNotificationBuilder
from lp.bugs.mail.bugnotificationrecipients import BugNotificationRecipients
from lp.bugs.mail.newbug import generate_bug_add_email
from lp.registry.enum import BugNotificationLevel
from lp.registry.interfaces.person import IPerson


@block_implicit_flushes
def notify_bug_added(bug, event):
    """Send an email notification that a bug was added.

    Event must be an IObjectCreatedEvent.
    """
    bug.addCommentNotification(bug.initial_message)


@block_implicit_flushes
def notify_bug_modified(bug, event):
    """Handle bug change events.

    Subscribe the security contacts for a bug when it becomes
    security-related, and add notifications for the changes.
    """
    if (event.object.security_related and
        not event.object_before_modification.security_related):
        # The bug turned out to be security-related, subscribe the security
        # contact.
        for pillar in bug.affected_pillars:
            if pillar.security_contact is not None:
                bug.subscribe(pillar.security_contact, IPerson(event.user))

    bug_delta = get_bug_delta(
        old_bug=event.object_before_modification,
        new_bug=event.object, user=IPerson(event.user))

    if bug_delta is not None:
        add_bug_change_notifications(bug_delta)


@block_implicit_flushes
def notify_bug_comment_added(bugmessage, event):
    """Notify CC'd list that a message was added to this bug.

    bugmessage must be an IBugMessage. event must be an
    IObjectCreatedEvent. If bugmessage.bug is a duplicate the
    comment will also be sent to the dup target's subscribers.
    """
    bug = bugmessage.bug
    bug.addCommentNotification(bugmessage.message)


@block_implicit_flushes
def notify_bug_attachment_added(bugattachment, event):
    """Notify CC'd list that a new attachment has been added.

    bugattachment must be an IBugAttachment. event must be an
    IObjectCreatedEvent.
    """
    bug = bugattachment.bug
    bug_delta = BugDelta(
        bug=bug,
        bugurl=canonical_url(bug),
        user=IPerson(event.user),
        attachment={'new': bugattachment, 'old': None})

    add_bug_change_notifications(bug_delta)


@block_implicit_flushes
def notify_bug_attachment_removed(bugattachment, event):
    """Notify that an attachment has been removed."""
    bug = bugattachment.bug
    bug_delta = BugDelta(
        bug=bug,
        bugurl=canonical_url(bug),
        user=IPerson(event.user),
        attachment={'old': bugattachment, 'new': None})

    add_bug_change_notifications(bug_delta)


@block_implicit_flushes
def notify_bug_subscription_added(bug_subscription, event):
    """Notify that a new bug subscription was added."""
    # When a user is subscribed to a bug by someone other
    # than themselves, we send them a notification email.
    if bug_subscription.person != bug_subscription.subscribed_by:
        send_bug_details_to_new_bug_subscribers(
            bug_subscription.bug, [], [bug_subscription.person],
            subscribed_by=bug_subscription.subscribed_by)


def get_bug_delta(old_bug, new_bug, user):
    """Compute the delta from old_bug to new_bug.

    old_bug and new_bug are IBug's. user is an IPerson. Returns an
    IBugDelta if there are changes, or None if there were no changes.
    """
    changes = {}

    for field_name in ("title", "description", "name", "private",
                       "security_related", "duplicateof", "tags"):
        # fields for which we show old => new when their values change
        old_val = getattr(old_bug, field_name)
        new_val = getattr(new_bug, field_name)
        if old_val != new_val:
            changes[field_name] = {}
            changes[field_name]["old"] = old_val
            changes[field_name]["new"] = new_val

    if changes:
        changes["bug"] = new_bug
        changes["bug_before_modification"] = old_bug
        changes["bugurl"] = canonical_url(new_bug)
        changes["user"] = user
        return BugDelta(**changes)
    else:
        return None


def get_bugtask_indirect_subscribers(bugtask, recipients=None, level=None):
    """Return the indirect subscribers for a bug task.

    Return the list of people who should get notifications about
    changes to the task because of having an indirect subscription
    relationship with it (by subscribing to its target, being an
    assignee or owner, etc...)

    If `recipients` is present, add the subscribers to the set of
    bug notification recipients.
    """
    if bugtask.bug.private:
        return set()

    also_notified_subscribers = set()

    # Assignees are indirect subscribers.
    if bugtask.assignee:
        also_notified_subscribers.add(bugtask.assignee)
        if recipients is not None:
            recipients.addAssignee(bugtask.assignee)

    # Get structural subscribers.
    also_notified_subscribers.update(
        getUtility(IBugTaskSet).getStructuralSubscribers(
            [bugtask], recipients, level))

    # If the target's bug supervisor isn't set,
    # we add the owner as a subscriber.
    pillar = bugtask.pillar
    if pillar.bug_supervisor is None:
        also_notified_subscribers.add(pillar.owner)
        if recipients is not None:
            recipients.addRegistrant(pillar.owner, pillar)

    # XXX: GavinPanella 2010-11-30: What about if the bug supervisor *is* set?
    # Don't we want to send mail to him/her?

    return sorted(
        also_notified_subscribers,
        key=attrgetter('displayname'))


def add_bug_change_notifications(bug_delta, old_bugtask=None,
                                 new_subscribers=None):
    """Generate bug notifications and add them to the bug."""
    changes = get_bug_changes(bug_delta)
    recipients = bug_delta.bug.getBugNotificationRecipients(
        old_bug=bug_delta.bug_before_modification,
        level=BugNotificationLevel.METADATA)
    if old_bugtask is not None:
        old_bugtask_recipients = BugNotificationRecipients()
        get_bugtask_indirect_subscribers(
            old_bugtask, recipients=old_bugtask_recipients,
            level=BugNotificationLevel.METADATA)
        recipients.update(old_bugtask_recipients)
    for change in changes:
        # XXX 2009-03-17 gmb [bug=344125]
        #     This if..else should be removed once the new BugChange API
        #     is complete and ubiquitous.
        if IBugChange.providedBy(change):
            if isinstance(change, BugDuplicateChange):
                no_dupe_master_recipients = (
                    bug_delta.bug.getBugNotificationRecipients(
                        old_bug=bug_delta.bug_before_modification,
                        level=BugNotificationLevel.METADATA,
                        include_master_dupe_subscribers=False))
                bug_delta.bug.addChange(
                    change, recipients=no_dupe_master_recipients)
            elif (isinstance(change, BugTaskAssigneeChange) and
                  new_subscribers is not None):
                for person in new_subscribers:
                    reason, rationale = recipients.getReason(person)
                    if 'Assignee' in rationale:
                        recipients.remove(person)
                bug_delta.bug.addChange(change, recipients=recipients)
            else:
                bug_delta.bug.addChange(change, recipients=recipients)
        else:
            bug_delta.bug.addChangeNotification(
                change, person=bug_delta.user, recipients=recipients)


def send_bug_details_to_new_bug_subscribers(
    bug, previous_subscribers, current_subscribers, subscribed_by=None,
    event_creator=None):
    """Send an email containing full bug details to new bug subscribers.

    This function is designed to handle situations where bugtasks get
    reassigned to new products or sourcepackages, and the new bug subscribers
    need to be notified of the bug.
    """
    prev_subs_set = set(previous_subscribers)
    cur_subs_set = set(current_subscribers)
    new_subs = cur_subs_set.difference(prev_subs_set)

    to_addrs = set()
    for new_sub in new_subs:
        to_addrs.update(get_contact_email_addresses(new_sub))

    if not to_addrs:
        return

    from_addr = format_address(
        'Launchpad Bug Tracker',
        "%s@%s" % (bug.id, config.launchpad.bugs_domain))
    # Now's a good a time as any for this email; don't use the original
    # reported date for the bug as it will just confuse mailer and
    # recipient.
    email_date = datetime.datetime.now()

    # The new subscriber email is effectively the initial message regarding
    # a new bug. The bug's initial message is used in the References
    # header to establish the message's context in the email client.
    references = [bug.initial_message.rfc822msgid]
    recipients = bug.getBugNotificationRecipients()

    bug_notification_builder = BugNotificationBuilder(bug, event_creator)
    for to_addr in sorted(to_addrs):
        reason, rationale = recipients.getReason(to_addr)
        subject, contents = generate_bug_add_email(
            bug, new_recipients=True, subscribed_by=subscribed_by,
            reason=reason, event_creator=event_creator)
        msg = bug_notification_builder.build(
            from_addr, to_addr, contents, subject, email_date,
            rationale=rationale, references=references)
        sendmail(msg)
