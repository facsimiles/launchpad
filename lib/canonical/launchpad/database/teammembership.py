# Copyright 2005 Canonical Ltd.  All rights reserved.
# pylint: disable-msg=E0611,W0212

__metaclass__ = type
__all__ = [
    'TeamMembership',
    'TeamMembershipSet',
    'TeamParticipation',
    ]

from datetime import datetime, timedelta
import itertools
import pytz

from zope.component import getUtility
from zope.interface import implements

from sqlobject import ForeignKey, StringCol

from canonical.database.sqlbase import (
    flush_database_updates, SQLBase, sqlvalues)
from canonical.database.constants import UTC_NOW
from canonical.database.datetimecol import UtcDateTimeCol
from canonical.database.enumcol import EnumCol

from canonical.config import config

from canonical.launchpad.mail import format_address, simple_sendmail
from canonical.launchpad.mailnotification import MailWrapper
from canonical.launchpad.helpers import (
    contactEmailAddresses, get_email_template)
from canonical.launchpad.validators.person import validate_public_person
from canonical.launchpad.interfaces import (
    CyclicalTeamMembershipError, DAYS_BEFORE_EXPIRATION_WARNING_IS_SENT,
    ILaunchpadCelebrities, IPersonSet, ITeamMembership, ITeamMembershipSet,
    ITeamParticipation, TeamMembershipRenewalPolicy, TeamMembershipStatus)
from canonical.launchpad.webapp import canonical_url
from canonical.launchpad.webapp.tales import DurationFormatterAPI


