# Copyright 2008 Canonical Ltd.  All rights reserved.

"""Resources having to do with Launchpad team memberships."""

__metaclass__ = type
__all__ = [
    'ITeamMembershipEntry',
    'TeamMembershipEntry',
    'PersonTeamMembershipCollection'
    ]

from zope.component import adapts
from zope.schema import Object, Text

from canonical.lazr import decorates
from canonical.lazr.rest import Entry, ScopedCollection
from canonical.lazr.interfaces import IEntry

from canonical.launchpad.interfaces import (IPerson, ITeamMembership)

class ITeamMembershipEntry(IEntry):
    """The part of a team membership exposed through the web service."""

    # XXX leonardr 2008-01-28 bug=186702 A much better solution would
    # let us reuse or copy fields from IPerson.
    team = Object(schema=IPerson)
    member = Object(schema=IPerson)
    reviewer = Object(schema=IPerson)

    date_joined = Text(title=u"Date Joined", required=True, readonly=True)
    date_expires = Text(title=u"Date Expires", required=False, readonly=False)
    reviewer_comment = Text(title=u"Reviewer Comment", required=False,
                           readonly=False)
    status = Text(title=u"Status of the membership", required=True)


class TeamMembershipEntry(Entry):
    """A proposed or actual membership in a team."""
    adapts(ITeamMembership)
    decorates(ITeamMembershipEntry)
    schema = ITeamMembershipEntry

    parent_collection_path = ['people', lambda tm: tm.member,
                              'team_memberships']

    @property
    def member(self):
        """See `ITeamMembershipEntry`."""
        return self.context.person

    @property
    def date_joined(self):
        """See `ITeamMembershipEntry`."""
        return self.context.datejoined

    @property
    def date_expires(self):
        """See `ITeamMembershipEntry`."""
        return self.context.dateexpires

    @property
    def reviewer_comment(self):
        """See `ITeamMembershipEntry`."""
        return self.context.reviewercomment


class PersonTeamMembershipCollection(ScopedCollection):
    """A collection of team memberships for a person.

    There will be one membership for each team of which the person is
    a member.
    """

    def getEntryPath(self, entry):
        """See `ICollection`."""
        return entry.team.name

    def lookupEntry(self, name):
        """Find a membership by team name."""
        for membership in self.collection:
            if membership.team.name == name:
                return membership
        else:
            return None
