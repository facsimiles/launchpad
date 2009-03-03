# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Tests for branch listing."""

__metaclass__ = type

import unittest

from storm.expr import Asc, Desc

from canonical.launchpad.browser.branchlisting import (
    BranchListingSort, BranchListingView, SourcePackageBranchesView)
from canonical.launchpad.database.branch import Branch
from canonical.launchpad.database.person import Owner
from canonical.launchpad.database.product import Product
from canonical.launchpad.testing import TestCase, TestCaseWithFactory
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


class TestSourcePackageBranchesView(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_distroseries_links(self):
        # There are some links at the bottom of the page to other
        # distroseries.
        distro = self.factory.makeDistribution()
        series_one = self.factory.makeDistroRelease(
            distribution=distro, version="1.0")
        series_two = self.factory.makeDistroRelease(
            distribution=distro, version="2.0")
        series_three = self.factory.makeDistroRelease(
            distribution=distro, version="3.0")
        package = self.factory.makeSourcePackage(distroseries=series_two)
        request = LaunchpadTestRequest()
        view = SourcePackageBranchesView(package, request)
        self.assertEqual(
            [dict(series=series_one, linked=True),
             dict(series=series_two, linked=False),
             dict(series=series_three, linked=True)],
            list(view.series_links))


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)

