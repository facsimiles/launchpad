# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Vanilla view classes related to `IDistroSeries`."""

__all__ = [
    "VanillaDistroSeriesView",
]


from datetime import datetime, timedelta, timezone
from enum import Enum

from zope.component import getUtility

from lp.bugs.browser.bugtask import BugTaskImportance, BugTaskStatus
from lp.bugs.interfaces.bugtask import IBugTaskSet
from lp.bugs.interfaces.bugtasksearch import BugTaskSearchParams
from lp.buildmaster.enums import BuildStatus
from lp.layers import VanillaLayer, setAdditionalLayer
from lp.registry.browser import MilestoneOverlayMixin
from lp.registry.browser.distroseries import DerivedDistroSeriesMixin
from lp.registry.interfaces.series import SeriesStatus
from lp.registry.model.milestone import milestone_sort_key
from lp.services.database.interfaces import IStore
from lp.services.webapp.publisher import LaunchpadView
from lp.soyuz.model.binarypackagebuild import BinaryPackageBuild


class ChipColor(str, Enum):
    """Vanilla chip color CSS classes.

    See: https://vanillaframework.io/docs/patterns/chip#colour-coding
    """

    NEUTRAL = "p-chip"
    POSITIVE = "p-chip--positive"
    INFORMATION = "p-chip--information"
    CAUTION = "p-chip--caution"
    NEGATIVE = "p-chip--negative"

    def __str__(self) -> str:
        return self.value


STATUS_CHIP_COLORS = {
    SeriesStatus.CURRENT: ChipColor.POSITIVE,
    SeriesStatus.SUPPORTED: ChipColor.POSITIVE,
    SeriesStatus.DEVELOPMENT: ChipColor.INFORMATION,
    SeriesStatus.FROZEN: ChipColor.INFORMATION,
    SeriesStatus.FUTURE: ChipColor.INFORMATION,
    SeriesStatus.EXPERIMENTAL: ChipColor.CAUTION,
    SeriesStatus.OBSOLETE: ChipColor.CAUTION,
}


class VanillaDistroSeriesView(
    LaunchpadView, MilestoneOverlayMixin, DerivedDistroSeriesMixin
):
    """View for the vanilla distroseries page."""

    def initialize(self):
        super().initialize()
        setAdditionalLayer(self.request, VanillaLayer)

    @property
    def page_title(self):
        """Return the HTML page title."""
        return "%s (%s) : %s" % (
            self.context.displayname,
            self.context.version,
            self.context.distribution.displayname,
        )

    @property
    def status_chip_color(self) -> ChipColor:
        """Return the status chip color."""
        return STATUS_CHIP_COLORS.get(
            self.context.status,
            ChipColor.INFORMATION,
        )

    def _search_bug_tasks(self, **kwargs):
        """Search bug tasks with eager loading disabled.

        Since we only need counts, we use ``_noprejoins`` to skip the
        expensive eager loading that ``searchTasks`` performs by default.
        """
        params = BugTaskSearchParams(
            orderby="-datecreated",
            omit_dupes=True,
            user=self.user,
            **kwargs,
        )
        params.setDistroSeries(self.context)
        return getUtility(IBugTaskSet).search(params, _noprejoins=True)

    @property
    def bugs_summary(self):
        """Return the bugs summary (critical, in progress, triaged counts)."""
        critical_bugs = self._search_bug_tasks(
            importance=BugTaskImportance.CRITICAL,
        )
        inprogress_bugs = self._search_bug_tasks(
            status=BugTaskStatus.INPROGRESS,
        )
        triaged_bugs = self._search_bug_tasks(
            status=BugTaskStatus.TRIAGED,
        )

        return {
            "critical_bugs_count": critical_bugs.count(),
            "inprogress_bugs_count": inprogress_bugs.count(),
            "triaged_bugs_count": triaged_bugs.count(),
        }

    @property
    def packages_summary_24h(self):
        """Return the packages summary for the last 24 hours.

        XXX: Ideally this query logic would live in
        `IBinaryPackageBuildSet` (e.g. `getBuildsForDistro`) with a
        search-params object similar to `BugTaskSearchParams`, rather
        than in the view. That refactoring is out of scope for now.
        """
        store = IStore(BinaryPackageBuild)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        base_clauses = [
            BinaryPackageBuild.distro_series == self.context,
            BinaryPackageBuild.is_distro_archive,
            BinaryPackageBuild.date_finished >= cutoff,
        ]

        total_built = store.find(
            BinaryPackageBuild,
            *base_clauses,
        ).count()
        successful_builds = store.find(
            BinaryPackageBuild,
            *base_clauses,
            BinaryPackageBuild.status == BuildStatus.FULLYBUILT,
        ).count()
        failed_to_build = store.find(
            BinaryPackageBuild,
            *base_clauses,
            BinaryPackageBuild.status == BuildStatus.FAILEDTOBUILD,
        ).count()
        failed_to_upload = store.find(
            BinaryPackageBuild,
            *base_clauses,
            BinaryPackageBuild.status == BuildStatus.FAILEDTOUPLOAD,
        ).count()

        return {
            "built_packages_percentage": (
                round(successful_builds / total_built * 100, 1)
                if total_built
                else 0
            ),
            "failed_to_build_packages_count": failed_to_build,
            "failed_to_upload_packages_count": failed_to_upload,
        }

    @property
    def next_milestone(self):
        """Return the closest upcoming milestone by expected date."""
        today = datetime.today().date()
        # `self.context.milestones` already returns active milestones for this
        # distroseries; we further restrict to those with a date on or after
        # today and pick the one with the earliest expected date.
        upcoming = [
            milestone
            for milestone in self.context.milestones
            if milestone.dateexpected is not None
            and milestone.dateexpected >= today
        ]

        if not upcoming:
            return None

        return min(upcoming, key=milestone_sort_key)
