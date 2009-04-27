# Copyright 2008, 2009 Canonical Ltd.  All rights reserved.

"""Branch targets."""

__metaclass__ = type
__all__ = [
    'branch_to_target',
    'PackageBranchTarget',
    'PersonBranchTarget',
    'ProductBranchTarget',
    ]

from zope.component import getUtility
from zope.interface import implements
from zope.security.interfaces import Unauthorized

from lp.code.interfaces.branch import BranchType
from lp.code.interfaces.branchtarget import IBranchTarget
from canonical.launchpad.interfaces.publishing import PackagePublishingPocket
from canonical.launchpad.webapp.interfaces import ICanonicalUrlData


def branch_to_target(branch):
    """Adapt an IBranch to an IBranchTarget."""
    return branch.target


def check_default_stacked_on(branch):
    """Return 'branch' if suitable to be a default stacked-on branch.

    Only certain branches are suitable to be default stacked-on branches.
    Branches that are *not* suitable include:
      - remote branches
      - branches the user cannot see
      - branches that have not yet been successfully processed by the puller.

    If the given branch is not suitable, return None. For convenience, also
    returns None if passed None. Otherwise, return the branch.
    """
    if branch is None:
        return None
    try:
        branch_type = branch.branch_type
    except Unauthorized:
        return None
    if branch_type == BranchType.REMOTE:
        return None
    if branch.last_mirrored is None:
        return None
    return branch


class _BaseBranchTarget:

    def __eq__(self, other):
        return self.context == other.context

    def __ne__(self, other):
        return self.context != other.context


class PackageBranchTarget(_BaseBranchTarget):
    implements(IBranchTarget)

    def __init__(self, sourcepackage):
        self.sourcepackage = sourcepackage

    @property
    def name(self):
        """See `IBranchTarget`."""
        return self.sourcepackage.path

    @property
    def components(self):
        """See `IBranchTarget`."""
        return [
            self.sourcepackage.distribution,
            self.sourcepackage.distroseries,
            self.sourcepackage,
            ]

    @property
    def context(self):
        """See `IBranchTarget`."""
        return self.sourcepackage

    def getNamespace(self, owner):
        """See `IBranchTarget`."""
        from lp.code.model.branchnamespace import (
            PackageNamespace)
        return PackageNamespace(owner, self.sourcepackage)

    def getCollection(self):
        """See `IBranchTarget`."""
        from lp.code.interfaces.branchcollection import IAllBranches
        return getUtility(IAllBranches).inSourcePackage(self.sourcepackage)

    @property
    def default_stacked_on_branch(self):
        """See `IBranchTarget`."""
        return check_default_stacked_on(
            self.sourcepackage.development_version.getBranch(
                PackagePublishingPocket.RELEASE))

    @property
    def displayname(self):
        """See `IBranchTarget`."""
        return self.sourcepackage.displayname


class PersonBranchTarget(_BaseBranchTarget):
    implements(IBranchTarget)

    name = '+junk'
    default_stacked_on_branch = None

    def __init__(self, person):
        self.person = person

    @property
    def components(self):
        """See `IBranchTarget`."""
        return [self.person]

    @property
    def context(self):
        """See `IBranchTarget`."""
        return self.person

    @property
    def displayname(self):
        """See `IBranchTarget`."""
        return "~%s/+junk" % self.person.name

    def getNamespace(self, owner):
        """See `IBranchTarget`."""
        from lp.code.model.branchnamespace import (
            PersonalNamespace)
        return PersonalNamespace(owner)

    def getCollection(self):
        """See `IBranchTarget`."""
        from lp.code.interfaces.branchcollection import IAllBranches
        return getUtility(IAllBranches).inPerson(self.person)


class ProductBranchTarget(_BaseBranchTarget):
    implements(IBranchTarget)

    def __init__(self, product):
        self.product = product

    @property
    def components(self):
        """See `IBranchTarget`."""
        return [self.product]

    @property
    def context(self):
        """See `IBranchTarget`."""
        return self.product

    @property
    def displayname(self):
        """See `IBranchTarget`."""
        return self.product.displayname

    @property
    def name(self):
        """See `IBranchTarget`."""
        return self.product.name

    @property
    def default_stacked_on_branch(self):
        """See `IBranchTarget`."""
        return check_default_stacked_on(self.product.development_focus.branch)

    def getNamespace(self, owner):
        """See `IBranchTarget`."""
        from lp.code.model.branchnamespace import (
            ProductNamespace)
        return ProductNamespace(owner, self.product)

    def getCollection(self):
        """See `IBranchTarget`."""
        from lp.code.interfaces.branchcollection import IAllBranches
        return getUtility(IAllBranches).inProduct(self.product)


def get_canonical_url_data_for_target(branch_target):
    """Return the `ICanonicalUrlData` for an `IBranchTarget`."""
    return ICanonicalUrlData(branch_target.context)
