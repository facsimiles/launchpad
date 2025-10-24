# Copyright 2011 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test `BugTargetTraversalMixin`."""

from zope.publisher.interfaces import NotFound
from zope.security.proxy import removeSecurityProxy

from lp.registry.interfaces.externalpackage import ExternalPackageType
from lp.services.webapp.publisher import canonical_url
from lp.testing import TestCaseWithFactory, login_person
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.publication import test_traverse


class TestBugTaskTraversal(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        distribution = self.factory.makeDistribution()
        distroseries = self.factory.makeDistroSeries()
        self.ep = self.factory.makeExternalPackage(distribution=distribution)
        self.eps = self.factory.makeExternalPackageSeries(
            distroseries=distroseries,
            sourcepackagename=self.ep.sourcepackagename,
            packagetype=self.ep.packagetype,
            channel=removeSecurityProxy(self.ep).channel,
        )

    def test_traversal_to_nonexistent_bugtask(self):
        # Test that a traversing to a non-existent bugtask redirects to the
        # bug's default bugtask.
        bug = self.factory.makeBug()
        bugtask = self.factory.makeBugTask(bug=bug)
        bugtask_url = canonical_url(bugtask, rootsite="bugs")
        login_person(bugtask.owner)
        bugtask.delete()
        obj, view, request = test_traverse(bugtask_url)
        view()
        naked_view = removeSecurityProxy(view)
        self.assertEqual(301, request.response.getStatus())
        self.assertEqual(
            naked_view.target,
            canonical_url(bug.default_bugtask, rootsite="bugs"),
        )

    def test_traversal_to_bugtask_delete_url(self):
        # Test that a traversing to the delete URL of a non-existent bugtask
        # raises a NotFound error.
        bug = self.factory.makeBug()
        bugtask = self.factory.makeBugTask(bug=bug)
        bugtask_delete_url = canonical_url(
            bugtask, rootsite="bugs", view_name="+delete"
        )
        login_person(bugtask.owner)
        bugtask.delete()
        self.assertRaises(NotFound, test_traverse, bugtask_delete_url)

    def test_traversal_to_nonexistent_bugtask_on_api(self):
        # Traversing to a non-existent bugtask on the API redirects to
        # the default bugtask, but also on the API.
        bug = self.factory.makeBug()
        product = self.factory.makeProduct()
        obj, view, request = test_traverse(
            "http://api.launchpad.test/1.0/%s/+bug/%d"
            % (product.name, bug.default_bugtask.bug.id)
        )
        self.assertEqual(
            removeSecurityProxy(view).target,
            "http://api.launchpad.test/1.0/%s/+bug/%d"
            % (bug.default_bugtask.target.name, bug.default_bugtask.bug.id),
        )

    def _build_expected_external_bugtask_url(self, bugtask, api=False):
        """Builds the expected canonical URL for a external like bugtask."""
        target = bugtask.target

        track, risk, branch = target.channel
        channel_url = f"/+risk/{risk}"
        if track is not None:
            channel_url = f"/+track/{track}" + channel_url
        if branch is not None:
            channel_url += f"/+branch/{branch}"

        if api:
            base_url = (
                f"http://api.launchpad.test/1.0/{target.distribution.name}"
            )
        else:
            base_url = f"http://bugs.launchpad.test/{target.distribution.name}"

        if bugtask.distroseries:
            base_url += f"/{bugtask.distroseries.name}"

        expected_url = (
            f"{base_url}"
            f"/+{target.packagetype.name.lower()}/{target.name}"
            f"{channel_url}/+bug/{bugtask.bug.id}"
        )
        return expected_url

    def test_traversal_to_external_bugtask(self):
        # Test that we can differ between bugtasks with same packagename and
        # distribution/distroseries, but different packagetype or channel
        bug = self.factory.makeBug()
        distribution = self.factory.makeDistribution()
        distroseries_1 = self.factory.makeDistroSeries(
            distribution=distribution
        )
        distroseries_2 = self.factory.makeDistroSeries(
            distribution=distribution
        )
        spn = self.factory.makeSourcePackageName(name="mypackage")

        targets = (
            self.factory.makeExternalPackage(
                distribution=distribution,
                sourcepackagename=spn,
                packagetype=ExternalPackageType.SNAP,
                channel=("11", "stable", None),
            ),
            self.factory.makeExternalPackage(
                distribution=distribution,
                sourcepackagename=spn,
                packagetype=ExternalPackageType.SNAP,
                channel=("11", "edge", "branch1"),
            ),
            self.factory.makeExternalPackage(
                distribution=distribution,
                sourcepackagename=spn,
                packagetype=ExternalPackageType.CHARM,
                channel=("11", "stable"),
            ),
            self.factory.makeExternalPackageSeries(
                distroseries=distroseries_1,
                sourcepackagename=spn,
                packagetype=ExternalPackageType.CHARM,
                channel="stable",
            ),
            self.factory.makeExternalPackageSeries(
                distroseries=distroseries_2,
                sourcepackagename=spn,
                packagetype=ExternalPackageType.CHARM,
                channel=("stable",),
            ),
        )

        bugtasks = []
        for target in targets:
            bugtasks.append(
                self.factory.makeBugTask(bug=bug, target=target),
            )

        # makeBug creates the first and default bugtask
        self.assertEqual(6, len(bug.bugtasks))
        default, _, _ = test_traverse(canonical_url(bug.default_bugtask))
        self.assertEqual(bug.default_bugtask, default)

        # Check externalpackage urls
        for bugtask in bugtasks[:3]:
            expected_url = self._build_expected_external_bugtask_url(bugtask)
            self.assertEqual(expected_url, canonical_url(bugtask))

            obj, _, _ = test_traverse(canonical_url(bugtask))
            self.assertEqual(bugtask, obj)

        # Check externalpackageseries urls
        for bugtask in bugtasks[3:]:
            expected_url = self._build_expected_external_bugtask_url(bugtask)
            self.assertEqual(expected_url, canonical_url(bugtask))

            obj, _, _ = test_traverse(canonical_url(bugtask))
            self.assertEqual(bugtask, obj)

    def test_traversal_to_default_external_package_bugtask(self):
        # Test that a traversing to a bug with an external package as default
        # bugtask redirects to the bug's default bugtask using +bugtask/id.
        bug = self.factory.makeBug(target=self.ep)
        bug_url = canonical_url(bug, rootsite="bugs")
        obj, view, request = test_traverse(bug_url)
        view()
        naked_view = removeSecurityProxy(view)
        self.assertEqual(303, request.response.getStatus())
        self.assertEqual(
            naked_view.target,
            canonical_url(bug.default_bugtask, rootsite="bugs"),
        )

        bugtask = bug.default_bugtask

        expected_url = self._build_expected_external_bugtask_url(bugtask)
        self.assertEqual(
            expected_url,
            removeSecurityProxy(view).target,
        )

    def test_traversal_to_default_external_package_series_bugtask(self):
        # Test that a traversing to a bug with an external package series
        # as default bugtask redirects to the bug's default bugtask using
        # +bugtask/id.
        bug = self.factory.makeBug(target=self.ep)
        bug_url = canonical_url(bug, rootsite="bugs")

        # We need to create a bugtask in the distribution before creating it in
        # the distroseries
        eps_bugtask = self.factory.makeBugTask(bug=bug, target=self.eps)

        # Deleting the distribution bugtask to change the default one
        login_person(bug.owner)
        bug.default_bugtask.delete()
        self.assertEqual(eps_bugtask, bug.default_bugtask)

        obj, view, request = test_traverse(bug_url)
        view()
        naked_view = removeSecurityProxy(view)
        self.assertEqual(303, request.response.getStatus())
        self.assertEqual(
            naked_view.target,
            canonical_url(bug.default_bugtask, rootsite="bugs"),
        )

        expected_url = self._build_expected_external_bugtask_url(
            bug.default_bugtask
        )
        self.assertEqual(
            expected_url,
            removeSecurityProxy(view).target,
        )

    def test_traversal_to_default_external_package_bugtask_on_api(self):
        # Traversing to a bug with an external package as default task
        # redirects to the +bugtask/id also in the API.
        bug = self.factory.makeBug(target=self.ep)
        obj, view, request = test_traverse(
            "http://api.launchpad.test/1.0/%s/+bug/%d"
            % (
                removeSecurityProxy(self.ep).distribution.name,
                bug.default_bugtask.bug.id,
            )
        )

        expected_url = self._build_expected_external_bugtask_url(
            bug.default_bugtask, api=True
        )
        self.assertEqual(
            expected_url,
            removeSecurityProxy(view).target,
        )

    def test_traversal_to_default_external_package_series_bugtask_on_api(self):
        # Traversing to a bug with an external package series as default task
        # redirects to the +bugtask/id also in the API.
        bug = self.factory.makeBug(target=self.ep)
        # We need to create a bugtask in the distribution before creating it in
        # the distroseries
        eps_bugtask = self.factory.makeBugTask(bug=bug, target=self.eps)

        # Deleting the distribution bugtask to change the default one
        login_person(bug.owner)
        bug.default_bugtask.delete()
        self.assertEqual(eps_bugtask, bug.default_bugtask)

        obj, view, request = test_traverse(
            "http://api.launchpad.test/1.0/%s/+bug/%d"
            % (
                removeSecurityProxy(self.ep).distribution.name,
                bug.default_bugtask.bug.id,
            )
        )

        expected_url = self._build_expected_external_bugtask_url(
            bug.default_bugtask, api=True
        )
        self.assertEqual(
            expected_url,
            removeSecurityProxy(view).target,
        )
