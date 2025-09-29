# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for classes in the lp.code.browser.bazaar module."""

from lp.app.enums import InformationType
from lp.code.browser.bazaar import BazaarApplicationView
from lp.services.webapp.authorization import check_permission
from lp.services.webapp.servers import LaunchpadTestRequest
from lp.testing import ANONYMOUS, TestCaseWithFactory, login
from lp.testing.layers import DatabaseFunctionalLayer


class TestBazaarViewPreCacheLaunchpadPermissions(TestCaseWithFactory):
    """Test the precaching of launchpad.View permissions."""

    layer = DatabaseFunctionalLayer

    def getViewBranches(self, attribute):
        """Create the view and get the branches for `attribute`."""
        request = LaunchpadTestRequest()
        login(ANONYMOUS, request)
        view = BazaarApplicationView(object(), request)
        return getattr(view, attribute)

    def test_recently_registered(self):
        # Create a some private branches (stacked and unstacked) that the
        # logged in user would not normally see.
        private_branch = self.factory.makeAnyBranch(
            information_type=InformationType.USERDATA
        )
        self.factory.makeAnyBranch(stacked_on=private_branch)
        branch = self.factory.makeAnyBranch()
        recent_branches = self.getViewBranches("recently_registered_branches")
        self.assertEqual(branch, recent_branches[0])
        self.assertTrue(check_permission("launchpad.View", branch))

    def makeBranchScanned(self, branch):
        """Make the branch appear scanned."""
        revision = self.factory.makeRevision()
        # Login an administrator so they can update the branch's details.
        login("admin@canonical.com")
        branch.updateScannedDetails(revision, 1)

    def test_recently_changed(self):
        # Create a some private branches (stacked and unstacked) that the
        # logged in user would not normally see.
        private_branch = self.factory.makeAnyBranch(
            information_type=InformationType.USERDATA
        )
        stacked_private_branch = self.factory.makeAnyBranch(
            stacked_on=private_branch
        )
        branch = self.factory.makeAnyBranch()
        self.makeBranchScanned(stacked_private_branch)
        self.makeBranchScanned(branch)
        recent_branches = self.getViewBranches("recently_changed_branches")
        self.assertEqual(branch, recent_branches[0])
        self.assertTrue(check_permission("launchpad.View", branch))
