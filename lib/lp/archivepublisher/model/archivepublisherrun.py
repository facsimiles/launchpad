# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Database class for table ArchivePublisherRun."""

__all__ = [
    "ArchivePublisherRun",
    "ArchivePublisherRunSet",
]

from datetime import datetime, timezone

from storm.locals import DateTime, Int
from storm.store import Store
from zope.component import getUtility
from zope.interface import implementer

from lp.archivepublisher.interfaces.archivepublisherrun import (
    ArchivePublisherRunStatus,
    IArchivePublisherRun,
    IArchivePublisherRunSet,
)
from lp.archivepublisher.interfaces.archivepublishinghistory import (
    IArchivePublishingHistorySet,
)
from lp.services.database.enumcol import DBEnum
from lp.services.database.interfaces import IPrimaryStore, IStore
from lp.services.database.stormbase import StormBase


@implementer(IArchivePublisherRun)
class ArchivePublisherRun(StormBase):
    """See `IArchivePublisherRun`."""

    __storm_table__ = "ArchivePublisherRun"

    id = Int(primary=True)

    date_started = DateTime(
        name="date_started", tzinfo=timezone.utc, allow_none=False
    )

    date_finished = DateTime(
        name="date_finished", tzinfo=timezone.utc, allow_none=True
    )

    status = DBEnum(
        name="status",
        allow_none=False,
        enum=ArchivePublisherRunStatus,
        default=ArchivePublisherRunStatus.INCOMPLETE,
    )

    def __init__(self):
        super().__init__()
        self.date_started = datetime.now(timezone.utc)
        self.date_finished = None
        self.status = ArchivePublisherRunStatus.INCOMPLETE

    def mark_succeeded(self):
        """See `IArchivePublisherRun`."""
        self.date_finished = datetime.now(timezone.utc)
        self.status = ArchivePublisherRunStatus.SUCCEEDED

    def mark_failed(self):
        """See `IArchivePublisherRun`."""
        self.date_finished = datetime.now(timezone.utc)
        self.status = ArchivePublisherRunStatus.FAILED

    def publishing_history(self):
        """See `IArchivePublisherRun`."""
        publishing_history_set = getUtility(IArchivePublishingHistorySet)
        return list(publishing_history_set.getByArchivePublisherRun(self))

    def destroySelf(self):
        """See `IArchivePublisherRun`."""
        Store.of(self).remove(self)


@implementer(IArchivePublisherRunSet)
class ArchivePublisherRunSet:
    """See `IArchivePublisherRunSet`."""

    title = "Archive Publisher Runs"

    def new(self):
        """See `IArchivePublisherRunSet`."""
        store = IPrimaryStore(ArchivePublisherRun)
        publisher_run = ArchivePublisherRun()
        store.add(publisher_run)
        return publisher_run

    def getById(self, id):
        """See `IArchivePublisherRunSet`."""
        return IStore(ArchivePublisherRun).get(ArchivePublisherRun, id)