class TeamMembership(SQLBase):
    """See `ITeamMembership`."""

    implements(ITeamMembership)

    _table = 'TeamMembership'
    _defaultOrder = 'id'

    team = ForeignKey(dbName='team', foreignKey='Person', notNull=True)
    person = ForeignKey(
        dbName='person', foreignKey='Person',
        storm_validator=validate_public_person, notNull=True)
    last_changed_by = ForeignKey(
        dbName='last_changed_by', foreignKey='Person',
        storm_validator=validate_public_person, default=None)
    proposed_by = ForeignKey(
        dbName='proposed_by', foreignKey='Person',
        storm_validator=validate_public_person, default=None)
    acknowledged_by = ForeignKey(
        dbName='acknowledged_by', foreignKey='Person',
        storm_validator=validate_public_person, default=None)
    reviewed_by = ForeignKey(
        dbName='reviewed_by', foreignKey='Person',
        storm_validator=validate_public_person, default=None)
    status = EnumCol(
        dbName='status', notNull=True, enum=TeamMembershipStatus)
    # XXX: salgado, 2008-03-06: Need to rename datejoined and dateexpires to
    # match their db names.
    datejoined = UtcDateTimeCol(dbName='date_joined', default=None)
    dateexpires = UtcDateTimeCol(dbName='date_expires', default=None)
    date_created = UtcDateTimeCol(default=UTC_NOW)
    date_proposed = UtcDateTimeCol(default=None)
    date_acknowledged = UtcDateTimeCol(default=None)
    date_reviewed = UtcDateTimeCol(default=None)
    date_last_changed = UtcDateTimeCol(default=None)
    last_change_comment = StringCol(default=None)
    proponent_comment = StringCol(default=None)
    acknowledger_comment = StringCol(default=None)
    reviewer_comment = StringCol(default=None)

    def isExpired(self):
        """See `ITeamMembership`."""
        return self.status == TeamMembershipStatus.EXPIRED

    def canBeRenewedByMember(self):
        """See `ITeamMembership`."""
        ondemand = TeamMembershipRenewalPolicy.ONDEMAND
        admin = TeamMembershipStatus.APPROVED
        approved = TeamMembershipStatus.ADMIN
        date_limit = datetime.now(pytz.timezone('UTC')) + timedelta(
            days=DAYS_BEFORE_EXPIRATION_WARNING_IS_SENT)
        return (self.status in (admin, approved)
                and self.team.renewal_policy == ondemand
                and self.dateexpires is not None
                and self.dateexpires < date_limit)

    def sendSelfRenewalNotification(self):
        """See `ITeamMembership`."""
        team = self.team
        member = self.person
        assert team.renewal_policy == TeamMembershipRenewalPolicy.ONDEMAND

        from_addr = format_address(
            team.displayname, config.canonical.noreply_from_address)
        replacements = {'member_name': member.unique_displayname,
                        'team_name': team.unique_displayname,
                        'team_url': canonical_url(team),
                        'dateexpires': self.dateexpires.strftime('%Y-%m-%d')}
        subject = '%s extended their membership' % member.name
        template = get_email_template('membership-member-renewed.txt')
        admins_addrs = self.team.getTeamAdminsEmailAddresses()
        for address in admins_addrs:
            recipient = getUtility(IPersonSet).getByEmail(address)
            replacements['recipient_name'] = recipient.displayname
            msg = MailWrapper().format(
                template % replacements, force_wrap=True)
            simple_sendmail(from_addr, address, subject, msg)

    def sendAutoRenewalNotification(self):
        """See `ITeamMembership`."""
        team = self.team
        member = self.person
        assert team.renewal_policy == TeamMembershipRenewalPolicy.AUTOMATIC

        from_addr = format_address(
            team.displayname, config.canonical.noreply_from_address)
        replacements = {'member_name': member.unique_displayname,
                        'team_name': team.unique_displayname,
                        'team_url': canonical_url(team),
                        'dateexpires': self.dateexpires.strftime('%Y-%m-%d')}
        subject = '%s renewed automatically' % member.name

        if member.isTeam():
            member_addrs = contactEmailAddresses(member.teamowner)
            template_name = 'membership-auto-renewed-bulk.txt'
        else:
            template_name = 'membership-auto-renewed-personal.txt'
            member_addrs = contactEmailAddresses(member)
        template = get_email_template(template_name)
        for address in member_addrs:
            recipient = getUtility(IPersonSet).getByEmail(address)
            replacements['recipient_name'] = recipient.displayname
            msg = MailWrapper().format(
                template % replacements, force_wrap=True)
            simple_sendmail(from_addr, address, subject, msg)

        template_name = 'membership-auto-renewed-bulk.txt'
        admins_addrs = self.team.getTeamAdminsEmailAddresses()
        admins_addrs = set(admins_addrs).difference(member_addrs)
        template = get_email_template(template_name)
        for address in admins_addrs:
            recipient = getUtility(IPersonSet).getByEmail(address)
            replacements['recipient_name'] = recipient.displayname
            msg = MailWrapper().format(
                template % replacements, force_wrap=True)
            simple_sendmail(from_addr, address, subject, msg)

    def canChangeExpirationDate(self, person):
        """See `ITeamMembership`."""
        person_is_admin = self.team in person.getAdministratedTeams()
        if (person.inTeam(self.team.teamowner) or
                person.inTeam(getUtility(ILaunchpadCelebrities).admin)):
            # The team owner and Launchpad admins can change the expiration
            # date of anybody's membership.
            return True
        elif person_is_admin and person != self.person:
            # A team admin can only change other member's expiration date.
            return True
        else:
            return False

    def setExpirationDate(self, date, user):
        """See `ITeamMembership`."""
        if date == self.dateexpires:
            return

        assert self.canChangeExpirationDate(user), (
            "This user can't change this membership's expiration date.")
        self._setExpirationDate(date, user)

    def _setExpirationDate(self, date, user):
        UTC = pytz.timezone('UTC')
        assert date is None or date.date() >= datetime.now(UTC).date(), (
            "The given expiration date must be None or be in the future: %s"
            % date.strftime('%Y-%m-%d'))
        self.dateexpires = date
        self.last_changed_by = user

    def sendExpirationWarningEmail(self):
        """See `ITeamMembership`."""
        assert self.dateexpires is not None, (
            'This membership has no expiration date')
        assert self.dateexpires > datetime.now(pytz.timezone('UTC')), (
            "This membership's expiration date must be in the future: %s"
            % self.dateexpires.strftime('%Y-%m-%d'))
        member = self.person
        team = self.team
        if member.isTeam():
            recipient = member.teamowner
            templatename = 'membership-expiration-warning-bulk.txt'
            subject = '%s will expire soon from %s' % (member.name, team.name)
        else:
            recipient = member
            templatename = 'membership-expiration-warning-personal.txt'
            subject = 'Your membership in %s is about to expire' % team.name

        if team.renewal_policy == TeamMembershipRenewalPolicy.ONDEMAND:
            how_to_renew = (
                "If you want, you can renew this membership at\n"
                "<%s/+expiringmembership/%s>"
                % (canonical_url(member), team.name))
        elif not self.canChangeExpirationDate(recipient):
            admins_names = []
            admins = team.getDirectAdministrators()
            assert admins.count() >= 1
            if admins.count() == 1:
                admin = admins[0]
                how_to_renew = (
                    "To prevent this membership from expiring, you should"
                    "contact the\nteam's administrator, %s.\n<%s>"
                    % (admin.unique_displayname, canonical_url(admin)))
            else:
                for admin in admins:
                    # Do not tell the member to contact himself when he can't
                    # extend his membership.
                    if admin != member:
                        admins_names.append(
                            "%s <%s>" % (admin.unique_displayname,
                                         canonical_url(admin)))

                how_to_renew = (
                    "To prevent this membership from expiring, you should "
                    "get in touch\nwith one of the team's administrators:\n")
                how_to_renew += "\n".join(admins_names)
        else:
            how_to_renew = (
                "To stay a member of this team you should extend your "
                "membership at\n<%s/+member/%s>"
                % (canonical_url(team), member.name))

        to_addrs = contactEmailAddresses(recipient)
        formatter = DurationFormatterAPI(
            self.dateexpires - datetime.now(pytz.timezone('UTC')))
        replacements = {
            'recipient_name': recipient.displayname,
            'member_name': member.unique_displayname,
            'team_url': canonical_url(team),
            'how_to_renew': how_to_renew,
            'team_name': team.unique_displayname,
            'expiration_date': self.dateexpires.strftime('%Y-%m-%d'),
            'approximate_duration': formatter.approximateduration()}

        msg = get_email_template(templatename) % replacements
        from_addr = format_address(
            team.displayname, config.canonical.noreply_from_address)
        simple_sendmail(from_addr, to_addrs, subject, msg)

    def setStatus(self, status, user, comment=None):
        """See `ITeamMembership`."""
        if status == self.status:
            return

        approved = TeamMembershipStatus.APPROVED
        admin = TeamMembershipStatus.ADMIN
        expired = TeamMembershipStatus.EXPIRED
        declined = TeamMembershipStatus.DECLINED
        deactivated = TeamMembershipStatus.DEACTIVATED
        proposed = TeamMembershipStatus.PROPOSED
        invited = TeamMembershipStatus.INVITED
        invitation_declined = TeamMembershipStatus.INVITATION_DECLINED

        self.person.clearInTeamCache()

        # Make sure the transition from the current status to the given one
        # is allowed. All allowed transitions are in the TeamMembership spec.
        state_transition = {
            admin: [approved, expired, deactivated],
            approved: [admin, expired, deactivated],
            deactivated: [proposed, approved, admin, invited],
            expired: [proposed, approved, admin, invited],
            proposed: [approved, admin, declined],
            declined: [proposed, approved, admin],
            invited: [approved, admin, invitation_declined],
            invitation_declined: [invited, approved, admin]}
        assert self.status in state_transition, (
            "Unknown status: %s" % self.status.name)
        assert status in state_transition[self.status], (
            "Bad state transition from %s to %s"
            % (self.status.name, status.name))

        active_states = [approved, admin]
        if status in active_states and self.team in self.person.allmembers:
            raise CyclicalTeamMembershipError(
                "Cannot make %(person)s a member of %(team)s because "
                "%(team)s is a member of %(person)s."
                % dict(person=self.person.name, team=self.team.name))


        old_status = self.status
        self.status = status

        now = datetime.now(pytz.timezone('UTC'))
        if status in [proposed, invited]:
            self.proposed_by = user
            self.proponent_comment = comment
            self.date_proposed = now
        elif ((status in active_states and old_status not in active_states)
              or status == declined):
            self.reviewed_by = user
            self.reviewer_comment = comment
            self.date_reviewed = now
            if self.datejoined is None and status in active_states:
                # This is the first time this membership is made active.
                self.datejoined = now
        else:
            # No need to set proponent or reviewer.
            pass

        if old_status == invited:
            # This member has been invited by an admin and is now accepting or
            # declining the invitation.
            self.acknowledged_by = user
            self.date_acknowledged = now
            self.acknowledger_comment = comment

        self.last_changed_by = user
        self.last_change_comment = comment
        self.date_last_changed = now

        if status in active_states:
            _fillTeamParticipation(self.person, self.team)
        elif old_status in active_states:
            # Need to flush db updates because _cleanTeamParticipation() will
            # manipulate the database directly, bypassing the ORM.
            flush_database_updates()
            _cleanTeamParticipation(self.person, self.team)
        else:
            # Changed from an inactive state to another inactive one, so no
            # need to fill/clean the TeamParticipation table.
            pass

        # Flush all updates to ensure any subsequent calls to this method on
        # the same transaction will operate on the correct data.  That is the
        # case with our script to expire team memberships.
        flush_database_updates()

        # When a member proposes himself, a more detailed notification is
        # sent to the team admins by a subscriber of JoinTeamEvent; that's
        # why we don't send anything here.
        if self.person == self.last_changed_by and self.status == proposed:
            return

        self._sendStatusChangeNotification(old_status)

    def _sendStatusChangeNotification(self, old_status):
        """Send a status change notification to all team admins and the
        member whose membership's status changed.
        """
        team = self.team
        member = self.person
        reviewer = self.last_changed_by
        from_addr = format_address(
            team.displayname, config.canonical.noreply_from_address)
        new_status = self.status
        admins_emails = team.getTeamAdminsEmailAddresses()
        # self.person might be a team, so we can't rely on its preferredemail.
        member_email = contactEmailAddresses(member)
        # Make sure we don't send the same notification twice to anybody.
        for email in member_email:
            if email in admins_emails:
                admins_emails.remove(email)

        if reviewer != member:
            reviewer_name = reviewer.unique_displayname
        else:
            # The user himself changed his membership.
            reviewer_name = 'the user himself'

        if self.last_change_comment:
            comment = ("\n%s said:\n %s\n" % (
                reviewer.displayname, self.last_change_comment.strip()))
        else:
            comment = ""

        replacements = {
            'member_name': member.unique_displayname,
            'recipient_name': member.displayname,
            'team_name': team.unique_displayname,
            'team_url': canonical_url(team),
            'old_status': old_status.title,
            'new_status': new_status.title,
            'reviewer_name': reviewer_name,
            'comment': comment}

        template_name = 'membership-statuschange'
        subject = ('Membership change: %(member)s in %(team)s'
                   % {'member': member.name, 'team': team.name})
        if new_status == TeamMembershipStatus.EXPIRED:
            template_name = 'membership-expired'
            subject = '%s expired from team' % member.name
        elif (new_status == TeamMembershipStatus.APPROVED and
              old_status != TeamMembershipStatus.ADMIN):
            if old_status == TeamMembershipStatus.INVITED:
                subject = ('Invitation to %s accepted by %s'
                           % (member.name, reviewer.name))
                template_name = 'membership-invitation-accepted'
            elif old_status == TeamMembershipStatus.PROPOSED:
                subject = '%s approved by %s' % (member.name, reviewer.name)
            else:
                subject = '%s added by %s' % (member.name, reviewer.name)
        elif new_status == TeamMembershipStatus.INVITATION_DECLINED:
            subject = ('Invitation to %s declined by %s'
                       % (member.name, reviewer.name))
            template_name = 'membership-invitation-declined'
        elif new_status == TeamMembershipStatus.DEACTIVATED:
            subject = '%s deactivated by %s' % (member.name, reviewer.name)
        elif new_status == TeamMembershipStatus.ADMIN:
            subject = '%s made admin by %s' % (member.name, reviewer.name)
        elif new_status == TeamMembershipStatus.DECLINED:
            subject = '%s declined by %s' % (member.name, reviewer.name)
        else:
            # Use the default template and subject.
            pass

        if admins_emails:
            admins_template = get_email_template(
                "%s-bulk.txt" % template_name)
            for address in admins_emails:
                recipient = getUtility(IPersonSet).getByEmail(address)
                replacements['recipient_name'] = recipient.displayname
                msg = MailWrapper().format(
                    admins_template % replacements, force_wrap=True)
                simple_sendmail(from_addr, address, subject, msg)

        # The member can be a team without any members, and in this case we
        # won't have a single email address to send this notification to.
        if member_email and reviewer != member:
            if member.isTeam():
                template = '%s-bulk.txt' % template_name
            else:
                template = '%s-personal.txt' % template_name
            member_template = get_email_template(template)
            for address in member_email:
                recipient = getUtility(IPersonSet).getByEmail(address)
                replacements['recipient_name'] = recipient.displayname
                msg = MailWrapper().format(
                    member_template % replacements, force_wrap=True)
                simple_sendmail(from_addr, address, subject, msg)


