# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import datetime
from datetime import timezone

import requests
import transaction
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.archivepublisher.interfaces.ctdeliveryjob import (
    ICTDeliveryDebJobSource,
)
from lp.archivepublisher.model import ctdeliverydebjob as jobmod
from lp.archivepublisher.model.archivepublisherrun import (
    ArchivePublisherRunStatus,
)
from lp.archivepublisher.model.ctdeliverydebjob import (
    CT_DELIVERY_ENABLED,
    CT_DELIVERY_MANUAL_TIMEOUT,
    CTDeliveryDebJob,
)
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.services.commitmenttracker.client import CommitmentTrackerClient
from lp.services.database import interfaces as dbinterfaces
from lp.services.features.testing import FeatureFixture
from lp.services.job.tests import block_on_job
from lp.soyuz.enums import PackagePublishingStatus
from lp.testing import TestCaseWithFactory
from lp.testing.layers import CeleryJobLayer, LaunchpadScriptLayer


class CTDeliveryDebJobTests(TestCaseWithFactory):
    """Test case for CTDeliveryDebJob."""

    layer = LaunchpadScriptLayer

    def setUp(self):
        super().setUp()
        # Default: enable CT delivery for tests unless explicitly disabled in
        # a given test case.
        self.useFixture(FeatureFixture({CT_DELIVERY_ENABLED: True}))
        self.publisher_run = self.factory.makeArchivePublisherRun()
        self.archive = self.factory.makeArchive()
        self.archive_history = self.factory.makeArchivePublishingHistory(
            publisher_run=self.publisher_run, archive=self.archive
        )

    @property
    def job_source(self):
        return getUtility(ICTDeliveryDebJobSource)

    def test_getOopsVars(self):
        """Test getOopsVars method."""
        job = self.job_source.create(self.archive_history)
        vars = job.getOopsVars()
        naked_job = removeSecurityProxy(job)
        self.assertIn(("ctdeliveryjob_job_id", naked_job.id), vars)
        self.assertIn(
            ("ctdeliveryjob_job_type", naked_job.job_type.title), vars
        )
        self.assertIn(
            ("publishing_history", naked_job.publishing_history), vars
        )

    def test___repr__(self):
        """Test __repr__ method."""
        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
        }

        job = self.job_source.create(self.archive_history)
        naked_archive_history = removeSecurityProxy(self.archive_history)

        expected = (
            "<CTDeliveryDebJob for "
            f"publishing_history: {naked_archive_history.id}, "
            f"metadata: {metadata}"
            ">"
        )
        self.assertEqual(expected, repr(job))

    def test_arguments(self):
        """Test that CTDeliveryDebJob specified with arguments can
        be gotten out again."""
        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
        }

        job = self.job_source.create(self.archive_history)

        naked_job = removeSecurityProxy(job)
        self.assertEqual(naked_job.metadata, metadata)

    def test_create_raises_error_when_publishing_history_is_none(self):
        """Test that create() raises ValueError when publishing_history_id is
        None."""
        self.assertRaisesWithContent(
            ValueError,
            "publishing_history not found",
            self.job_source.create,
            publishing_history_id=None,
        )

    def test_create_feature_flag_disabled_returns_none(self):
        """Test that create() returns None when feature flag is disabled."""
        self.useFixture(FeatureFixture({CT_DELIVERY_ENABLED: ""}))
        job = self.job_source.create(self.archive_history)
        self.assertIsNone(job)

    def test_run(self):
        """Run CTDeliveryDebJob."""
        job = self.job_source.create(self.archive_history)
        job.run()

        result = job.metadata.get("result")
        self.assertEqual([], result.get("error_description"))
        self.assertIn("bpph", result)
        self.assertIn("spph", result)
        self.assertIn("ct_success_count", result)
        self.assertIn("ct_failure_count", result)

    def test_get(self):
        """CTDeliveryDebJob.get() returns the import job for the given
        handler.
        """
        # There is no job before creating it
        self.assertIs(None, self.job_source.get(self.archive_history))

        job = self.job_source.create(self.archive_history)
        job_gotten = self.job_source.get(self.archive_history)

        self.assertIsInstance(job, CTDeliveryDebJob)
        self.assertEqual(job, job_gotten)

    def test_error_description_when_no_error(self):
        """The CTDeliveryDebJob.error_description property returns
        None when no error description is recorded."""
        job = self.job_source.create(self.archive_history)
        self.assertEqual([], removeSecurityProxy(job).error_description)

    def test_error_description_set_when_notifying_about_user_errors(self):
        """Test that error_description is set by notifyUserError()."""
        job = self.job_source.create(self.archive_history)
        message = "This is an example message."
        job.notifyUserError(message)
        self.assertEqual([message], removeSecurityProxy(job).error_description)

    def _setup_published_history(self):
        """Create prev/current runs and published SPPH/BPPH with files."""
        # Provide a previous successful run/history so the window is defined.
        prev_run = self.factory.makeArchivePublisherRun()
        prev_run = removeSecurityProxy(prev_run)
        prev_run.status = ArchivePublisherRunStatus.SUCCEEDED
        prev_run.date_finished = datetime.datetime.now(
            timezone.utc
        ) - datetime.timedelta(hours=2)
        prev_hist = self.factory.makeArchivePublishingHistory(
            archive=self.archive, publisher_run=prev_run
        )
        dbinterfaces.IStore(prev_run).flush()
        dbinterfaces.IStore(prev_hist).flush()

        # Create real SPPH/BPPH within window.
        # Source publish
        spph = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph = removeSecurityProxy(spph)
        spph.datepublished = datetime.datetime.now(
            timezone.utc
        ) - datetime.timedelta(hours=1)
        # Ensure SPPH has a file/sha256.
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph).flush()

        # Binary publish (with file so sha256 is present).
        bpph = self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        bpph = removeSecurityProxy(bpph)
        bpph.datecreated = datetime.datetime.now(
            timezone.utc
        ) - datetime.timedelta(minutes=90)
        bpph.datepublished = datetime.datetime.now(
            timezone.utc
        ) - datetime.timedelta(minutes=80)
        dbinterfaces.IStore(bpph).flush()

        ah = removeSecurityProxy(self.archive_history)
        ah.publisher_run.date_finished = datetime.datetime.now(timezone.utc)
        return bpph, spph

    def test_run_records_counts_and_errors(self):
        """Job run records CT counts and failure summaries."""
        bpph, spph = self._setup_published_history()

        def _client_with_failing_post():
            client = CommitmentTrackerClient(base_url="http://commitment.test")

            def _fail_post(*args, **kwargs):
                raise requests.RequestException("boom")

            client.session.post = _fail_post
            return client

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            _client_with_failing_post,
        )

        job = self.job_source.create(self.archive_history)
        job.run()
        result = job.metadata.get("result")
        self.assertEqual([bpph.id], result["bpph"])
        self.assertEqual([spph.id], result["spph"])
        self.assertEqual(0, result["ct_success_count"])
        self.assertEqual(2, result["ct_failure_count"])
        self.assertGreaterEqual(len(result["error_description"]), 2)

    def test_run_records_counts_success(self):
        """Job run records CT counts on success."""
        bpph, spph = self._setup_published_history()

        def _client_with_ok_post():
            client = CommitmentTrackerClient(base_url="http://commitment.test")

            def _ok_post(*args, **kwargs):
                class _Resp:
                    status_code = 200
                    text = ""

                return _Resp()

            client.session.post = _ok_post
            return client

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            _client_with_ok_post,
        )

        job = self.job_source.create(self.archive_history)
        job.run()
        result = job.metadata.get("result")
        self.assertEqual([bpph.id], result["bpph"])
        self.assertEqual([spph.id], result["spph"])
        self.assertEqual(2, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])
        self.assertEqual([], result["error_description"])

    def test_run_feature_flag_disabled(self):
        """Run exits early when feature flag is off."""
        self.useFixture(
            # Feature flags are stored as strings; use an empty string to be
            # falsy under bool().
            FeatureFixture({CT_DELIVERY_ENABLED: ""})
        )

        # Ensure the run would otherwise proceed.
        ah = removeSecurityProxy(self.archive_history)
        ah.publisher_run.date_finished = datetime.datetime.now(timezone.utc)

        def _should_not_call():
            raise AssertionError(
                "CT client should not be called when disabled"
            )

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            _should_not_call,
        )

        job = self.job_source.create(self.archive_history)
        self.assertIsNone(job)

    def test_run_first_run_uses_lookback_window(self):
        """First run falls back to lookback window and delivers payloads."""
        now = datetime.datetime.now(timezone.utc)
        ah = removeSecurityProxy(self.archive_history)
        ah.publisher_run.date_finished = now
        ah.publisher_run.status = ArchivePublisherRunStatus.SUCCEEDED
        dbinterfaces.IStore(ah.publisher_run).flush()

        # Create publishes within lookback (no previous run exists).
        spph = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph = removeSecurityProxy(spph)
        spph.datecreated = now
        spph.datepublished = now
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph).flush()

        bpph = self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        bpph = removeSecurityProxy(bpph)
        bpph.datecreated = now
        bpph.datepublished = now
        dbinterfaces.IStore(bpph).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        job = self.job_source.create(self.archive_history)
        job.run()
        result = job.metadata["result"]
        self.assertEqual([bpph.id], result["bpph"])
        self.assertEqual([spph.id], result["spph"])
        self.assertEqual(2, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])
        self.assertEqual([], result["error_description"])
        self.assertEqual(2, len(captured.get("payloads", [])))

    def test_run_pocket_to_enum_conversion(self):
        """Pocket numeric values map to enum suffix strings."""
        bpph, spph = self._setup_published_history()
        bpph = removeSecurityProxy(bpph)
        spph = removeSecurityProxy(spph)
        bpph.pocket = PackagePublishingPocket.UPDATES
        spph.pocket = PackagePublishingPocket.UPDATES

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        job = self.job_source.create(self.archive_history)
        job.run()

        payloads = captured.get("payloads", [])
        self.assertEqual(2, len(payloads))
        pockets = [
            p["release"]["properties"]["archive_pocket"] for p in payloads
        ]
        self.assertEqual(["updates", "updates"], pockets)

        result = job.metadata["result"]
        self.assertEqual(2, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])
        self.assertEqual([], result["error_description"])

    def test_run_no_payloads_to_deliver(self):
        """Run exits early when no payloads fall in the window."""
        prev_run = self.factory.makeArchivePublisherRun()
        prev_run = removeSecurityProxy(prev_run)
        prev_run.status = ArchivePublisherRunStatus.SUCCEEDED
        prev_run.date_finished = datetime.datetime.now(
            timezone.utc
        ) - datetime.timedelta(hours=2)
        prev_hist = self.factory.makeArchivePublishingHistory(
            archive=self.archive, publisher_run=prev_run
        )
        dbinterfaces.IStore(prev_run).flush()
        dbinterfaces.IStore(prev_hist).flush()

        ah = removeSecurityProxy(self.archive_history)
        ah.publisher_run.date_finished = datetime.datetime.now(timezone.utc)

        def _should_not_call():
            raise AssertionError(
                "CT client should not be called when no payloads exist"
            )

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            _should_not_call,
        )

        job = self.job_source.create(self.archive_history)
        job.run()

        result = job.metadata["result"]
        self.assertEqual([], result["bpph"])
        self.assertEqual([], result["spph"])
        self.assertEqual(0, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])
        self.assertEqual([], result["error_description"])

    def test_run_with_none_finished_date_uses_now(self):
        """Test that run uses current time when publisher_run.date_finished is
        None."""
        # Set date_finished to None
        ah = removeSecurityProxy(self.archive_history)
        ah.publisher_run.date_finished = None
        dbinterfaces.IStore(ah.publisher_run).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Should not raise and should complete
        job = self.job_source.create(self.archive_history)
        job.run()

        # No publishes in window
        result = job.metadata["result"]
        self.assertEqual(0, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])

    def test_manual_mode_create_requires_parameters(self):
        """Manual mode requires archive_id."""
        self.assertRaisesWithContent(
            ValueError,
            "archive_id is required",
            CTDeliveryDebJob.create_manual,
            archive_id=None,
            date_start=datetime.datetime.now(timezone.utc),
            date_end=datetime.datetime.now(timezone.utc),
        )

    def test_manual_mode_create_validates_date_order(self):
        """Manual mode validates that date_start <= date_end."""
        date_start = datetime.datetime(2024, 2, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)

        self.assertRaisesWithContent(
            ValueError,
            "date_start must be less than or equal to date_end",
            CTDeliveryDebJob.create_manual,
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
        )

    def test_manual_mode_create_feature_flag_disabled(self):
        """Manual mode returns None when feature flag is disabled."""
        self.useFixture(FeatureFixture({CT_DELIVERY_ENABLED: ""}))

        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)

        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
        )

        self.assertIsNone(job)

    def test_manual_mode_create_stores_metadata(self):
        """Manual mode stores parameters in metadata."""
        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)

        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
        )

        self.assertIsNotNone(job)
        manual_mode = job.metadata.get("manual_mode")
        self.assertIsNotNone(manual_mode)
        self.assertEqual(self.archive.id, manual_mode["archive_id"])
        self.assertEqual(date_start.timestamp(), manual_mode["date_start"])
        self.assertEqual(date_end.timestamp(), manual_mode["date_end"])

        # Should have no publishing_history
        self.assertIsNone(job.context.publishing_history_id)

    def test_manual_mode_run_with_published_data(self):
        """Manual mode processes publications within date range."""
        # Create publications within a specific date range
        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)
        publish_date = datetime.datetime(2024, 1, 15, tzinfo=timezone.utc)

        # Create a source package publication
        spph = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph = removeSecurityProxy(spph)
        spph.datecreated = publish_date
        spph.datepublished = publish_date
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph).flush()

        # Create a binary package publication
        bpph = self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        bpph = removeSecurityProxy(bpph)
        bpph.datecreated = publish_date
        bpph.datepublished = publish_date
        dbinterfaces.IStore(bpph).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Create and run job in manual mode
        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
        )
        job.run()

        # Verify results
        result = job.metadata["result"]
        self.assertEqual([bpph.id], result["bpph"])
        self.assertEqual([spph.id], result["spph"])
        self.assertEqual(2, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])
        self.assertEqual([], result["error_description"])

        # Verify payloads were sent
        payloads = captured.get("payloads", [])
        self.assertEqual(2, len(payloads))

    def test_manual_mode_run_excludes_outside_date_range(self):
        """Manual mode excludes publications outside date range."""
        # Define date range
        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)

        # Create publication BEFORE date range
        spph_before = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph_before = removeSecurityProxy(spph_before)
        spph_before.datecreated = datetime.datetime(
            2023, 12, 15, tzinfo=timezone.utc
        )
        spph_before.datepublished = datetime.datetime(
            2023, 12, 15, tzinfo=timezone.utc
        )
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph_before.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph_before).flush()

        # Create publication AFTER date range
        spph_after = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph_after = removeSecurityProxy(spph_after)
        spph_after.datecreated = datetime.datetime(
            2024, 2, 15, tzinfo=timezone.utc
        )
        spph_after.datepublished = datetime.datetime(
            2024, 2, 15, tzinfo=timezone.utc
        )
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph_after.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph_after).flush()

        # Create publication WITHIN date range
        spph_within = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph_within = removeSecurityProxy(spph_within)
        spph_within.datecreated = datetime.datetime(
            2024, 1, 15, tzinfo=timezone.utc
        )
        spph_within.datepublished = datetime.datetime(
            2024, 1, 15, tzinfo=timezone.utc
        )
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph_within.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph_within).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Create and run job in manual mode
        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
        )
        job.run()

        # Verify only the publication within range is included
        result = job.metadata["result"]
        self.assertEqual([spph_within.id], result["spph"])
        self.assertEqual(1, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])

        # Verify only one payload was sent
        payloads = captured.get("payloads", [])
        self.assertEqual(1, len(payloads))

    def test_manual_mode_run_with_nonexistent_archive(self):
        """Manual mode handles nonexistent archive gracefully."""
        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)

        # Use an archive ID that doesn't exist
        nonexistent_archive_id = 999999

        job = CTDeliveryDebJob.create_manual(
            archive_id=nonexistent_archive_id,
            date_start=date_start,
            date_end=date_end,
        )

        # Should not raise, just log and return
        job.run()

        # No payloads should be sent
        result = job.metadata["result"]
        self.assertEqual([], result["bpph"])
        self.assertEqual([], result["spph"])
        self.assertEqual(0, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])

    def test_manual_mode_with_none_dates(self):
        """Manual mode works with None dates."""
        # Create publication within recent timeframe
        publish_date = datetime.datetime.now(timezone.utc)

        spph = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph = removeSecurityProxy(spph)
        spph.datecreated = publish_date
        spph.datepublished = publish_date
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Create and run job with no date constraints
        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
        )
        job.run()

        # Should find and process the recent publication
        result = job.metadata["result"]
        self.assertIn(spph.id, result["spph"])
        self.assertGreater(result["ct_success_count"], 0)

    def test_manual_mode_with_distroseries_filter(self):
        """Manual mode filters by distroseries when provided."""
        date_start = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        date_end = datetime.datetime(2024, 1, 31, tzinfo=timezone.utc)
        publish_date = datetime.datetime(2024, 1, 15, tzinfo=timezone.utc)

        # Create distroseries
        distroseries1 = self.factory.makeDistroSeries(
            distribution=self.archive.distribution
        )
        distroseries2 = self.factory.makeDistroSeries(
            distribution=self.archive.distribution
        )

        # Create publication in distroseries1
        spph1 = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            distroseries=distroseries1,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph1 = removeSecurityProxy(spph1)
        spph1.datecreated = publish_date
        spph1.datepublished = publish_date
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph1.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph1).flush()

        # Create publication in distroseries2
        spph2 = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            distroseries=distroseries2,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph2 = removeSecurityProxy(spph2)
        spph2.datecreated = publish_date
        spph2.datepublished = publish_date
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph2.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph2).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Filter by distroseries1
        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            date_start=date_start,
            date_end=date_end,
            distroseries=distroseries1.id,
        )
        job.run()

        # Should only include spph1
        result = job.metadata["result"]
        self.assertEqual([spph1.id], result["spph"])
        self.assertEqual(1, result["ct_success_count"])

    def test_run_with_superseded_status_filter(self):
        """Job includes only SUPERSEDED publications when status filter is
        set to SUPERSEDED."""
        # Create publications that should be excluded
        spph_published = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph_published = removeSecurityProxy(spph_published)
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph_published.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph_published).flush()

        bpph_pending = self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PENDING,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.PUBLISHED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.DELETED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.OBSOLETE,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        bpph_pending = removeSecurityProxy(bpph_pending)
        dbinterfaces.IStore(bpph_pending).flush()

        # Create superseded publications that should be included
        spph_superseded = self.factory.makeSourcePackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.SUPERSEDED,
            pocket=PackagePublishingPocket.RELEASE,
        )
        spph_superseded = removeSecurityProxy(spph_superseded)
        self.factory.makeSourcePackageReleaseFile(
            sourcepackagerelease=spph_superseded.sourcepackagerelease,
            library_file=self.factory.makeLibraryFileAlias(db_only=True),
        )
        dbinterfaces.IStore(spph_superseded).flush()

        bpph_superseded = self.factory.makeBinaryPackagePublishingHistory(
            archive=self.archive,
            status=PackagePublishingStatus.SUPERSEDED,
            pocket=PackagePublishingPocket.RELEASE,
            with_file=True,
        )
        bpph_superseded = removeSecurityProxy(bpph_superseded)
        dbinterfaces.IStore(bpph_superseded).flush()

        captured = {}

        class _FakeClient:
            def send_payloads_with_results(self, payloads):
                captured["payloads"] = payloads
                return len(payloads), []

        self.patch(
            jobmod,
            "get_commitment_tracker_client",
            lambda: _FakeClient(),
        )

        # Create manual job with SUPERSEDED status filter
        job = CTDeliveryDebJob.create_manual(
            archive_id=self.archive.id,
            status=PackagePublishingStatus.SUPERSEDED.value,
        )
        job.run()

        # Only superseded (not published) should be included
        result = job.metadata["result"]
        self.assertEqual([bpph_superseded.id], result["bpph"])
        self.assertEqual([spph_superseded.id], result["spph"])
        self.assertEqual(2, result["ct_success_count"])
        self.assertEqual(0, result["ct_failure_count"])

        # Should only have 2 payloads (the superseded ones)
        payloads = captured.get("payloads", [])
        self.assertEqual(2, len(payloads))

    def test_get_manual_timeout_minutes_method(self):
        """Test _get_manual_timeout_minutes static method."""
        # Default value when not set
        self.useFixture(FeatureFixture({CT_DELIVERY_ENABLED: True}))
        self.assertEqual(30, CTDeliveryDebJob._get_manual_timeout_minutes())

        # Configured value
        self.useFixture(
            FeatureFixture(
                {
                    CT_DELIVERY_MANUAL_TIMEOUT: "60",
                }
            )
        )
        self.assertEqual(60, CTDeliveryDebJob._get_manual_timeout_minutes())

        # Invalid value falls back to default
        self.useFixture(
            FeatureFixture(
                {
                    CT_DELIVERY_MANUAL_TIMEOUT: "invalid",
                }
            )
        )
        self.assertEqual(30, CTDeliveryDebJob._get_manual_timeout_minutes())


class TestViaCelery(TestCaseWithFactory):
    layer = CeleryJobLayer

    def setUp(self):
        super().setUp()
        self.publisher_run = self.factory.makeArchivePublisherRun()
        self.archive = self.factory.makeArchive()
        self.archive_history = self.factory.makeArchivePublishingHistory(
            publisher_run=self.publisher_run, archive=self.archive
        )

    def test_job(self):
        """Job runs via Celery."""
        fixture = FeatureFixture(
            {
                "jobs.celery.enabled_classes": "CTDeliveryDebJob",
                CT_DELIVERY_ENABLED: True,
            }
        )
        self.useFixture(fixture)
        job_source = getUtility(ICTDeliveryDebJobSource)

        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
        }

        with block_on_job():
            job_source.create(self.archive_history)
            transaction.commit()

        job = job_source.get(self.archive_history)
        self.assertEqual(metadata, job.metadata)
