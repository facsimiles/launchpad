# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Tests for branch listing."""

__metaclass__ = type

from datetime import timedelta
from pprint import pformat
import unittest

from storm.expr import Asc, Desc
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.code.browser.branchlisting import (
    BranchListingBatchNavigator, BranchListingSort, BranchListingView,
    GroupedDistributionSourcePackageBranchesView, PersonOwnedBranchesView,
    SourcePackageBranchesView)
from lp.code.interfaces.seriessourcepackagebranch import (
    IMakeOfficialBranchLinks)
from lp.code.model.branch import Branch
from lp.registry.model.person import Owner
from lp.registry.model.product import Product
from lp.soyuz.interfaces.publishing import PackagePublishingPocket
from lp.testing import TestCase, TestCaseWithFactory, time_counter
from canonical.launchpad.webapp.servers import LaunchpadTestRequest
from canonical.testing.layers import DatabaseFunctionalLayer


class TestListingToSortOrder(TestCase):
    """Tests for the BranchSet._listingSortToOrderBy static method.

    This method translates values from the BranchListingSort enumeration into
    values suitable to pass to orderBy in queries against BranchWithSortKeys.
    """

    DEFAULT_BRANCH_LISTING_SORT = [
        Asc(Product.name),
        Desc(Branch.lifecycle_status),
        Asc(Owner.name),
        Asc(Branch.name),
        ]

    def assertColumnNotReferenced(self, column, order_by_list):
        """Ensure that column is not referenced in any way in order_by_list.
        """
        self.failIf(column in order_by_list or
                    ('-' + column) in order_by_list)

    def assertSortsEqual(self, sort_one, sort_two):
        """Assert that one list of sort specs is equal to another."""
        def sort_data(sort):
            return sort.suffix, sort.expr
        self.assertEqual(map(sort_data, sort_one), map(sort_data, sort_two))

    def test_default(self):
        """Test that passing None results in the default list."""
        self.assertSortsEqual(
            self.DEFAULT_BRANCH_LISTING_SORT,
            BranchListingView._listingSortToOrderBy(None))

    def test_lifecycle(self):
        """Test with an option that's part of the default sort.

        Sorting on LIFECYCYLE moves the lifecycle reference to the
        first element of the output."""
        # Check that this isn't a no-op.
        lifecycle_order = BranchListingView._listingSortToOrderBy(
            BranchListingSort.LIFECYCLE)
        self.assertSortsEqual(
            [Desc(Branch.lifecycle_status),
             Asc(Product.name),
             Asc(Owner.name),
             Asc(Branch.name)], lifecycle_order)

    def test_sortOnColumNotInDefaultSortOrder(self):
        """Test with an option that's not part of the default sort.

        This should put the passed option first in the list, but leave
        the rest the same.
        """
        registrant_order = BranchListingView._listingSortToOrderBy(
            BranchListingSort.OLDEST_FIRST)
        self.assertSortsEqual(
            [Asc(Branch.date_created)] + self.DEFAULT_BRANCH_LISTING_SORT,
            registrant_order)


