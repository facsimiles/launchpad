# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for `VanillaDistroSeriesView`."""

from unittest import TestCase

from lp.buildmaster.enums import BuildStatus
from lp.registry.browser.vanilla_distroseries import (
    BUILD_STATUS_ICONS,
    ERROR_ICON,
    HELP_ICON,
    LOADING_ICON,
    PENDING_ICON,
    SKIP_ICON,
    SUCCESS_ICON,
    Tabs,
)
from lp.soyuz.enums import PackagePublishingStatus
from lp.testing import TestCaseWithFactory, person_logged_in
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.views import create_initialized_view


class TestVanillaDistroSeriesPackagesList(TestCaseWithFactory):
    """Tests for the packages list view properties."""

    layer = DatabaseFunctionalLayer

    def _makeDistroSeries(self):
        distribution = self.factory.makeDistribution()
        return self.factory.makeDistroSeries(distribution=distribution)

    def _makeSpph(self, distroseries, **kwargs):
        return self.factory.makeSourcePackagePublishingHistory(
            distroseries=distroseries,
            archive=distroseries.main_archive,
            status=PackagePublishingStatus.PUBLISHED,
            **kwargs,
        )

    def _getView(self, distroseries, principal=None):
        return create_initialized_view(
            distroseries, "+vanilla", principal=principal
        )

    # -- packages_list_data --

    def test_packages_list_data_empty_state(self):
        """An empty-state <p> is rendered when there are no uploads."""
        distroseries = self._makeDistroSeries()
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn("No recent package uploads found", html)
        self.assertIn("<p", html)
        self.assertNotIn("<table", html)

    def test_packages_list_data_renders_table(self):
        """A <table> is rendered when uploads exist."""
        distroseries = self._makeDistroSeries()
        self._makeSpph(distroseries)
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn("<table>", html)
        self.assertIn("<thead>", html)
        self.assertIn("<tbody>", html)
        self.assertNotIn("No recent package uploads found", html)

    def test_packages_list_data_table_headers(self):
        """The table has the expected column headers."""
        distroseries = self._makeDistroSeries()
        self._makeSpph(distroseries)
        view = self._getView(distroseries)
        html = view.packages_list_data
        for header in ("Source package", "Version", "Pocket", "Builds"):
            self.assertIn("<th>%s</th>" % header, html)

    def test_packages_list_data_shows_package_info(self):
        """The table row contains the source package name and version."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(spph.source_package_name, html)
        self.assertIn(spph.source_package_version, html)

    # -- build status icons --

    def test_packages_list_data_build_success_icon(self):
        """Successfully built packages show the success icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.FULLYBUILT,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(SUCCESS_ICON, html)
        self.assertIn("amd64", html)
        self.assertIn("Successfully built", html)

    def test_packages_list_data_build_failure_icon(self):
        """Failed builds show the error icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.FAILEDTOBUILD,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(ERROR_ICON, html)
        self.assertIn("Failed to build", html)

    def test_packages_list_data_build_in_progress_icon(self):
        """In-progress builds show the loading icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.BUILDING,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(LOADING_ICON, html)
        self.assertIn("Currently building", html)

    def test_packages_list_data_build_pending_icon(self):
        """Queued builds show the pending icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.NEEDSBUILD,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(PENDING_ICON, html)
        self.assertIn("Needs building", html)

    def test_packages_list_data_build_superseded_icon(self):
        """Superseded builds show the skip icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.SUPERSEDED,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(SKIP_ICON, html)

    def test_packages_list_data_multiple_builds(self):
        """Multiple builds for a source are all shown with correct icons."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das_amd64 = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        das_arm64 = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="arm64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das_amd64,
            archive=spph.archive,
            status=BuildStatus.FULLYBUILT,
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das_arm64,
            archive=spph.archive,
            status=BuildStatus.FAILEDTOBUILD,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn(SUCCESS_ICON, html)
        self.assertIn(ERROR_ICON, html)
        self.assertIn("amd64", html)
        self.assertIn("arm64", html)

    def test_packages_list_data_build_tooltip_markup(self):
        """Each build icon is wrapped in a Vanilla tooltip with ARIA."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.FULLYBUILT,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn("p-tooltip--btm-center", html)
        self.assertIn('aria-describedby="build-tooltip-0"', html)
        self.assertIn('role="tooltip"', html)
        self.assertIn('id="build-tooltip-0"', html)
        self.assertIn("Successfully built", html)

    def test_packages_list_data_unknown_status_uses_help_icon(self):
        """Unknown statuses fall back to the pending icon."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das,
            archive=spph.archive,
            status=BuildStatus.NEEDSBUILD,
        )
        original = BUILD_STATUS_ICONS.pop(BuildStatus.NEEDSBUILD)
        try:
            view = self._getView(distroseries)
            html = view.packages_list_data
        finally:
            BUILD_STATUS_ICONS[BuildStatus.NEEDSBUILD] = original
        self.assertIn(HELP_ICON, html)
        self.assertIn("Needs building", html)

    def test_packages_list_data_build_tooltip_unique_ids(self):
        """Each build tooltip has a unique ID."""
        distroseries = self._makeDistroSeries()
        spph = self._makeSpph(distroseries)
        das_amd64 = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="amd64"
        )
        das_arm64 = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="arm64"
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das_amd64,
            archive=spph.archive,
            status=BuildStatus.FULLYBUILT,
        )
        self.factory.makeBinaryPackageBuild(
            source_package_release=spph.sourcepackagerelease,
            distroarchseries=das_arm64,
            archive=spph.archive,
            status=BuildStatus.FAILEDTOBUILD,
        )
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn('id="build-tooltip-0"', html)
        self.assertIn('id="build-tooltip-1"', html)

    def test_packages_list_data_no_builds(self):
        """A source with no builds still renders a row (empty builds cell)."""
        distroseries = self._makeDistroSeries()
        self._makeSpph(distroseries)
        view = self._getView(distroseries)
        html = view.packages_list_data
        self.assertIn("<table>", html)
        # No icon classes should appear.
        self.assertNotIn(SUCCESS_ICON, html)
        self.assertNotIn(ERROR_ICON, html)

    # -- my_uploads_data --

    def test_my_uploads_data_anonymous_returns_empty(self):
        """When no user is logged in, my_uploads_data returns empty markup."""
        distroseries = self._makeDistroSeries()
        view = self._getView(distroseries, principal=None)
        self.assertEqual("", str(view.my_uploads_data))

    def test_my_uploads_data_with_user_no_uploads(self):
        """A logged-in user with no uploads sees the empty-state message."""
        distroseries = self._makeDistroSeries()
        person = self.factory.makePerson()
        with person_logged_in(person):
            view = self._getView(distroseries, principal=person)
            html = view.my_uploads_data
        self.assertIn("You have no recent uploads to this series", html)

    def test_my_uploads_data_with_user_has_uploads(self):
        """A logged-in user with uploads sees a table of their uploads."""
        distroseries = self._makeDistroSeries()
        person = self.factory.makePerson()
        self._makeSpph(distroseries, creator=person)
        # Also create an upload by someone else to confirm filtering.
        self._makeSpph(distroseries, creator=self.factory.makePerson())
        with person_logged_in(person):
            view = self._getView(distroseries, principal=person)
            html = view.my_uploads_data
        self.assertIn("<table>", html)
        # Only one row should appear (the user's upload).
        self.assertEqual(html.count("<tr>"), 2)  # 1 header + 1 data row


class TestBuildStatusIcons(TestCaseWithFactory):
    """Tests for the BUILD_STATUS_ICONS mapping completeness."""

    layer = DatabaseFunctionalLayer

    def test_all_build_statuses_have_icons(self):
        """Every BuildStatus value has a corresponding icon entry."""
        for status in BuildStatus.items:
            self.assertIn(
                status,
                BUILD_STATUS_ICONS,
                "BuildStatus.%s has no entry in BUILD_STATUS_ICONS"
                % status.name,
            )


class FakeRequest(dict):
    """Minimal request stub for Tabs tests."""

    def __init__(self, form=None, query_string=""):
        super().__init__(QUERY_STRING=query_string)
        self.form = form or {}


class TestTabs(TestCase):

    def _makeTabs(self, query_string="", form=None):
        request = FakeRequest(form=form or {}, query_string=query_string)
        return Tabs(
            param="packages-chart",
            default="source",
            tabs=[("source", "Source"), ("binary", "Binary")],
            request=request,
            base_url="/ubuntu/hoary/+vanilla",
            swap_url="/ubuntu/hoary/+vanilla-distroseries-packages-chart",
            swap_target="#packages-chart",
            swap_style="outerHTML",
            aria_label="Package builds",
        )

    def _tabByKey(self, tabs, key):
        for tab in tabs:
            if tab["panel_id"].endswith("-%s-panel" % key):
                return tab
        self.fail("No tab with key %r" % key)

    def test_swap_url_is_clean(self):
        """swap_url is the clean base URL without query params."""
        tabs = self._makeTabs()
        source_tab = self._tabByKey(tabs, "source")
        binary_tab = self._tabByKey(tabs, "binary")
        self.assertEqual(
            "/ubuntu/hoary/+vanilla-distroseries-packages-chart",
            source_tab["swap_url"],
        )
        self.assertEqual(
            "/ubuntu/hoary/+vanilla-distroseries-packages-chart",
            binary_tab["swap_url"],
        )

    def test_swap_url_ignores_query_string(self):
        """swap_url stays clean regardless of request QUERY_STRING."""
        tabs = self._makeTabs(query_string="packages-list=my-uploads")
        source_tab = self._tabByKey(tabs, "source")
        self.assertEqual(
            "/ubuntu/hoary/+vanilla-distroseries-packages-chart",
            source_tab["swap_url"],
        )

    def test_swap_param_key_and_value(self):
        """Each tab has swap_param_key and swap_param_value."""
        tabs = self._makeTabs()
        source_tab = self._tabByKey(tabs, "source")
        binary_tab = self._tabByKey(tabs, "binary")
        self.assertEqual("packages-chart", source_tab["swap_param_key"])
        self.assertEqual("source", source_tab["swap_param_value"])
        self.assertEqual("packages-chart", binary_tab["swap_param_key"])
        self.assertEqual("binary", binary_tab["swap_param_value"])

    def test_is_default(self):
        """Default tab has is_default=True, others False."""
        tabs = self._makeTabs()
        source_tab = self._tabByKey(tabs, "source")
        binary_tab = self._tabByKey(tabs, "binary")
        self.assertTrue(source_tab["is_default"])
        self.assertFalse(binary_tab["is_default"])

    def test_href_includes_param_for_non_default(self):
        """Non-default tab href includes the tab's param."""
        tabs = self._makeTabs()
        binary_tab = self._tabByKey(tabs, "binary")
        self.assertIn("packages-chart=binary", binary_tab["href"])

    def test_href_preserves_other_params(self):
        """href preserves cross-section params for no-JS fallback."""
        tabs = self._makeTabs(query_string="packages-list=my-uploads")
        binary_tab = self._tabByKey(tabs, "binary")
        self.assertIn("packages-list=my-uploads", binary_tab["href"])
        self.assertIn("packages-chart=binary", binary_tab["href"])

    def test_active_returns_default_when_no_form_param(self):
        tabs = self._makeTabs()
        self.assertEqual("source", tabs.active)

    def test_active_returns_form_param(self):
        tabs = self._makeTabs(form={"packages-chart": "binary"})
        self.assertEqual("binary", tabs.active)

    def test_active_panel_id(self):
        tabs = self._makeTabs()
        self.assertEqual("packages-chart-source-panel", tabs.active_panel_id)

    def test_render_includes_swap_attributes(self):
        tabs = self._makeTabs()
        html = tabs.render
        self.assertIn('swap-url="', html)
        self.assertIn('swap-target="#packages-chart"', html)
        self.assertIn('swap-style="outerHTML"', html)
        self.assertIn('swap-param-key="packages-chart"', html)
        self.assertIn('swap-param-value="source"', html)
        self.assertIn('swap-param-value="binary"', html)
        self.assertIn("swap-current", html)

    def test_render_swap_default_on_default_tab_only(self):
        tabs = self._makeTabs()
        html = tabs.render
        # Default tab ("Source") should have swap-default
        self.assertIn('swap-param-value="source" swap-default', html)
        # Non-default tab ("Binary") should NOT have swap-default
        self.assertNotIn('swap-param-value="binary" swap-default', html)
