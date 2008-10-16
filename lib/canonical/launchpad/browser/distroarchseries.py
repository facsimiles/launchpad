# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

__metaclass__ = type

__all__ = [
    'DistroArchSeriesAddView',
    'DistroArchSeriesBinariesView',
    'DistroArchSeriesContextMenu',
    'DistroArchSeriesNavigation',
    'DistroArchSeriesView',
    ]

from canonical.launchpad import _
from canonical.launchpad.webapp import (
    action, canonical_url, enabled_with_permission, ContextMenu,
    GetitemNavigation, LaunchpadFormView, Link)
from canonical.launchpad.webapp.batching import BatchNavigator
from canonical.launchpad.browser.build import BuildRecordsView

from canonical.launchpad.interfaces.distroarchseries import IDistroArchSeries


class DistroArchSeriesNavigation(GetitemNavigation):

    usedfor = IDistroArchSeries


class DistroArchSeriesContextMenu(ContextMenu):

    usedfor = IDistroArchSeries
    links = ['admin', 'builds']

    @enabled_with_permission('launchpad.Admin')
    def admin(self):
        text = 'Administer'
        return Link('+admin', text, icon='edit')

    # Search link not necessary, because there's a search form on
    # the overview page.

    def builds(self):
        text = 'Show builds'
        return Link('+builds', text, icon='info')


class DistroArchSeriesView(BuildRecordsView):
    """Default DistroArchSeries view class."""


class DistroArchSeriesBinariesView:

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.text = self.request.get("text", None)
        self.matches = 0
        self.detailed = True
        self._results = None

        self.searchrequested = False
        if self.text:
            self.searchrequested = True

    def searchresults(self):
        """Try to find the binary packages in this port that match
        the given text, then present those as a list. Cache previous results
        so the search is only done once.
        """
        if self._results is None:
            self._results = self.context.searchBinaryPackages(self.text)
        self.matches = len(self._results)
        if self.matches > 5:
            self.detailed = False
        return self._results


    def binaryPackagesBatchNavigator(self):
        # XXX: kiko 2006-03-17: This is currently disabled in the template.

        if self.text:
            binary_packages = self.context.searchBinaryPackages(self.text)
        else:
            binary_packages = []
        return BatchNavigator(binary_packages, self.request)


class DistroArchSeriesAddView(LaunchpadFormView):

    schema = IDistroArchSeries
    field_names = ['architecturetag', 'processorfamily', 'official',
                   'supports_virtualized']
    label = _('Create a port')

    @action(_('Continue'), name='continue')
    def create_action(self, action, data):
        """Create a new Port."""
        distroarchseries = self.context.newArch(
            data['architecturetag'], data['processorfamily'],
            data['official'], self.user, data['supports_virtualized'])
        self.next_url = canonical_url(distroarchseries)
