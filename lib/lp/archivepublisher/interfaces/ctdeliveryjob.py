# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "CTDeliveryJobType",
    "ICTDeliveryJob",
    "ICTDeliveryJobSource",
    "ICTDeliveryDebJob",
]

from lazr.enum import DBEnumeratedType, DBItem
from lazr.restful.fields import Reference
from zope.interface import Attribute, Interface
from zope.schema import Choice, Int, Text

from lp import _
from lp.archivepublisher.interfaces.archivepublishinghistory import (
    IArchivePublishingHistory,
)
from lp.services.job.interfaces.job import IJob, IJobSource, IRunnableJob


class CTDeliveryJobType(DBEnumeratedType):
    DEB = DBItem(
        1,
        """
        DEB

        A job that gets Launchpad DEB data and post it to CT.
        """,
    )


class ICTDeliveryJob(Interface):
    """A Job that acts on CT data."""

    id = Int(
        title=_("ID"),
        required=True,
        readonly=True,
        description=_("The tracking number for this job."),
    )

    publishing_history = Reference(
        title=_("The Archive Publishing History associated with this job."),
        schema=IArchivePublishingHistory,
        required=True,
        readonly=True,
    )

    job_type = Choice(
        title=_("Job type"),
        vocabulary=CTDeliveryJobType,
        required=True,
        readonly=True,
    )

    job = Reference(
        title=_("The common Job attributes"),
        schema=IJob,
        required=True,
        readonly=True,
    )

    metadata = Attribute("A dict of data about the job.")

    def destroySelf():
        """Destroy this object."""


class ICTDeliveryJobSource(IJobSource):
    """An interface for acquiring ICTDeliveryDebJob."""

    def create(publishing_history):
        """Create a new CTDeliveryJob."""

    def get(handler):
        """Retrieve the import job for a handler, if any.

        :return: `None` or an `ICTDeliveryJob`.
        """


class ICTDeliveryDebJob(IRunnableJob):
    """A job that gets Launchpad DEB data and post it to CT."""

    error_description = Text(
        title=_("Error description"),
        description=_(
            "A short description of the last error this "
            "job encountered, if any."
        ),
        readonly=True,
        required=False,
    )
