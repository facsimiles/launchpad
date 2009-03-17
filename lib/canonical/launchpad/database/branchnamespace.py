# Copyright 2008 Canonical Ltd.  All rights reserved.

"""Implementations of `IBranchNamespace`."""

__metaclass__ = type
__all__ = [
    'BranchNamespaceSet',
    'get_namespace',
    'PackageNamespace',
    'PersonalNamespace',
    'ProductNamespace',
    ]


from zope.component import getUtility
from zope.event import notify
from zope.interface import implements
from zope.security.interfaces import Unauthorized

from lazr.lifecycle.event import ObjectCreatedEvent
from storm.locals import And

from canonical.config import config
from canonical.database.constants import UTC_NOW
from canonical.launchpad.database import Branch
from canonical.launchpad.database.sourcepackage import SourcePackage
from canonical.launchpad.interfaces.branch import (
    BranchCreationForbidden, BranchCreatorNotMemberOfOwnerTeam,
    BranchCreatorNotOwner, BranchExists, BranchLifecycleStatus,
    BranchMergeControlStatus, IBranch, NoSuchBranch)
from canonical.launchpad.interfaces.branchnamespace import (
    IBranchNamespace, InvalidNamespace)
from canonical.launchpad.interfaces.branchsubscription import (
    BranchSubscriptionDiffSize, BranchSubscriptionNotificationLevel,
    CodeReviewNotificationLevel)
from canonical.launchpad.interfaces.branchtarget import IBranchTarget
from canonical.launchpad.interfaces.branchvisibilitypolicy import (
    BranchVisibilityRule)
from canonical.launchpad.interfaces.distribution import (
    IDistributionSet, NoSuchDistribution)
from canonical.launchpad.interfaces.distroseries import (
    IDistroSeriesSet, NoSuchDistroSeries)
from canonical.launchpad.interfaces.person import IPersonSet, NoSuchPerson
from canonical.launchpad.interfaces.pillar import IPillarNameSet
from canonical.launchpad.interfaces.project import IProject
from canonical.launchpad.interfaces.product import (
    IProduct, IProductSet, NoSuchProduct)
from canonical.launchpad.interfaces.sourcepackagename import (
    ISourcePackageNameSet, NoSuchSourcePackageName)
from canonical.launchpad.webapp.interfaces import (
    IStoreSelector, MAIN_STORE, DEFAULT_FLAVOR)
from canonical.launchpad.xmlrpc.codehosting import iter_split


