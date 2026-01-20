# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test cases for the CTPopulator script."""

import sys
from datetime import datetime, timezone
from optparse import OptionValueError

from lp.archivepublisher.model.ctdeliverydebjob import CTDeliveryDebJob
from lp.archivepublisher.scripts.ctpopulator import CTPopulator
from lp.services.config import config
from lp.services.log.logger import BufferLogger
from lp.soyuz.enums import PackagePublishingStatus
from lp.testing import TestCaseWithFactory
from lp.testing.fakemethod import FakeMethod
from lp.testing.faketransaction import FakeTransaction
from lp.testing.layers import ZopelessDatabaseLayer


class FakeJob:
    """Simple fake job object for testing."""

    def __init__(self, job_id):
        self.job_id = job_id

    def start(self):
        """Fake start method."""
        pass

    def complete(self):
        """Fake complete method."""
        pass


class FakeCTDeliveryDebJob:
    """Simple fake CTDeliveryDebJob object for testing."""

    def __init__(self, job_id):
        self.job = FakeJob(job_id)
        self.job_id = job_id

    def run(self):
        """Fake start method."""
        pass


class TestCTPopulator(TestCaseWithFactory):
    layer = ZopelessDatabaseLayer

    def makeScript(self, test_args=None):
        """Create a CTPopulator script instance for testing."""
        test_args = [] if test_args is None else list(test_args)
        script = CTPopulator(
            "ctpopulator",
            dbuser=config.archivepublisher.dbuser,
            test_args=test_args,
        )
        script.logger = BufferLogger()
        script.txn = FakeTransaction()
        return script

    def test_script_requires_archive(self):
        """The script requires an archive reference."""
        script = self.makeScript([])
        self.assertRaisesWithContent(
            OptionValueError,
            "Archive reference is required (use -A or --archive).",
            script.main,
        )

    def test_script_with_invalid_archive(self):
        """The script fails with a clear error for invalid archive."""
        script = self.makeScript(["-A", "nonexistent/archive"])
        self.assertRaisesWithContent(
            OptionValueError,
            "Archive 'nonexistent/archive' not found.",
            script.main,
        )

    def test_script_with_valid_archive(self):
        """The script accepts a valid archive reference."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        # Should have been called with archive id
        self.assertEqual(1, CTDeliveryDebJob.create_manual.call_count)
        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(archive.id, call_kwargs["archive_id"])

    def test_script_with_distroseries_requires_distribution(self):
        """Specifying a series requires a distribution."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference, "-s", "jammy"])
        self.assertRaisesWithContent(
            OptionValueError,
            "Distribution name is required when specifying a series "
            "(use -d or --distribution).",
            script.main,
        )

    def test_script_with_invalid_distribution(self):
        """The script fails with invalid distribution."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            ["-A", archive.reference, "-d", "nonexistent", "-s", "jammy"]
        )
        self.assertRaisesWithContent(
            OptionValueError,
            "Distribution 'nonexistent' not found.",
            script.main,
        )

    def test_script_with_invalid_distroseries(self):
        """The script fails with invalid distroseries."""
        archive = self.factory.makeArchive()
        distro = archive.distribution
        script = self.makeScript(
            ["-A", archive.reference, "-d", distro.name, "-s", "nonexistent"]
        )
        self.assertRaisesWithContent(
            OptionValueError,
            "Distroseries 'nonexistent' not found in distribution "
            f"'{distro.name}'.",
            script.main,
        )

    def test_script_with_valid_distroseries(self):
        """The script accepts a valid distroseries."""
        distroseries = self.factory.makeDistroSeries()
        archive = self.factory.makeArchive(
            distribution=distroseries.distribution
        )
        script = self.makeScript(
            [
                "-A",
                archive.reference,
                "-d",
                distroseries.distribution.name,
                "-s",
                distroseries.name,
            ]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(distroseries.id, call_kwargs["distroseries"])

    def test_script_with_distroseries_only(self):
        """The script accepts distroseries without archive (all archives)."""
        distroseries = self.factory.makeDistroSeries()
        script = self.makeScript(
            [
                "-d",
                distroseries.distribution.name,
                "-s",
                distroseries.name,
            ]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        # Should have been called with archive_id=None and distroseries set
        self.assertEqual(1, CTDeliveryDebJob.create_manual.call_count)
        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertIsNone(call_kwargs["archive_id"])
        self.assertEqual(distroseries.id, call_kwargs["distroseries"])

    def test_script_with_date_range(self):
        """The script accepts date range parameters."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            [
                "-A",
                archive.reference,
                "--after",
                "2024-01-01",
                "--before",
                "2024-01-31",
            ]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            call_kwargs["date_start"],
        )
        self.assertEqual(
            datetime(2024, 1, 31, tzinfo=timezone.utc),
            call_kwargs["date_end"],
        )

    def test_script_with_datetime_range(self):
        """The script accepts datetime parameters with time."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            [
                "-A",
                archive.reference,
                "--after",
                "2024-01-01 10:30:00",
                "--before",
                "2024-01-31 23:59:59",
            ]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            call_kwargs["date_start"],
        )
        self.assertEqual(
            datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
            call_kwargs["date_end"],
        )

    def test_script_rejects_invalid_date_range(self):
        """The script rejects date ranges where start is after end."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            [
                "-A",
                archive.reference,
                "--after",
                "2024-01-31",
                "--before",
                "2024-01-01",
            ]
        )
        self.assertRaisesWithContent(
            OptionValueError,
            "Start date must be before or equal to end date.",
            script.main,
        )

    def test_script_rejects_malformed_date_range(self):
        """The script rejects malformed date values."""
        archive = self.factory.makeArchive()

        # Mock sys.exit to capture the call without actually exiting
        exit_called = []

        def mock_exit(code=0):
            exit_called.append(code)
            # Don't actually exit, just record the call

        self.patch(sys, "exit", mock_exit)
        self.makeScript(
            [
                "-A",
                archive.reference,
                "--after",
                "01-01-2024",
            ]
        )

        # Verify sys.exit was called (optparse calls it on error)
        self.assertTrue(
            len(exit_called) > 0,
            "sys.exit should have been called for malformed date",
        )

    def test_script_with_status_published(self):
        """The script accepts PUBLISHED status."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            ["-A", archive.reference, "--status", "PUBLISHED"]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            PackagePublishingStatus.PUBLISHED.value,
            call_kwargs["status"],
        )

    def test_script_with_status_superseded(self):
        """The script accepts SUPERSEDED status."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            ["-A", archive.reference, "--status", "SUPERSEDED"]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            PackagePublishingStatus.SUPERSEDED.value,
            call_kwargs["status"],
        )

    def test_script_with_status_case_insensitive(self):
        """The script accepts status in any case."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            ["-A", archive.reference, "--status", "published"]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            PackagePublishingStatus.PUBLISHED.value,
            call_kwargs["status"],
        )

    def test_script_rejects_invalid_status(self):
        """The script rejects invalid status values."""
        archive = self.factory.makeArchive()
        script = self.makeScript(
            ["-A", archive.reference, "--status", "PENDING"]
        )
        self.assertRaisesWithContent(
            OptionValueError,
            "Invalid status 'PENDING'. Must be one of: PUBLISHED, SUPERSEDED",
            script.main,
        )

    def test_script_default_status_is_published(self):
        """The script defaults to PUBLISHED status."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(
            PackagePublishingStatus.PUBLISHED.value,
            call_kwargs["status"],
        )

    def test_script_dry_run(self):
        """The script supports dry run mode."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference, "--dry-run"])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        # In dry run, create_manual should not be called
        self.assertEqual(0, CTDeliveryDebJob.create_manual.call_count)

    def test_script_handles_none_job_return(self):
        """The script handles when create_manual returns None."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=None),
        )
        script.main()

        log_output = script.logger.getLogBuffer()
        self.assertIn(
            "Job creation returned None. CT delivery may be disabled.",
            log_output,
        )

    def test_script_commits_on_success(self):
        """The script commits the transaction on successful job creation and
        ending."""
        archive = self.factory.makeArchive()
        script = self.makeScript(["-A", archive.reference])

        # Create a fake job with a job_id attribute
        fake_job = FakeCTDeliveryDebJob(12345)

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=fake_job),
        )
        self.patch(
            script.txn,
            "commit",
            FakeMethod(),
        )
        script.main()

        self.assertEqual(2, script.txn.commit.call_count)

    def test_script_with_all_parameters(self):
        """The script accepts all parameters together."""
        distroseries = self.factory.makeDistroSeries()
        archive = self.factory.makeArchive(
            distribution=distroseries.distribution
        )
        script = self.makeScript(
            [
                "-A",
                archive.reference,
                "-d",
                distroseries.distribution.name,
                "-s",
                distroseries.name,
                "--after",
                "2024-01-01 00:00:00",
                "--before",
                "2024-12-31 23:59:59",
                "--status",
                "SUPERSEDED",
            ]
        )

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(archive.id, call_kwargs["archive_id"])
        self.assertEqual(distroseries.id, call_kwargs["distroseries"])
        self.assertEqual(
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            call_kwargs["date_start"],
        )
        self.assertEqual(
            datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            call_kwargs["date_end"],
        )
        self.assertEqual(
            PackagePublishingStatus.SUPERSEDED.value,
            call_kwargs["status"],
        )

    def test_script_processes_primary_archive(self):
        """The script can process a primary archive."""
        distro = self.factory.makeDistribution()
        archive = distro.main_archive
        script = self.makeScript(["-A", archive.reference])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(archive.id, call_kwargs["archive_id"])

    def test_script_processes_ppa(self):
        """The script can process a PPA."""
        ppa = self.factory.makeArchive()
        script = self.makeScript(["-A", ppa.reference])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(ppa.id, call_kwargs["archive_id"])

    def test_script_with_csv_output(self):
        """The script passes CSV output path to job creation."""
        archive = self.factory.makeArchive()
        csv_path = "/tmp/test_releases.csv"
        script = self.makeScript(["-A", archive.reference, "--csv", csv_path])

        self.patch(
            CTDeliveryDebJob,
            "create_manual",
            FakeMethod(result=FakeCTDeliveryDebJob(1)),
        )
        script.main()

        call_args, call_kwargs = CTDeliveryDebJob.create_manual.calls[0]
        self.assertEqual(archive.id, call_kwargs["archive_id"])
        self.assertEqual(csv_path, call_kwargs["csv_output"])
