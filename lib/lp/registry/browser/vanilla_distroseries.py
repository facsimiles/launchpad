# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Vanilla view classes related to `IDistroSeries`."""

__all__ = [
    "VanillaDistroSeriesView",
]

from zope.interface import alsoProvides

from lp.layers import VanillaLayer, setAdditionalLayer
from lp.registry.interfaces.distroseries import IDistroSeries
from lp.services.webapp.publisher import LaunchpadView


class VanillaDistroSeriesView(LaunchpadView):
    """View for the vanilla distroseries page."""

    def initialize(self):
        super().initialize()
        setAdditionalLayer(self.request, VanillaLayer)
        alsoProvides(self, IDistroSeries)

    @property
    def page_title(self):
        """Return the HTML page title."""
        return "%s (%s) : %s" % (
            self.context.displayname,
            self.context.version,
            self.context.distribution.displayname,
        )