class _BaseNamespace:
    """Common code for branch namespaces."""

    def createBranch(self, branch_type, name, registrant, url=None,
                     title=None,
                     lifecycle_status=BranchLifecycleStatus.DEVELOPMENT,
                     summary=None, whiteboard=None, date_created=None,
                     branch_format=None, repository_format=None,
                     control_format=None,
                     merge_control_status=BranchMergeControlStatus.NO_QUEUE):
        """See `IBranchNamespace`."""
        owner = self.owner
        if not registrant.inTeam(owner):
            if owner.isTeam():
                raise BranchCreatorNotMemberOfOwnerTeam(
                    "%s is not a member of %s"
                    % (registrant.displayname, owner.displayname))
            else:
                raise BranchCreatorNotOwner(
                    "%s cannot create branches owned by %s"
                    % (registrant.displayname, owner.displayname))

        target = self._target()
        if not target.canCreateBranches(registrant):
            raise BranchCreationForbidden(
                "You cannot create branches for %r"% target.name)

        existing_branch = self.getByName(name)
        if existing_branch is not None:
            raise BranchExists(existing_branch)

        private = target.areNewBranchesPrivate(registrant)

        if date_created is None:
            date_created = UTC_NOW

        # Not all code paths that lead to branch creation go via a
        # schema-validated form (e.g. the register_branch XML-RPC call or
        # pushing a new branch to codehosting), so we validate the branch name
        # here to give a nicer error message than 'ERROR: new row for relation
        # "branch" violates check constraint "valid_name"...'.
        IBranch['name'].validate(unicode(name))

        # Run any necessary data massage on the branch URL.
        if url is not None:
            url = IBranch['url'].normalize(url)

        product = getattr(self, 'product', None)
        sourcepackage = getattr(self, 'sourcepackage', None)
        if sourcepackage is None:
            distroseries = None
            sourcepackagename = None
        else:
            distroseries = sourcepackage.distroseries
            sourcepackagename = sourcepackage.sourcepackagename

        branch = Branch(
            registrant=registrant,
            name=name, owner=owner, product=product, url=url,
            title=title, lifecycle_status=lifecycle_status, summary=summary,
            whiteboard=whiteboard, private=private,
            date_created=date_created, branch_type=branch_type,
            date_last_modified=date_created, branch_format=branch_format,
            repository_format=repository_format,
            control_format=control_format, distroseries=distroseries,
            sourcepackagename=sourcepackagename,
            merge_control_status=merge_control_status)

        # Implicit subscriptions are to enable teams to see private branches
        # as soon as they are created.  The subscriptions can be edited at
        # a later date if desired.
        implicit_subscription = self.getPrivacySubscriber()
        if implicit_subscription is not None:
            branch.subscribe(
                implicit_subscription,
                BranchSubscriptionNotificationLevel.NOEMAIL,
                BranchSubscriptionDiffSize.NODIFF,
                CodeReviewNotificationLevel.NOEMAIL)

        # The registrant of the branch should also be automatically subscribed
        # in order for them to get code review notifications.  The implicit
        # registrant subscription does not cause email to be sent about
        # attribute changes, just merge proposals and code review comments.
        branch.subscribe(
            registrant,
            BranchSubscriptionNotificationLevel.NOEMAIL,
            BranchSubscriptionDiffSize.NODIFF,
            CodeReviewNotificationLevel.FULL)

        notify(ObjectCreatedEvent(branch))
        return branch

    def _target(self):
        """Return the BranchTarget for this namespace."""
        raise NotImplemented(self._target)

    def createBranchWithPrefix(self, branch_type, prefix, registrant,
                               url=None):
        """See `IBranchNamespace`."""
        name = self.findUnusedName(prefix)
        return self.createBranch(branch_type, name, registrant, url=url)

    def findUnusedName(self, prefix):
        """See `IBranchNamespace`."""
        name = prefix
        count = 0
        while self.isNameUsed(name):
            count += 1
            name = "%s-%s" % (prefix, count)
        return name

    def getBranches(self):
        """See `IBranchNamespace`."""
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        return store.find(Branch, self._getBranchesClause())

    def getBranchName(self, branch_name):
        """See `IBranchNamespace`."""
        return '%s/%s' % (self.name, branch_name)

    def getByName(self, branch_name, default=None):
        """See `IBranchNamespace`."""
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        match = store.find(
            Branch, self._getBranchesClause(),
            Branch.name == branch_name).one()
        if match is None:
            match = default
        return match

    def isNameUsed(self, branch_name):
        return self.getByName(branch_name) is not None

    def canCreateBranches(self, user):
        """See `IBranchNamespace`."""
        return user.inTeam(self.owner)

    def areNewBranchesPrivate(self):
        """See `IBranchNamespace`."""
        return False

    def getPrivacySubscriber(self):
        """See `IBranchNamespace`."""
        return None


class PersonalNamespace(_BaseNamespace):
    """A namespace for personal (or 'junk') branches.

    Branches in this namespace have names like '~foo/+junk/bar'.
    """

    implements(IBranchNamespace)

    def __init__(self, person):
        self.owner = person

    def _getBranchesClause(self):
        return And(
            Branch.owner == self.owner, Branch.product == None,
            Branch.distroseries == None, Branch.sourcepackagename == None)

    @property
    def name(self):
        """See `IBranchNamespace`."""
        return '~%s/+junk' % (self.owner.name,)

    def _target(self):
        """Return the BranchTarget for this namespace."""
        return IBranchTarget(self.owner)