class TeamMembershipSet:
    """See `ITeamMembershipSet`."""

    implements(ITeamMembershipSet)

    _defaultOrder = ['Person.displayname', 'Person.name']

    def new(self, person, team, status, user, dateexpires=None, comment=None):
        """See `ITeamMembershipSet`."""
        proposed = TeamMembershipStatus.PROPOSED
        approved = TeamMembershipStatus.APPROVED
        admin = TeamMembershipStatus.ADMIN
        invited = TeamMembershipStatus.INVITED
        assert status in [proposed, approved, admin, invited]

        person.clearInTeamCache()

        tm = TeamMembership(
            person=person, team=team, status=status, dateexpires=dateexpires)

        now = datetime.now(pytz.timezone('UTC'))
        tm.proposed_by = user
        tm.date_proposed = now
        tm.proponent_comment = comment
        if status in [approved, admin]:
            tm.datejoined = now
            tm.reviewed_by = user
            tm.date_reviewed = now
            tm.reviewer_comment = comment
            _fillTeamParticipation(person, team)

        return tm

    def handleMembershipsExpiringToday(self, reviewer):
        """See `ITeamMembershipSet`."""
        memberships = self.getMembershipsToExpire()
        for membership in memberships:
            team = membership.team
            if team.renewal_policy == TeamMembershipRenewalPolicy.AUTOMATIC:
                # Keep the same status, change the expiration date and send a
                # notification explaining the membership has been renewed.
                assert (team.defaultrenewalperiod is not None
                        and team.defaultrenewalperiod > 0), (
                    'Teams with a renewal policy of AUTOMATIC must specify '
                    'a default renewal period greater than 0.')
                membership.dateexpires += timedelta(
                    days=team.defaultrenewalperiod)
                membership.sendAutoRenewalNotification()
            else:
                membership.setStatus(TeamMembershipStatus.EXPIRED, reviewer)

    def getByPersonAndTeam(self, person, team):
        """See `ITeamMembershipSet`."""
        return TeamMembership.selectOneBy(person=person, team=team)

    def getMembershipsToExpire(self, when=None):
        """See `ITeamMembershipSet`."""
        if when is None:
            when = datetime.now(pytz.timezone('UTC'))
        query = ("date_expires <= %s AND status IN (%s, %s)"
                 % sqlvalues(when, TeamMembershipStatus.ADMIN,
                             TeamMembershipStatus.APPROVED))
        return TeamMembership.select(query)


