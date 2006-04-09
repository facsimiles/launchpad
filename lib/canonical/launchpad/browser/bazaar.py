# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""View support classes for the bazaar application."""

__metaclass__ = type

__all__ = ['BazaarApplicationView', 'BazaarApplicationNavigation']

from zope.component import getUtility
from canonical.launchpad.interfaces import (
    IProductSeriesSourceSet, IBazaarApplication, IProductSet)
from canonical.lp.dbschema import ImportStatus
from canonical.launchpad.webapp import (
    Navigation, stepto, enabled_with_permission, ApplicationMenu, Link)
import canonical.launchpad.layers


class BazaarBranchesMenu(ApplicationMenu):
    usedfor = IBazaarApplication
    facet = 'branches'
    links = ['importer', 'all_branches']

    @enabled_with_permission('launchpad.Admin')
    def importer(self):
        target = 'series/'
        text = 'Branch Importer'
        summary = 'Manage CVS and SVN Trunk Imports'
        return Link(target, text, summary, icon='branch')

    def all_branches(self):
        target = '+all-branches'
        text = 'Show All Branches'
        summary = 'Listing every branch registered in The Bazaar'
        return Link(target, text, summary, icon='branch')


class BazaarApplicationView:

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.seriesset = getUtility(IProductSeriesSourceSet)

    def branches(self):
        """List of all branches in the system."""
        branches = self.context.all
        return sorted(branches, key=self._branch_sort_key)

    @staticmethod
    def _branch_sort_key(branch):
        """Key for sorting branches for display."""
        if branch.product is None:
            product = None
        else:
            product = branch.product.name
        if branch.author is None:
            author = None
        else:
            author = branch.author.browsername
        status = branch.lifecycle_status.sortkey
        return (product, author, status, branch.name)

    def import_count(self):
        return self.seriesset.importcount()

    def testing_count(self):
        return self.seriesset.importcount(ImportStatus.TESTING.value)

    def autotested_count(self):
        return self.seriesset.importcount(ImportStatus.AUTOTESTED.value)

    def testfailed_count(self):
        return self.seriesset.importcount(ImportStatus.TESTFAILED.value)

    def processing_count(self):
        return self.seriesset.importcount(ImportStatus.PROCESSING.value)

    def syncing_count(self):
        return self.seriesset.importcount(ImportStatus.SYNCING.value)

    def stopped_count(self):
        return self.seriesset.importcount(ImportStatus.STOPPED.value)

    def hct_count(self):
        branches = self.seriesset.search(forimport=True,
            importstatus=ImportStatus.SYNCING.value)
        count = 0
        for branch in branches:
            for package in branch.sourcepackages:
                if package.shouldimport:
                    count += 1
                    continue
        return count


class BazaarApplicationNavigation(Navigation):

    usedfor = IBazaarApplication

    newlayer = canonical.launchpad.layers.BazaarLayer

    @stepto('products')
    def products(self):
        # DEPRECATED
        return getUtility(IProductSet)

    @stepto('series')
    def series(self):
        # DEPRECATED
        return getUtility(IProductSeriesSourceSet)

