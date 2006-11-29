# Copyright 2006 Canonical Ltd.  All rights reserved.

"""Launchpad Pillars share a namespace.

Pillars are currently Product, Project and Distribution.
"""

__metaclass__ = type

from zope.component import getUtility
from zope.interface import Interface

from canonical.config import config
from canonical.launchpad import _
from canonical.launchpad.fields import BlacklistableContentNameField
from canonical.launchpad.interfaces import NotFoundError


__all__ = ['IPillarSet', 'PillarNameField']


class IPillarSet(Interface):
    def __contains__(name):
        """Return True if the given name is a Pillar."""

    def __getitem__(name):
        """Get a pillar by its name."""

    def search(text, limit=config.launchpad.default_batch_size):
        """Return at most limit+1 Products/Projects/Distros matching :text:.

        The return value is a sequence of tuples, where each tuple
        contain the name of the object it represents (one of 'product',
        'project' or 'distribution'), that object's id, name, title,
        description and the rank of that object on this specific search, in
        this specific order.

        The results are ordered descending by rank.
        """


class PillarNameField(BlacklistableContentNameField):

    errormessage = _(
            "%s is already in use by another product, project or distribution"
            )

    def _getByName(self, name):
        pillar_set = getUtility(IPillarSet)
        try:
            return pillar_set[name]
        except NotFoundError:
            return None