class ProductNamespace(_BaseNamespace):
    """A namespace for product branches.

    This namespace is for all the branches owned by a particular person in a
    particular product.
    """

    implements(IBranchNamespace)

    def __init__(self, person, product):
        self.owner = person
        self.product = product

    def _getBranchesClause(self):
        return And(Branch.owner == self.owner, Branch.product == self.product)

    @property
    def name(self):
        """See `IBranchNamespace`."""
        return '~%s/%s' % (self.owner.name, self.product.name)

    def _target(self):
        """Return the BranchTarget for this namespace."""
        return IBranchTarget(self.product)

    def getPrivacySubscriber(self):
        """See `IBranchNamespace`."""
        # If there is a rule defined for the owner, then there is no privacy
        # subscriber.
        rule = self.product.getBranchVisibilityRuleForTeam(self.owner)
        if rule is not None:
            return None
        policies = self.product.getBranchVisibilityTeamPolicies()
        private = (
            BranchVisibilityRule.PRIVATE,
            BranchVisibilityRule.PRIVATE_ONLY)
        subscriber = None
        for policy in policies:
            if self.owner.inTeam(policy.team) and policy.rule in private:
                # If we haven't found a private rule yet, remember the team.
                if subscriber is None:
                    subscriber = policy.team
                else:
                    # If we have a subscriber already, we have just found a
                    # second team that the owner is in, so there is no privacy
                    # subscriber.
                    return None
        return subscriber

    def canCreateBranches(self, user):
        """See `IBranchNamespace`."""
        if not _BaseNamespace.canCreateBranches(self, user):
            return False

        policies = self.product.getBranchVisibilityTeamPolicies()
        for policy in policies:
            if user.inTeam(policy.team):
                return True
        base_rule = self.product.getBaseBranchVisibilityRule()
        return base_rule == BranchVisibilityRule.PUBLIC

    def areNewBranchesPrivate(self):
        """See `IBranchNamespace`."""
        # If there is a rule for the namespace owner, use that.
        private = (
            BranchVisibilityRule.PRIVATE,
            BranchVisibilityRule.PRIVATE_ONLY)
        rule = self.product.getBranchVisibilityRuleForTeam(self.owner)
        if rule is not None:
            return rule in private
        # If the owner is a member of any team that has a PRIVATE or
        # PRIVATE_ONLY rule, then the branches are private.
        policies = self.product.getBranchVisibilityTeamPolicies()
        for policy in policies:
            if self.owner.inTeam(policy.team) and policy.rule in private:
                return True
        return False


class PackageNamespace(_BaseNamespace):
    """A namespace for source package branches.

    This namespace is for all the branches owned by a particular person in a
    particular source package in a particular distroseries.
    """

    implements(IBranchNamespace)

    def __init__(self, person, sourcepackage):
        if not config.codehosting.package_branches_enabled:
            raise Unauthorized("Package branches are disabled.")
        self.owner = person
        self.sourcepackage = sourcepackage

    def _getBranchesClause(self):
        return And(
            Branch.owner == self.owner,
            Branch.distroseries == self.sourcepackage.distroseries,
            Branch.sourcepackagename == self.sourcepackage.sourcepackagename)

    @property
    def name(self):
        """See `IBranchNamespace`."""
        return '~%s/%s' % (self.owner.name, self.sourcepackage.path)

    def _target(self):
        """Return the BranchTarget for this namespace."""
        return IBranchTarget(self.sourcepackage)


