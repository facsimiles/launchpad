# Copyright 2007 Canonical Ltd.  All rights reserved.

"""Tests for BranchSet."""

__metaclass__ = type

from unittest import TestCase, TestLoader

import transaction

from canonical.launchpad.ftests import login, logout, ANONYMOUS
from canonical.launchpad.interfaces import IBranchSet, IProductSet

from canonical.lp.dbschema import BranchLifecycleStatus

from canonical.testing import LaunchpadFunctionalLayer

from zope.component import getUtility


class TestBranchSet(TestCase):

    layer = LaunchpadFunctionalLayer

    def setUp(self):
        TestCase.setUp(self)
        login(ANONYMOUS)
        self.product = getUtility(IProductSet).getByName('firefox')
        self.branch_set = getUtility(IBranchSet)

    def tearDown(self):
        logout()
        TestCase.tearDown(self)

    def test_limitedByQuantity(self):
        """When getting the latest branches for a product, we can specify the
        maximum number of branches we want to know about.
        """
        quantity = 3
        latest_branches = self.branch_set.getLatestBranchesForProduct(
            self.product, quantity)
        self.assertEqual(quantity, len(list(latest_branches)))

    def test_onlyForProduct(self):
        """getLatestBranchesForProduct returns branches only from the requested
        product.
        """
        quantity = 5
        latest_branches = self.branch_set.getLatestBranchesForProduct(
            self.product, quantity)
        self.assertEqual(
            [self.product.name] * quantity,
            [branch.product.name for branch in latest_branches])

    def test_abandonedBranchesNotIncluded(self):
        """getLatestBranchesForProduct does not include branches that have been
        abandoned, because they are not relevant for those interested in recent
        activity.
        """
        original_branches = list(
            self.branch_set.getLatestBranchesForProduct(self.product, 0))
        branch = original_branches[0]
        # XXX: JonathanLange 2007-07-05, This assumes that the branch owner is
        # an individual and not a team.
        login(branch.owner.preferredemail.email)
        try:
            branch.lifecycle_status = BranchLifecycleStatus.ABANDONED
        finally:
            logout()
        transaction.commit()
        login(ANONYMOUS)
        latest_branches = list(
            self.branch_set.getLatestBranchesForProduct(self.product, 0))
        self.assertEqual(original_branches[1:], latest_branches)


def test_suite():
    return TestLoader().loadTestsFromName(__name__)
