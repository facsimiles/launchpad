# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "ExternalPackageBreadcrumb",
    "ExternalPackageNavigation",
    "ExternalPackageFacets",
    "ExternalPackageURL",
    "ExternalPackageNavigationMixin",
]


from zope.interface import implementer
from zope.publisher.interfaces import NotFound

from lp.app.interfaces.headings import IHeadingBreadcrumb
from lp.bugs.browser.bugtask import BugTargetTraversalMixin
from lp.bugs.browser.structuralsubscription import (
    StructuralSubscriptionTargetTraversalMixin,
)
from lp.registry.interfaces.externalpackage import IExternalPackage
from lp.services.webapp import (
    Navigation,
    StandardLaunchpadFacets,
    redirection,
    stepthrough,
)
from lp.services.webapp.breadcrumb import Breadcrumb
from lp.services.webapp.interfaces import (
    ICanonicalUrlData,
    IMultiFacetedBreadcrumb,
)


@implementer(IHeadingBreadcrumb, IMultiFacetedBreadcrumb)
class ExternalPackageBreadcrumb(Breadcrumb):
    """Builds a breadcrumb for an `IExternalPackage`."""

    rootsite = "bugs"

    @property
    def text(self):
        return "%s %s package" % (
            self.context.sourcepackagename.name,
            self.context.packagetype.name.lower(),
        )


class ExternalPackageFacets(StandardLaunchpadFacets):
    usedfor = IExternalPackage
    enable_only = [
        "bugs",
    ]


class ExternalPackageNavigationMixin:
    """Provides traversal for +track, +risk, and +branch."""

    def _get_package_for_channel(self, channel):
        """
        Get the external package or package series for a given channel.

        Subclasses must implement this.
        """
        raise NotImplementedError

    @stepthrough("+track")
    def traverse_track(self, track):
        stack = self.request.getTraversalStack()
        if len(stack) >= 2 and stack[-1] == "+risk":
            risk = stack[-2]
        else:
            # If no risk provided, default to stable
            risk = "stable"

        channel = (track, risk, None)
        return self._get_package_for_channel(channel)

    @stepthrough("+risk")
    def traverse_risk(self, risk):
        if self.context.channel:
            channel = (self.context.channel[0], risk)
        else:
            channel = (None, risk, None)

        return self._get_package_for_channel(channel)

    @stepthrough("+branch")
    def traverse_branch(self, branch):
        if self.context.channel:
            track, risk = self.context.channel[0], self.context.channel[1]
        else:
            # If no track/risk provided, default to None/stable
            track = None
            risk = "stable"

        channel = (track, risk, branch)
        return self._get_package_for_channel(channel)


class ExternalPackageNavigation(
    Navigation,
    BugTargetTraversalMixin,
    StructuralSubscriptionTargetTraversalMixin,
    ExternalPackageNavigationMixin,
):
    usedfor = IExternalPackage

    @redirection("+editbugcontact")
    def redirect_editbugcontact(self):
        return "+subscribe"

    def _get_package_for_channel(self, channel):
        try:
            return self.context.distribution.getExternalPackage(
                self.context.name, self.context.packagetype, channel
            )
        except ValueError:
            # invalid channel returns a 404
            raise NotFound(self.context, channel)


@implementer(ICanonicalUrlData)
class ExternalPackageURL:
    """External Package URL creation rules."""

    rootsite = None

    def __init__(self, context):
        self.context = context

    @property
    def inside(self):
        return self.context.distribution

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
