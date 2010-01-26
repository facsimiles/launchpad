# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = ['BuildFarmJob']


from zope.component import getUtility
from zope.interface import classProvides, implements

from canonical.database.sqlbase import sqlvalues
from canonical.launchpad.webapp.interfaces import (
    DEFAULT_FLAVOR, IStoreSelector, MAIN_STORE)
from lp.buildmaster.interfaces.buildfarmjob import (
    IBuildFarmJob, IBuildFarmCandidateJobSelection,
    IBuildFarmJobDispatchEstimation, ISpecificBuildFarmJobClass)
from lp.services.job.interfaces.job import JobStatus


class BuildFarmJob:
    """Mix-in class for `IBuildFarmJob` implementations."""
    implements(IBuildFarmJob)
    classProvides(
        IBuildFarmCandidateJobSelection, IBuildFarmJobDispatchEstimation,
        ISpecificBuildFarmJobClass)

    def score(self):
        """See `IBuildFarmJob`."""
        raise NotImplementedError

    def getLogFileName(self):
        """See `IBuildFarmJob`."""
        return 'buildlog.txt'

    def getName(self):
        """See `IBuildFarmJob`."""
        raise NotImplementedError

    def getTitle(self):
        """See `IBuildFarmJob`."""
        raise NotImplementedError

    def jobStarted(self):
        """See `IBuildFarmJob`."""
        pass

    def jobReset(self):
        """See `IBuildFarmJob`."""
        pass

    def jobAborted(self):
        """See `IBuildFarmJob`."""
        pass

    @property
    def processor(self):
        """See `IBuildFarmJob`."""
        return None

    @property
    def virtualized(self):
        """See `IBuildFarmJob`."""
        return None

    @staticmethod
    def addCandidateSelectionCriteria(processor, virtualized):
        """See `IBuildFarmCandidateJobSelection`."""
        return ('')

    @classmethod
    def getByJob(cls, job):
        """See `ISpecificBuildFarmJobClass`.
        This base implementation should work for most build farm job
        types, but some need to override it.
        """
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        return store.find(cls, cls.job == job).one()

    @staticmethod
    def postprocessCandidate(job, logger):
        """See `IBuildFarmCandidateJobSelection`."""
        return True

    @staticmethod
    def composePendingJobsQuery(min_score, processor, virtualized):
        """See `IBuildFarmJobDispatchEstimation`."""
        return """
            SELECT
                BuildQueue.job,
                BuildQueue.lastscore,
                BuildQueue.estimated_duration,
                BuildQueue.processor,
                BuildQueue.virtualized
            FROM
                BuildQueue, Job
            WHERE
                BuildQueue.job = Job.id
                AND Job.status = %s
                AND BuildQueue.lastscore >= %s
                AND (
                    -- The processor values either match or the candidate
                    -- job is processor-independent.
                    buildqueue.processor = %s OR 
                    buildqueue.processor IS NULL)
                AND buildqueue.virtualized = %s
        """ % sqlvalues(JobStatus.WAITING, min_score, processor, virtualized)
