# Copyright 2019 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Views, menus, and traversal related to `PersonOCIProject`s."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'PersonOCIProjectNavigation',
    ]

from zope.component import queryAdapter
from zope.interface import implementer
from zope.traversing.interfaces import IPathAdapter

from lp.code.browser.vcslisting import PersonTargetDefaultVCSNavigationMixin
from lp.registry.interfaces.personociproject import IPersonOCIProject
from lp.services.webapp import (
    canonical_url,
    Navigation,
    StandardLaunchpadFacets,
    )
from lp.services.webapp.breadcrumb import Breadcrumb
from lp.services.webapp.interfaces import IMultiFacetedBreadcrumb


class PersonOCIProjectNavigation(
        PersonTargetDefaultVCSNavigationMixin, Navigation):

    usedfor = IPersonOCIProject


# XXX cjwatson 2019-11-26: Do we need two breadcrumbs, one for the
# distribution and one for the OCI project?
@implementer(IMultiFacetedBreadcrumb)
class PersonOCIProjectBreadcrumb(Breadcrumb):
    """Breadcrumb for an `IPersonOCIProject`."""

    @property
    def text(self):
        return self.context.oci_project.display_name

    @property
    def url(self):
        if self._url is None:
            return canonical_url(
                self.context.oci_project, rootsite=self.rootsite)
        else:
            return self._url

    @property
    def icon(self):
        return queryAdapter(
            self.context.oci_project, IPathAdapter, name='image').icon()


class PersonOCIProjectFacets(StandardLaunchpadFacets):
    """The links that will appear in the facet menu for an `IPersonOCIProject`.
    """

    usedfor = IPersonOCIProject
    enable_only = ['branches']