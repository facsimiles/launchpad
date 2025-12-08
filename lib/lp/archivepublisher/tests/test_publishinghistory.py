# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for ArchivePublishingHistory model class."""

from storm.exceptions import NoneError
from zope.component import getUtility
from zope.interface.verify import verifyObject

from lp.archivepublisher.interfaces.archivepublishinghistory import (
    IArchivePublishingHistory,
    IArchivePublishingHistorySet,
)
from lp.archivepublisher.model.archivepublishinghistory import (
    ArchivePublishingHistory,
    ArchivePublishingHistorySet,
)
from lp.services.database.interfaces import IStore
from lp.testing import TestCaseWithFactory
from lp.testing.layers import ZopelessDatabaseLayer


class TestArchivePublishingHistory(TestCaseWithFactory):
    """Test the `ArchivePublishingHistory` model."""

    layer = ZopelessDatabaseLayer

    def test_verify_interface(self):
        """Test ArchivePublishingHistory interface."""
        archive = self.factory.makeArchive()
        publisher_run = self.factory.makeArchivePublisherRun()

        publishing_history = ArchivePublishingHistory(
            archive=archive, publisher_run=publisher_run
        )
        IStore(ArchivePublishingHistory).add(publishing_history)
        IStore(ArchivePublishingHistory).flush()

        verified = verifyObject(IArchivePublishingHistory, publishing_history)
        self.assertTrue(verified)

    def test_properties(self):
        """Test ArchivePublishingHistory properties."""
        archive = self.factory.makeArchive()
        publisher_run = self.factory.makeArchivePublisherRun()

        publishing_history = self.factory.makeArchivePublishingHistory(
            archive=archive, publisher_run=publisher_run
        )

        self.assertIsNotNone(publishing_history.id)
        self.assertEqual(archive, publishing_history.archive)
        self.assertEqual(publisher_run, publishing_history.publisher_run)

    def test_archive_required(self):
        """Test that storm raises NoneError when archive is None."""

        publisher_run = self.factory.makeArchivePublisherRun()

        self.assertRaises(
            NoneError,
            ArchivePublishingHistory,
            archive=None,
            publisher_run=publisher_run,
        )

    def test_publisher_run_required(self):
        """Test that storm raises NoneError when publisher_run is None."""

        archive = self.factory.makeArchive()
        self.assertRaises(
            NoneError,
            ArchivePublishingHistory,
            archive=archive,
            publisher_run=None,
        )

    def test_multiple_archives_in_same_run(self):
        """Test that multiple archives can be published in the same run."""
        archive1 = self.factory.makeArchive()
        archive2 = self.factory.makeArchive()
        publisher_run = self.factory.makeArchivePublisherRun()

        publishing_history1 = self.factory.makeArchivePublishingHistory(
            archive=archive1, publisher_run=publisher_run
        )
        publishing_history2 = self.factory.makeArchivePublishingHistory(
            archive=archive2, publisher_run=publisher_run
        )

        self.assertEqual(publisher_run, publishing_history1.publisher_run)
        self.assertEqual(publisher_run, publishing_history2.publisher_run)
        self.assertNotEqual(archive1, archive2)


