# Copyright 2008 Canonical Ltd.  All rights reserved.
# pylint: disable-msg=E0213

"""Interface for branch containers."""

__metaclass__ = type
__all__ = [
    'IBranchContainer',
    ]

from zope.interface import Interface, Attribute


class IBranchContainer(Interface):
    """A container of branches.

    A product contains branches, a source package on a distroseries contains
    branches, and a person contains 'junk' branches.
    """

    name = Attribute("The name of the container.")

    def getNamespace(owner):
        """Return a namespace for this container and the specified owner."""
