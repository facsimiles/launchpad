# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "ExternalPackageSeriesBreadcrumb",
    "ExternalPackageSeriesNavigation",
    "ExternalPackageSeriesFacets",
    "ExternalPackageSeriesURL",
]


from zope.interface import implementer
from zope.publisher.interfaces import NotFound

from lp.app.interfaces.headings import IHeadingBreadcrumb
from lp.bugs.browser.bugtask import BugTargetTraversalMixin
from lp.bugs.browser.structuralsubscription import (
    StructuralSubscriptionTargetTraversalMixin,
)
from lp.registry.browser.externalpackage import ExternalPackageNavigationMixin
from lp.registry.interfaces.externalpackageseries import IExternalPackageSeries
from lp.services.webapp import (
    Navigation,
    StandardLaunchpadFacets,
    canonical_url,
    redirection,
    stepto,
)
from lp.services.webapp.breadcrumb import Breadcrumb
from lp.services.webapp.interfaces import (
    ICanonicalUrlData,
    IMultiFacetedBreadcrumb,
)


@implementer(IHeadingBreadcrumb, IMultiFacetedBreadcrumb)
class ExternalPackageSeriesBreadcrumb(Breadcrumb):
    """Builds a breadcrumb for an `IExternalPackageSeries`."""

    rootsite = "bugs"

    @property
    def text(self):
        return "%s %s package in %s" % (
            self.context.sourcepackagename.name,
            self.context.packagetype.name.lower(),
            self.context.distroseries.named_version,
        )


class ExternalPackageSeriesFacets(StandardLaunchpadFacets):
    usedfor = IExternalPackageSeries
    enable_only = [
        "bugs",
    ]


class ExternalPackageSeriesNavigation(
    Navigation,
    BugTargetTraversalMixin,
    StructuralSubscriptionTargetTraversalMixin,
    ExternalPackageNavigationMixin,
):
    usedfor = IExternalPackageSeries

    @redirection("+editbugcontact")
    def redirect_editbugcontact(self):
        return "+subscribe"

    @stepto("+filebug")
    def filebug(self):
        """Redirect to the IExternalPackage +filebug page."""
        external_package = self.context.distribution_sourcepackage

        redirection_url = canonical_url(external_package, view_name="+filebug")
        if self.request.form.get("no-redirect") is not None:
            redirection_url += "?no-redirect"
        return self.redirectSubTree(redirection_url, status=303)

    def _get_package_for_channel(self, channel):
        try:
            return self.context.distroseries.getExternalPackageSeries(
                self.context.name, self.context.packagetype, channel
            )
        except ValueError:
            # invalid channel returns a 404
            raise NotFound(self.context, channel)


@implementer(ICanonicalUrlData)
class ExternalPackageSeriesURL:
    """External Package URL creation rules."""

    rootsite = None

    def __init__(self, context):
        self.context = context

    @property
    def inside(self):
        return self.context.distroseries

    @property
    def path(self):
        packagetype = self.context.packagetype.name.lower()

        track, risk, branch = self.context.channel or (None, None, None)

        channel_url = ""
        if track:
            channel_url = f"/+track/{track}"
        if risk:
            channel_url = channel_url + f"/+risk/{risk}"
        if branch:
            channel_url = channel_url + f"/+branch/{branch}"

        return f"+{packagetype}/{self.context.name}{channel_url}"