class TestPersonOwnedBranchesView(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.barney = self.factory.makePerson(name='barney')
        self.bambam = self.factory.makeProduct(name='bambam')

        time_gen = time_counter(delta=timedelta(days=-1))
        self.branches = [
            self.factory.makeProductBranch(
                product=self.bambam, owner=self.barney,
                date_created=time_gen.next())
            for i in range(5)]

    def _createView(self):
        '''Create the view and initialize it.'''
        view = PersonOwnedBranchesView(self.barney, LaunchpadTestRequest())
        view.initialize()
        return view

    def test_branch_sparks(self):
        # branch_sparks should return a simplejson list for the branches with
        # the value being [id, url]
        branch_sparks = ('['
        '["b-1", "http://code.launchpad.dev/~barney/bambam/branch9/+spark"], '
        '["b-2", "http://code.launchpad.dev/~barney/bambam/branch10/+spark"], '
        '["b-3", "http://code.launchpad.dev/~barney/bambam/branch11/+spark"], '
        '["b-4", "http://code.launchpad.dev/~barney/bambam/branch12/+spark"], '
        '["b-5", "http://code.launchpad.dev/~barney/bambam/branch13/+spark"]'
        ']')

        view = self._createView()
        self.assertEqual(view.branches().branch_sparks, branch_sparks)

    def test_branch_ids_with_bug_links(self):
        # _branches_for_current_batch should return a list of all branches in
        # the current batch.
        branch_ids = set([])

        view = self._createView()
        self.assertEqual(
            view.branches().branch_ids_with_bug_links,
            branch_ids)

    def test_branch_ids_with_spec_links(self):
        # _branches_for_current_batch should return a list of all branches in
        # the current batch.
        branch_ids = set([])

        view = self._createView()
        self.assertEqual(
            view.branches().branch_ids_with_spec_links,
            branch_ids)

    def test_branch_ids_with_merge_propoasls(self):
        # _branches_for_current_batch should return a list of all branches in
        # the current batch.
        branch_ids = set([])
        view = self._createView()
        self.assertEqual(
            view.branches().branch_ids_with_merge_proposals,
            branch_ids)

    def test_tip_revisions(self):
        # _branches_for_current_batch should return a list of all branches in
        # the current batch.
        tip_revisions = {80: None, 81: None, 77: None, 78: None, 79: None}

        view = self._createView()
        self.assertEqual(
            view.branches().tip_revisions,
            tip_revisions)


class TestSourcePackageBranchesView(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_distroseries_links(self):
        # There are some links at the bottom of the page to other
        # distroseries.
        distro = self.factory.makeDistribution()
        sourcepackagename = self.factory.makeSourcePackageName()
        packages = {}
        for version in ("1.0", "2.0", "3.0"):
            series = self.factory.makeDistroRelease(
                distribution=distro, version=version)
            package = self.factory.makeSourcePackage(
                distroseries=series, sourcepackagename=sourcepackagename)
            packages[version] = package
        request = LaunchpadTestRequest()
        view = SourcePackageBranchesView(packages["2.0"], request)
        self.assertEqual(
            [dict(series_name=packages["3.0"].distroseries.displayname,
                  package=packages["3.0"], linked=True,
                  num_branches='0 branches',
                  dev_focus_css='sourcepackage-dev-focus',
                  ),
             dict(series_name=packages["2.0"].distroseries.displayname,
                  package=packages["2.0"], linked=False,
                  num_branches='0 branches',
                  dev_focus_css='sourcepackage-not-dev-focus',
                  ),
             dict(series_name=packages["1.0"].distroseries.displayname,
                  package=packages["1.0"], linked=True,
                  num_branches='0 branches',
                  dev_focus_css='sourcepackage-not-dev-focus',
                  ),
             ],
            list(view.series_links))


class TestGroupedDistributionSourcePackageBranchesView(TestCaseWithFactory):
    """Test the groups for the branches of distribution source packages."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        # Make a distro with some series, a source package name, and a distro
        # source package.
        self.distro = self.factory.makeDistribution()
        for version in ("1.0", "2.0", "3.0"):
            self.factory.makeDistroRelease(
                distribution=self.distro, version=version)
        self.sourcepackagename = self.factory.makeSourcePackageName()
        self.distro_source_package = (
            self.factory.makeDistributionSourcePackage(
                distribution=self.distro,
                sourcepackagename=self.sourcepackagename))

    def test_groups_with_no_branches(self):
        # If there are no branches for a series, the groups are not there.
        view = GroupedDistributionSourcePackageBranchesView(
            self.distro_source_package, LaunchpadTestRequest())
        self.assertEqual([], view.groups)

    def makeBranches(self, branch_count, official_count=0):
        """Make some package branches.

        Make `branch_count` branches, and make `official_count` of those
        official branches.
        """
        distroseries = self.distro.serieses[0]
        # Make the branches created in the past in order.
        time_gen = time_counter(delta=timedelta(days=-1))
        branches = [
            self.factory.makePackageBranch(
                distroseries=distroseries,
                sourcepackagename=self.sourcepackagename,
                date_created=time_gen.next())
            for i in range(branch_count)]

        official = []
        # We don't care about who can make things official, so get rid of the
        # security proxy.
        series_set = removeSecurityProxy(getUtility(IMakeOfficialBranchLinks))
        # Sort the pocket items so RELEASE is last, and thus first popped.
        pockets = sorted(PackagePublishingPocket.items, reverse=True)
        for i in range(official_count):
            branch = branches.pop()
            pocket = pockets.pop()
            sspb = series_set.new(
                distroseries, pocket, self.sourcepackagename,
                branch, branch.owner)
            official.append(branch)

        return distroseries, branches, official

    def assertMoreBranchCount(self, expected, series):
        """Check that the more-branch-count is the expected value."""
        view = GroupedDistributionSourcePackageBranchesView(
            self.distro_source_package, LaunchpadTestRequest())
        series_group = view.groups[0]
        self.assertEqual(expected, series_group['more-branch-count'])

    def test_more_branch_count_zero(self):
        # If there are less than six branches, the more-branch-count is zero.
        series, ignored, ignored = self.makeBranches(5)
        self.assertMoreBranchCount(0, series)

    def test_more_branch_count_nonzero(self):
        # If there are more than five branches, the more-branch-count is the
        # total branch count less five.
        series, ignored, ignored = self.makeBranches(8)
        self.assertMoreBranchCount(3, series)

    def assertGroupBranchesEqual(self, expected, series):
        """Check that the branches part of the series dict match."""
        view = GroupedDistributionSourcePackageBranchesView(
            self.distro_source_package, LaunchpadTestRequest())
        series_group = view.groups[0]
        branches = series_group['branches']
        self.assertEqual(len(expected), len(branches),
                         "%s different length to %s" %
                         (pformat(expected), pformat(branches)))
        for b1, b2 in zip(expected, branches):
            # Since one is a branch and the other is a decorated branch,
            # just check the ids.
            self.assertEqual(b1.id, b2.id)

    def test_series_branch_order_no_official(self):
        # If there are no official branches, then the branches are in most
        # recently modified order, with at most five in the list.
        series, branches, official = self.makeBranches(8)
        self.assertGroupBranchesEqual(branches[:5], series)

    def test_series_branch_order_official_first(self):
        # If there is an official branch, it comes first in the list.
        series, branches, official = self.makeBranches(8, 1)
        expected = official + branches[:4]
        self.assertGroupBranchesEqual(expected, series)

    def test_series_branch_order_two_three(self):
        # If there are more than two official branches, and there are three or
        # more user branches, then only two of the official branches will be
        # shown, ordered by pocket.
        series, branches, official = self.makeBranches(8, 3)
        expected = official[:2] + branches[:3]
        self.assertGroupBranchesEqual(expected, series)

    def test_series_branch_order_three_two(self):
        # If there are more than two official branches, but there are less
        # than three user branches, then official branches are added in until
        # there are at most five branches.
        series, branches, official = self.makeBranches(6, 4)
        expected = official[:3] + branches
        self.assertGroupBranchesEqual(expected, series)


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)

