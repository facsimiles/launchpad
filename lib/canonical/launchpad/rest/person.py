# Copyright 2008 Canonical Ltd.  All rights reserved.

"""Resources having to do with Launchpad people."""

__metaclass__ = type
__all__ = [
    'PersonEntry',
    'PersonCollection',
    ]


from zope.component import adapts
from canonical.lazr.rest import Collection, Entry
from canonical.launchpad.interfaces import IPerson, IPersonEntry
from canonical.lp import decorates


class PersonEntry(Entry):
    """A person."""
    adapts(IPerson)
    decorates(IPersonEntry)
    schema = IPersonEntry


class PersonCollection(Collection):
    """A collection of people."""

    def find(self):
        """Return all the people on the site."""
        return self.context.getAllValidPersons()