class TeamParticipation(SQLBase):
    implements(ITeamParticipation)

    _table = 'TeamParticipation'

    team = ForeignKey(foreignKey='Person', dbName='team', notNull=True)
    person = ForeignKey(dbName='person', foreignKey='Person', notNull=True)


def _cleanTeamParticipation(person, team):
    """Remove relevant entries in TeamParticipation for <person> and <team>.

    If the given person is not a team then we only need to remove that person
    from the given team and its super teams.

    If the person is a team, though, we will remove all its participants from
    the given team as well, but only if they're not active members of that
    team or participants through teams other than the given person.
    """
    # First of all, we remove <person> from <team> (and its superteams).
    _removeParticipantFromTeamAndSuperTeams(person, team)
    if not person.is_team:
        # Nothing else to do.
        return

    # The person is actually a team, so we must remove all its participants
    # as well.
    all_person_members = set(person.allmembers)

    # Obviously, we must not remove anybody who's a participant through our
    # person if that participant is also a direct member of the team.
    members_to_skip = set(team.activemembers)

    # We also don't want to remove somebody who's a participant through our
    # person if he's also a participant through other team.
    member_subteams = list(person.sub_teams)
    for member in team.allmembers:
        if (member.is_team and member != person
                and member not in member_subteams):
            members_to_skip.update(member.allmembers)
    to_remove = all_person_members - members_to_skip

    for person in to_remove:
        _removeParticipantFromTeamAndSuperTeams(person, team)


