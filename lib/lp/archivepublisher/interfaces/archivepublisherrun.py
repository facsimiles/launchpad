# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""ArchivePublisherRun interface."""

__all__ = [
    "IArchivePublisherRun",
    "IArchivePublisherRunSet",
    "ArchivePublisherRunStatus",
]

from lazr.enum import DBEnumeratedType, DBItem
from zope.interface import Interface
from zope.schema import Choice, Datetime, Int

from lp import _


class ArchivePublisherRunStatus(DBEnumeratedType):
    """Archive Publisher Run Status

    The various possible states for a publisher run.
    """

    INCOMPLETE = DBItem(
        10,
        """
        Incomplete

        Run is not complete.
        """,
    )

    SUCCEEDED = DBItem(
        20,
        """
        Succeeded

        Run has succeeded.
        """,
    )

    FAILED = DBItem(
        30,
        """
        Failed

        Run has failed.
        """,
    )


class IArchivePublisherRun(Interface):
    """Start and end timestamps for a publisher run."""

    id = Int(title=_("ID"), required=True, readonly=True)

    date_started = Datetime(
        title=_("Date Started"),
        required=True,
        readonly=True,
        description=_("Start timestamp for the publisher run."),
    )

    date_finished = Datetime(
        title=_("Date Finished"),
        required=False,
        readonly=False,
        description=_("End timestamp for the publisher run."),
    )

    status = Choice(
        title=_("Status"),
        required=True,
        readonly=False,
        vocabulary=ArchivePublisherRunStatus,
        description=_("Status of the publisher run."),
    )

    def mark_succeeded():
        """Mark the publisher run as succeeded."""

    def mark_failed():
        """Mark the publisher run as failed."""


class IArchivePublisherRunSet(Interface):
    """A set of archive publisher runs."""

    def new():
        """Create a new `IArchivePublisherRun`.

        :return: A new `IArchivePublisherRun`.
        """

    def getById(id):
        """Get a `IArchivePublisherRun` by its ID.

        :param id: The ID of the publisher run.
        :return: An `IArchivePublisherRun`, or None if not found.
        """
