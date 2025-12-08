# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for ArchivePublisherRun model class."""

from zope.component import getUtility
from zope.interface.verify import verifyObject

from lp.archivepublisher.interfaces.archivepublisherrun import (
    ArchivePublisherRunStatus,
    IArchivePublisherRun,
    IArchivePublisherRunSet,
)
from lp.archivepublisher.model.archivepublisherrun import (
    ArchivePublisherRun,
    ArchivePublisherRunSet,
)
from lp.services.database.interfaces import IStore
from lp.testing import TestCaseWithFactory
from lp.testing.layers import ZopelessDatabaseLayer


class TestArchivePublisherRun(TestCaseWithFactory):
    """Test the `ArchivePublisherRun` model."""

    layer = ZopelessDatabaseLayer

    def test_verify_interface(self):
        """Test ArchivePublisherRun interface."""
        publisher_run = ArchivePublisherRun()
        IStore(ArchivePublisherRun).add(publisher_run)
        IStore(ArchivePublisherRun).flush()
        verified = verifyObject(IArchivePublisherRun, publisher_run)
        self.assertTrue(verified)

    def test_properties(self):
        """Test ArchivePublisherRun properties."""
        publisher_run = self.factory.makeArchivePublisherRun()

        self.assertIsNotNone(publisher_run.id)
        self.assertIsNotNone(publisher_run.date_started)
        self.assertIsNone(publisher_run.date_finished)
        self.assertEqual(
            ArchivePublisherRunStatus.INCOMPLETE, publisher_run.status
        )

    def test_mark_succeeded(self):
        """Test mark_succeeded method."""
        publisher_run = self.factory.makeArchivePublisherRun()
        publisher_run.mark_succeeded()

        self.assertIsNotNone(publisher_run.date_started)
        self.assertIsNotNone(publisher_run.date_finished)
        self.assertEqual(
            ArchivePublisherRunStatus.SUCCEEDED, publisher_run.status
        )

    def test_mark_failed(self):
        """Test mark_failed method."""
        publisher_run = self.factory.makeArchivePublisherRun()
        publisher_run.mark_failed()

        self.assertIsNotNone(publisher_run.date_started)
        self.assertIsNotNone(publisher_run.date_finished)
        self.assertEqual(
            ArchivePublisherRunStatus.FAILED, publisher_run.status
        )


class TestArchivePublisherRunSet(TestCaseWithFactory):
    """Test the `ArchivePublisherRunSet` utility."""

    layer = ZopelessDatabaseLayer

    def test_verify_interface(self):
        """Test ArchivePublisherRunSet interface."""
        publisher_run_set = ArchivePublisherRunSet()
        verified = verifyObject(IArchivePublisherRunSet, publisher_run_set)
        self.assertTrue(verified)

    def test_new(self):
        """Test creating a new ArchivePublisherRun."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)
        publisher_run = publisher_run_set.new()
        IStore(ArchivePublisherRun).flush()

        self.assertIsNotNone(publisher_run.id)
        self.assertIsNotNone(publisher_run.date_started)
        self.assertIsNone(publisher_run.date_finished)
        self.assertEqual(
            ArchivePublisherRunStatus.INCOMPLETE, publisher_run.status
        )

    def test_getById(self):
        """Test retrieving a ArchivePublisherRun by ID."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)
        publisher_run = publisher_run_set.new()
        IStore(ArchivePublisherRun).flush()

        retrieved_run = publisher_run_set.getById(publisher_run.id)
        self.assertEqual(publisher_run, retrieved_run)

    def test_getById_not_found(self):
        """Test getById a non-existent ArchivePublisherRun returns None."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)
        result = publisher_run_set.getById(999999)
        self.assertIsNone(result)

    def test_multiple_runs(self):
        """Test creating multiple archive publisher runs."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)

        run1 = publisher_run_set.new()
        run2 = publisher_run_set.new()
        IStore(ArchivePublisherRun).flush()

        self.assertNotEqual(run1.id, run2.id)
        self.assertEqual(run1, publisher_run_set.getById(run1.id))
        self.assertEqual(run2, publisher_run_set.getById(run2.id))

    def test_title_property(self):
        """Test that the Set has a title property."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)
        self.assertEqual("Archive Publisher Runs", publisher_run_set.title)

    def test_can_create_with_specific_status(self):
        """Test that ArchivePublisherRun can be created with a specific
        status."""
        publisher_run_set = getUtility(IArchivePublisherRunSet)

        # Create with SUCCEEDED status
        succeeded_run = publisher_run_set.new()
        succeeded_run.mark_succeeded()
        IStore(ArchivePublisherRun).flush()
        self.assertEqual(
            ArchivePublisherRunStatus.SUCCEEDED, succeeded_run.status
        )

        # Create with FAILED status
        failed_run = publisher_run_set.new()
        failed_run.mark_failed()
        IStore(ArchivePublisherRun).flush()
        self.assertEqual(ArchivePublisherRunStatus.FAILED, failed_run.status)
