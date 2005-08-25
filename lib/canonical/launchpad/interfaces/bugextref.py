# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""External bug reference interfaces."""

__metaclass__ = type

__all__ = [
    'IBugExternalRef',
    'IBugExternalRefSet',
    ]

from zope.i18nmessageid import MessageIDFactory
from zope.interface import Interface, Attribute
from zope.schema import Datetime, Int, TextLine

from canonical.launchpad.fields import Title

_ = MessageIDFactory('launchpad')

class IBugExternalRef(Interface):
    """An external reference for a bug, not supported remote bug systems."""

    id = Int(
            title=_('ID'), required=True, readonly=True
            )
    bug = Int(
            title=_('Bug ID'), required=True, readonly=True,
            )
    url = TextLine(
            title=_('URL'), required=True, readonly=False,
            description = _("""The url of the content that is related to
            this bug.""")
            )
    title = Title(
            title=_('Title'), required=True, readonly=False,
            description=_("""A brief description of the content that is
            being linked to.""")
            )
    datecreated = Datetime(
            title=_('Date Created'), required=True, readonly=True,
            )
    owner = Int(
            title=_('Owner'), required=False, readonly=True,
            )


class IBugExternalRefSet(Interface):
    """A set for IBugExternalRef objects."""

    bug = Int(title=_("Bug id"), readonly=True)

    title = Attribute('Title')

    def __getitem__(key):
        """Get a BugExternalRef."""

    def __iter__():
        """Iterate through BugExternalRefs for a given bug."""

    def createBugExternalRef(bug, url, title, owner):
        """Create and link an external web link to an IBug.

        Returns the IBugExternalRef that's created.
        """