class BranchNamespaceSet:
    """Only implementation of `IBranchNamespaceSet`."""

    def get(self, person, product=None, distroseries=None,
            sourcepackagename=None):
        """See `IBranchNamespaceSet`."""
        if product is not None:
            assert (distroseries is None and sourcepackagename is None), (
                "product implies no distroseries or sourcepackagename. "
                "Got %r, %r, %r."
                % (product, distroseries, sourcepackagename))
            return ProductNamespace(person, product)
        elif distroseries is not None:
            assert sourcepackagename is not None, (
                "distroseries implies sourcepackagename. Got %r, %r"
                % (distroseries, sourcepackagename))
            return PackageNamespace(
                person, SourcePackage(sourcepackagename, distroseries))
        else:
            return PersonalNamespace(person)

    def parse(self, namespace_name):
        """See `IBranchNamespaceSet`."""
        data = dict(
            person=None, product=None, distribution=None, distroseries=None,
            sourcepackagename=None)
        tokens = namespace_name.split('/')
        if len(tokens) == 2:
            data['person'] = tokens[0]
            data['product'] = tokens[1]
        elif len(tokens) == 4:
            data['person'] = tokens[0]
            data['distribution'] = tokens[1]
            data['distroseries'] = tokens[2]
            data['sourcepackagename'] = tokens[3]
        else:
            raise InvalidNamespace(namespace_name)
        if not data['person'].startswith('~'):
            raise InvalidNamespace(namespace_name)
        data['person'] = data['person'][1:]
        return data

    def parseBranchPath(self, namespace_path):
        """See `IBranchNamespaceSet`."""
        found = False
        for branch_path, trailing_path in iter_split(namespace_path, '/'):
            try:
                branch_path, branch = branch_path.rsplit('/', 1)
            except ValueError:
                continue
            try:
                parsed = self.parse(branch_path)
            except InvalidNamespace:
                continue
            else:
                found = True
                yield parsed, branch, trailing_path
        if not found:
            raise InvalidNamespace(namespace_path)

    def lookup(self, namespace_name):
        """See `IBranchNamespaceSet`."""
        names = self.parse(namespace_name)
        return self.interpret(**names)

    def interpret(self, person=None, product=None, distribution=None,
                  distroseries=None, sourcepackagename=None):
        """See `IBranchNamespaceSet`."""
        names = dict(
            person=person, product=product, distribution=distribution,
            distroseries=distroseries, sourcepackagename=sourcepackagename)
        data = self._realize(names)
        return self.get(**data)

    def traverse(self, segments):
        """See `IBranchNamespaceSet`."""
        traversed_segments = []
        def get_next_segment():
            try:
                result = segments.next()
            except StopIteration:
                raise InvalidNamespace('/'.join(traversed_segments))
            if result is None:
                raise AssertionError("None segment passed to traverse()")
            traversed_segments.append(result)
            return result
        person_name = get_next_segment()
        person = self._findPerson(person_name)
        pillar_name = get_next_segment()
        pillar = self._findPillar(pillar_name)
        if pillar is None or IProduct.providedBy(pillar):
            namespace = self.get(person, product=pillar)
        else:
            distroseries_name = get_next_segment()
            distroseries = self._findDistroSeries(pillar, distroseries_name)
            sourcepackagename_name = get_next_segment()
            sourcepackagename = self._findSourcePackageName(
                sourcepackagename_name)
            namespace = self.get(
                person, distroseries=distroseries,
                sourcepackagename=sourcepackagename)
        branch_name = get_next_segment()
        return self._findOrRaise(
            NoSuchBranch, branch_name, namespace.getByName)

    def _findOrRaise(self, error, name, finder, *args):
        if name is None:
            return None
        args = list(args)
        args.append(name)
        result = finder(*args)
        if result is None:
            raise error(name)
        return result

    def _findPerson(self, person_name):
        return self._findOrRaise(
            NoSuchPerson, person_name, getUtility(IPersonSet).getByName)

    def _findPillar(self, pillar_name):
        """Find and return the pillar with the given name.

        If the given name is '+junk' or None, return None.

        :raise NoSuchProduct if there's no pillar with the given name or it is
            a project.
        """
        if pillar_name == '+junk':
            return None
        pillar = self._findOrRaise(
            NoSuchProduct, pillar_name, getUtility(IPillarNameSet).getByName)
        if IProject.providedBy(pillar):
            raise NoSuchProduct(pillar_name)
        return pillar

    def _findProduct(self, product_name):
        if product_name == '+junk':
            return None
        return self._findOrRaise(
            NoSuchProduct, product_name,
            getUtility(IProductSet).getByName)

    def _findDistribution(self, distribution_name):
        return self._findOrRaise(
            NoSuchDistribution, distribution_name,
            getUtility(IDistributionSet).getByName)

    def _findDistroSeries(self, distribution, distroseries_name):
        return self._findOrRaise(
            NoSuchDistroSeries, distroseries_name,
            getUtility(IDistroSeriesSet).queryByName, distribution)

    def _findSourcePackageName(self, sourcepackagename_name):
        return self._findOrRaise(
            NoSuchSourcePackageName, sourcepackagename_name,
            getUtility(ISourcePackageNameSet).queryByName)

    def _realize(self, names):
        """Turn a dict of object names into a dict of objects.

        Takes the results of `IBranchNamespaceSet.parse` and turns them into a
        dict where the values are Launchpad objects.
        """
        data = {}
        data['person'] = self._findPerson(names['person'])
        data['product'] = self._findProduct(names['product'])
        distribution = self._findDistribution(names['distribution'])
        data['distroseries'] = self._findDistroSeries(
            distribution, names['distroseries'])
        data['sourcepackagename'] = self._findSourcePackageName(
            names['sourcepackagename'])
        return data