def _removeParticipantFromTeamAndSuperTeams(person, team):
    """Remove the given person from team and all its super teams.

    Delete the TeamParticipation entry for the given person and team, if it
    exists and then delete the TeamParticipation for that person on each super
    team of the given team, only if the person is not an active member of that
    super team or is a participant through a team other than the given one.
    """
    result = TeamParticipation.selectOneBy(person=person, team=team)
    if result is not None:
        result.destroySelf()

    for superteam in team.super_teams:
        if person not in superteam.activemembers:
            # XXX: Having just this call here will cause some tests in
            # doc/teammembership.txt to fail
            # ./test.py -vvt doc/teammembership.txt
            _removeParticipantFromTeamAndSuperTeams(person, superteam)

            # XXX: Replacing the above with this one will cause the new test
            # (in tests/test_teammembership) to fail.
            # ./test.py -vvt canonical.launchpad.tests.test_teammembership.TestTeamMembership
#             for subteam in superteam.sub_teams:
#                 if (person != subteam
#                         and person.hasParticipationEntryFor(subteam)):
#                     # This is a participant through a team other than the
#                     # given one, so we must not remove his participation entry
#                     # for that team.
#                     break
#             else:
#                 _removeParticipantFromTeamAndSuperTeams(person, superteam)


def _fillTeamParticipation(member, team):
    """Add relevant entries in TeamParticipation for given member and team.

    Add a tuple "member, team" in TeamParticipation for the given team and all
    of its superteams. More information on how to use the TeamParticipation
    table can be found in the TeamParticipationUsage spec.
    """
    members = [member]
    if member.isTeam():
        # The given member is, in fact, a team, and in this case we must
        # add all of its members to the given team and to its superteams.
        members.extend(member.allmembers)

    for m in members:
        for t in itertools.chain(team.super_teams, [team]):
            if not m.hasParticipationEntryFor(t):
                TeamParticipation(person=m, team=t)
