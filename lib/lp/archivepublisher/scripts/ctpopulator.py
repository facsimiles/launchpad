# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).
"""Populate Commitment Tracker with Launchpad DEB packages data.

This script creates `CTDeliveryDebJob` for the given archive, status,
distroseries and date range.
"""

__all__ = [
    "CTPopulator",
]

from datetime import timezone
from optparse import OptionValueError

from zope.component import getUtility

from lp.archivepublisher.model.ctdeliverydebjob import CTDeliveryDebJob
from lp.registry.errors import NoSuchDistroSeries
from lp.registry.interfaces.distribution import IDistributionSet
from lp.scripts.helpers import LPOptionParser
from lp.services.scripts.base import LaunchpadScript
from lp.soyuz.enums import PackagePublishingStatus
from lp.soyuz.interfaces.archive import IArchiveSet


class CTPopulator(LaunchpadScript):
    """Populate Commitment Tracker with Launchpad DEB data, using the
    `CTDeliveryDebJob`."""

    def add_my_options(self):
        """Register options specific to this script."""
        # Replace the parser with LPOptionParser for datetime support
        usage = self.parser.usage
        description = self.parser.description
        self.parser = LPOptionParser(usage=usage, description=description)

        self.parser.add_option(
            "-A",
            "--archive",
            dest="archive",
            default=None,
            help=(
                "Filter by this archive reference. "
                "Ex: ~owner/distribution/name"
            ),
        )
        self.parser.add_option(
            "-d",
            "--distribution",
            dest="distribution",
            default=None,
            help="Filter by this distribution name.",
        )
        self.parser.add_option(
            "-s",
            "--series",
            dest="distroseries",
            default=None,
            help="Filter by this distroseries name.",
        )
        self.parser.add_option(
            "--status",
            dest="status",
            default="PUBLISHED",
            help=(
                "Filter by this publishing status (PUBLISHED, SUPERSEDED). "
                "Default: PUBLISHED"
            ),
        )
        self.parser.add_option(
            "--before",
            dest="date_end",
            type="datetime",
            default=None,
            help=(
                "Filter by this UTC end date "
                "(format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)."
            ),
        )
        self.parser.add_option(
            "--after",
            dest="date_start",
            type="datetime",
            default=None,
            help=(
                "Filter by this UTC start date "
                "(format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)."
            ),
        )
        self.parser.add_option(
            "-x",
            "--dry-run",
            dest="dry_run",
            action="store_true",
            default=False,
            help="Pretend; don't commit changes.",
        )
        self.parser.add_option(
            "--profile",
            dest="profile",
            metavar="FILE",
            help=(
                "Run the script under the profiler and save the "
                "profiling stats in FILE."
            ),
        )

    def getOptions(self):
        """Verify command-line options and return the corresponding objects."""
        if not self.options.archive:
            raise OptionValueError(
                "Archive reference is required (use -A or --archive)."
            )

        # Validate date range if both dates are provided
        if self.options.date_start and self.options.date_end:
            if self.options.date_start > self.options.date_end:
                raise OptionValueError(
                    "Start date must be before or equal to end date."
                )

        # Validate status parameter
        valid_statuses = [
            PackagePublishingStatus.PUBLISHED.name,
            PackagePublishingStatus.SUPERSEDED.name,
        ]
        if self.options.status.upper() not in valid_statuses:
            raise OptionValueError(
                f"Invalid status '{self.options.status}'. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )

        # Resolve the archive
        archive = getUtility(IArchiveSet).getByReference(self.options.archive)
        if archive is None:
            raise OptionValueError(
                f"Archive '{self.options.archive}' not found."
            )

        self.logger.info(
            "Processing archive: %s (%s)",
            archive.reference,
            archive.displayname,
        )

        # Resolve distroseries ID if provided
        distroseries_id = None
        if self.options.distroseries:
            if not self.options.distribution:
                raise OptionValueError(
                    "Distribution name is required when specifying a series "
                    "(use -d or --distribution)."
                )

            distro = getUtility(IDistributionSet).getByName(
                self.options.distribution
            )
            if distro is None:
                raise OptionValueError(
                    f"Distribution '{self.options.distribution}' not found."
                )

            try:
                distroseries = distro.getSeries(self.options.distroseries)
            except NoSuchDistroSeries:
                raise OptionValueError(
                    f"Distroseries '{self.options.distroseries}' not found "
                    f"in distribution '{self.options.distribution}'."
                )

            distroseries_id = distroseries.id
            self.logger.info(
                "Filtering by distroseries: %s/%s",
                distro.name,
                distroseries.name,
            )

        # Convert dates to UTC if provided
        date_start = None
        date_end = None
        if self.options.date_start:
            date_start = self.options.date_start.replace(tzinfo=timezone.utc)
            self.logger.info("Start date: %s", date_start.isoformat())

        if self.options.date_end:
            date_end = self.options.date_end.replace(tzinfo=timezone.utc)
            self.logger.info("End date: %s", date_end.isoformat())

        # Get the status enum value
        status = getattr(PackagePublishingStatus, self.options.status.upper())
        self.logger.info("Status filter: %s", status.name)

        return archive, date_start, date_end, distroseries_id, status

    def main(self):
        """Do the script's work."""
        archive, date_start, date_end, distroseries_id, status = (
            self.getOptions()
        )

        self.logger.info(
            f"CTDeliveryDebJob: archive_id={archive.id}, "
            f"date_start={date_start}, date_end={date_end}, "
            f"distroseries={distroseries_id}, status={status.name}"
        )

        if self.options.dry_run:
            self.logger.info("Dry run mode - aborting.")
            self.txn.abort()
            return

        # Create the job
        job = CTDeliveryDebJob.create_manual(
            archive_id=archive.id,
            date_start=date_start,
            date_end=date_end,
            distroseries=distroseries_id,
            status=status.value,
        )

        if job is None:
            self.logger.warning(
                "Job creation returned None. CT delivery may be disabled."
            )
        else:
            self.logger.info(f"Created CTDeliveryDebJob: {job.job_id}")
            self.txn.commit()
            self.logger.info("Job committed successfully.")
