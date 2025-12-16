# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import transaction
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.archivepublisher.interfaces.ctdeliveryjob import ICTDeliveryJobSource
from lp.archivepublisher.model.ctdeliverydebjob import CTDeliveryDebJob
from lp.services.features.testing import FeatureFixture
from lp.services.job.tests import block_on_job
from lp.testing import TestCaseWithFactory
from lp.testing.layers import CeleryJobLayer, DatabaseFunctionalLayer


class CTDeliveryDebJobTests(TestCaseWithFactory):
    """Test case for CTDeliveryDebJob."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.publisher_run = self.factory.makeArchivePublisherRun()
        self.archive = self.factory.makeArchive()
        self.archive_history = self.factory.makeArchivePublishingHistory(
            publisher_run=self.publisher_run, archive=self.archive
        )

    @property
    def job_source(self):
        return getUtility(ICTDeliveryJobSource)

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
            "request": {},
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
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
            "request": {},
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
            },
        }

        job = self.job_source.create(self.archive_history)

        naked_job = removeSecurityProxy(job)
        self.assertEqual(naked_job.metadata, metadata)

    def test_run(self):
        """Run CTDeliveryDebJob."""
        job = self.job_source.create(self.archive_history)
        job.run()

        self.assertEqual(
            job.metadata.get("result"),
            {
                "error_description": [],
                "bpph": ["hello-1.1"],
                "spph": [],
            },
        )

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
            }
        )
        self.useFixture(fixture)
        job_source = getUtility(ICTDeliveryJobSource)

        metadata = {
            "request": {},
            "result": {
                "error_description": [],
                "bpph": ["hello-1.1"],
                "spph": [],
            },
        }

        with block_on_job():
            job_source.create(self.archive_history)
            transaction.commit()

        job = job_source.get(self.archive_history)
        self.assertEqual(metadata, job.metadata)