class TestArchivePublishingHistorySet(TestCaseWithFactory):
    """Test the `ArchivePublishingHistorySet` utility."""

    layer = ZopelessDatabaseLayer

    def test_verify_interface(self):
        """Test ArchivePublishingHistorySet interface."""
        publishing_history_set = ArchivePublishingHistorySet()
        verified = verifyObject(
            IArchivePublishingHistorySet, publishing_history_set
        )
        self.assertTrue(verified)

    def test_new(self):
        """Test creating a new ArchivePublishingHistory."""
        archive = self.factory.makeArchive()
        publisher_run = self.factory.makeArchivePublisherRun()

        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        publishing_history = publishing_history_set.new(
            archive=archive, publisher_run=publisher_run
        )
        IStore(ArchivePublishingHistory).flush()

        self.assertIsNotNone(publishing_history.id)
        self.assertEqual(archive, publishing_history.archive)
        self.assertEqual(publisher_run, publishing_history.publisher_run)

    def test_new_with_archive_id(self):
        """Test creating a new ArchivePublishingHistory with archive ID."""
        archive = self.factory.makeArchive()
        publisher_run = self.factory.makeArchivePublisherRun()

        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        publishing_history = publishing_history_set.new(
            archive=archive.id, publisher_run=publisher_run
        )
        IStore(ArchivePublishingHistory).flush()

        self.assertIsNotNone(publishing_history.id)
        self.assertEqual(archive, publishing_history.archive)
        self.assertEqual(publisher_run, publishing_history.publisher_run)

    def test_getById(self):
        """Test retrieving a ArchivePublishingHistory by ID."""
        publishing_history = self.factory.makeArchivePublishingHistory()

        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        retrieved = publishing_history_set.getById(publishing_history.id)

        self.assertEqual(publishing_history, retrieved)
        self.assertEqual(publishing_history.archive, retrieved.archive)
        self.assertEqual(
            publishing_history.publisher_run, retrieved.publisher_run
        )

    def test_getById_not_found(self):
        """Test getById returns None for non-existent ID."""
        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        result = publishing_history_set.getById(999999)
        self.assertIsNone(result)

    def test_getByArchive(self):
        """Test getByArchive returns ArchivePublishingHistory records for an
        archive."""
        archive1 = self.factory.makeArchive()
        archive2 = self.factory.makeArchive()
        publisher_run1 = self.factory.makeArchivePublisherRun()
        publisher_run2 = self.factory.makeArchivePublisherRun()

        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        # Create histories for archive1
        history1_1 = publishing_history_set.new(
            archive=archive1, publisher_run=publisher_run1
        )
        history1_2 = publishing_history_set.new(
            archive=archive1, publisher_run=publisher_run2
        )
        # Create history for archive2
        history2_1 = publishing_history_set.new(
            archive=archive2, publisher_run=publisher_run1
        )

        # Get histories for archive1
        histories = list(publishing_history_set.getByArchive(archive1))
        self.assertEqual(2, len(histories))
        self.assertIn(history1_1, histories)
        self.assertIn(history1_2, histories)
        self.assertNotIn(history2_1, histories)

    def test_getByArchive_empty(self):
        """Test getByArchive returns empty when archive has no histories."""
        archive = self.factory.makeArchive()
        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        histories = list(publishing_history_set.getByArchive(archive))
        self.assertEqual(0, len(histories))

    def test_getByArchivePublisherRun(self):
        """Test getByArchivePublisherRun returns ArchivePublishingHistory
        records for a publisher run."""
        archive1 = self.factory.makeArchive()
        archive2 = self.factory.makeArchive()
        publisher_run1 = self.factory.makeArchivePublisherRun()
        publisher_run2 = self.factory.makeArchivePublisherRun()

        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        # Create histories for publisher_run1
        history1_1 = publishing_history_set.new(
            archive=archive1, publisher_run=publisher_run1
        )
        history1_2 = publishing_history_set.new(
            archive=archive2, publisher_run=publisher_run1
        )
        # Create history for publisher_run2
        history2_1 = publishing_history_set.new(
            archive=archive1, publisher_run=publisher_run2
        )

        # Get histories for publisher_run1
        histories = list(
            publishing_history_set.getByArchivePublisherRun(publisher_run1)
        )
        self.assertEqual(2, len(histories))
        self.assertIn(history1_1, histories)
        self.assertIn(history1_2, histories)
        self.assertNotIn(history2_1, histories)

    def test_getByArchivePublisherRun_empty(self):
        """Test getByArchivePublisherRun returns empty when run has no
        histories."""
        publisher_run = self.factory.makeArchivePublisherRun()
        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        histories = list(
            publishing_history_set.getByArchivePublisherRun(publisher_run)
        )
        self.assertEqual(0, len(histories))

    def test_title_property(self):
        """Test that the Set has a title property."""
        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        self.assertEqual(
            "Archive Publishing History Records", publishing_history_set.title
        )

    def test_archive_reference_integrity(self):
        """Test that the archive reference is properly maintained."""
        publishing_history = self.factory.makeArchivePublishingHistory()

        # Verify we can access the archive through the reference
        self.assertEqual(
            publishing_history.archive.id, publishing_history.archive.id
        )
        self.assertIsNotNone(publishing_history.archive.owner)

    def test_publisher_run_reference_integrity(self):
        """Test that the publisher_run reference is properly maintained."""
        publishing_history = self.factory.makeArchivePublishingHistory()
        publishing_history.publisher_run.mark_succeeded()

        # Verify we can access the publisher run through the reference
        self.assertIsNotNone(publishing_history.publisher_run.id)
        self.assertIsNotNone(publishing_history.publisher_run.date_started)
        self.assertIsNotNone(publishing_history.publisher_run.date_finished)
