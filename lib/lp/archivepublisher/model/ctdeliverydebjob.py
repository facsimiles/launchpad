# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "CTDeliveryDebJob",
]

import logging

from zope.interface import implementer, provider

from lp.archivepublisher.interfaces.ctdeliveryjob import (
    CTDeliveryJobType,
    ICTDeliveryDebJob,
    ICTDeliveryJobSource,
)
from lp.archivepublisher.model.ctdeliveryjob import (
    CTDeliveryJob,
    CTDeliveryJobDerived,
)
from lp.services.config import config
from lp.services.database.interfaces import IPrimaryStore, IStore
from lp.services.job.model.job import Job

logger = logging.getLogger(__name__)


@implementer(ICTDeliveryDebJob)
@provider(ICTDeliveryJobSource)
class CTDeliveryDebJob(CTDeliveryJobDerived):
    class_job_type = CTDeliveryJobType.DEB

    user_error_types = ()

    config = config.ICTDeliveryJobSource

    @property
    def publishing_history(self):
        return self.context.publishing_history

    @property
    def error_description(self):
        return self.metadata.get("result").get("error_description")

    @classmethod
    def create(
        cls,
        publishing_history,
    ):
        """Create a new `CTDeliveryDebJob`.

        :param publishing_history: The `IArchivePublishingHistory` associated
            with this job.
        """
        store = IPrimaryStore(CTDeliveryJob)

        # Schedule the initialization.
        metadata = {
            "request": {},
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
            },
        }

        ctdeliveryjob = CTDeliveryJob(
            publishing_history, cls.class_job_type, metadata
        )
        store.add(ctdeliveryjob)
        derived_job = cls(ctdeliveryjob)
        derived_job.celeryRunOnCommit()
        IStore(CTDeliveryJob).flush()
        return derived_job

    @classmethod
    def get(cls, publishing_history):
        """See `ICTDeliveryDebJob`."""
        ctdelivery_job = (
            IStore(CTDeliveryJob)
            .find(
                CTDeliveryJob,
                CTDeliveryJob.job_id == Job.id,
                CTDeliveryJob.job_type == cls.class_job_type,
                CTDeliveryJob.publishing_history == publishing_history,
            )
            .one()
        )
        return None if ctdelivery_job is None else cls(ctdelivery_job)

    def __repr__(self):
        """Returns an informative representation of the job."""
        return (
            f"<{self.__class__.__name__} for "
            f"publishing_history: {self.publishing_history.id}, "
            f"metadata: {self.metadata}>"
        )

    def run(self):
        """See `IRunnableJob`."""
        # Placeholder implementation
        logger.info(
            f"Running CTDeliveryDebJob {self.context.id} - "
            f"Publishing history: {self.context.publishing_history}"
        )
        self.metadata["result"]["bpph"] = ["hello-1.1"]

    def notifyUserError(self, error):
        """Calls up and also saves the error text in this job's metadata.

        See `BaseRunnableJob`.
        """
        # This method is called when error is an instance of
        # self.user_error_types.
        super().notifyUserError(error)
        logger.error(error)
        error_description = self.metadata.get("result").get(
            "error_description", []
        )
        error_description.append(str(error))
        self.metadata["result"]["error_description"] = error_description

    def getOopsVars(self):
        """See `IRunnableJob`."""
        vars = super().getOopsVars()
        vars.extend(
            [
                ("ctdeliveryjob_job_id", self.context.id),
                ("ctdeliveryjob_job_type", self.context.job_type.title),
                ("publishing_history", self.context.publishing_history),
            ]
        )
        return vars
