# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "CTDeliveryJob",
    "CTDeliveryJobDerived",
]

from lazr.delegates import delegate_to
from storm.databases.postgres import JSON
from storm.locals import Int, Reference
from zope.interface import implementer

from lp.app.errors import NotFoundError
from lp.archivepublisher.interfaces.ctdeliveryjob import (
    CTDeliveryJobType,
    ICTDeliveryJob,
)
from lp.services.database.enumcol import DBEnum
from lp.services.database.stormbase import StormBase
from lp.services.job.model.job import EnumeratedSubclass, Job
from lp.services.job.runner import BaseRunnableJob


@implementer(ICTDeliveryJob)
class CTDeliveryJob(StormBase):
    """Base class for jobs related to CT."""

    __storm_table__ = "CTDeliveryJob"

    id = Int(primary=True)

    publishing_history_id = Int(name="publishing_history", allow_none=True)
    publishing_history = Reference(
        publishing_history_id, "ArchivePublishingHistory.id"
    )

    job_type = DBEnum(enum=CTDeliveryJobType, allow_none=False)

    job_id = Int(name="job")
    job = Reference(job_id, Job.id)

    metadata = JSON("json_data", allow_none=False)

    def __init__(self, publishing_history, job_type, metadata):
        super().__init__()
        self.job = Job()
        self.publishing_history = publishing_history
        self.job_type = job_type
        self.metadata = metadata

    def makeDerived(self):
        return CTDeliveryJobDerived.makeSubclass(self)


@delegate_to(ICTDeliveryJob)
class CTDeliveryJobDerived(BaseRunnableJob, metaclass=EnumeratedSubclass):
    """Abstract class for deriving from CTDeliveryJob."""

    def __init__(self, job):
        self.context = job

    @classmethod
    def get(cls, job_id):
        """Get a job by id.

        :return: the CTDeliveryJob with the specified id, as
                 the current CTDeliveryJobDerived subclass.
        :raises: NotFoundError if there is no job with the specified id,
                 or its job_type does not match the desired subclass.
        """
        job = CTDeliveryJob.get(job_id)
        if job.job_type != cls.class_job_type:
            raise NotFoundError(
                "No object found with id %d and type %s"
                % (job_id, cls.class_job_type.title)
            )
        return cls(job)

    def getOopsVars(self):
        """See `IRunnableJob`."""
        vars = super().getOopsVars()
        vars.extend(
            [
                ("ctdeliveryjob_job_id", self.context.id),
                ("publishing_history", self.context.publishing_history),
            ]
        )
        return vars
