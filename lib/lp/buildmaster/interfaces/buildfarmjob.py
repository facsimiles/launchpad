# Copyright 2009-2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=E0211,E0213

"""Interface for Soyuz build farm jobs."""

__metaclass__ = type

__all__ = [
    'IBuildFarmJob',
    'IBuildFarmJobOld',
    'IBuildFarmJobSet',
    'IBuildFarmJobSource',
    'InconsistentBuildFarmJobError',
    'ISpecificBuildFarmJob',
    ]

from lazr.enum import (
    DBEnumeratedType,
    )
from lazr.restful.declarations import exported
from lazr.restful.fields import Reference
from zope.interface import (
    Attribute,
    Interface,
    )
from zope.schema import (
    Bool,
    Choice,
    Datetime,
    Int,
    TextLine,
    Timedelta,
    )

from canonical.launchpad import _
from canonical.launchpad.interfaces.librarian import ILibraryFileAlias
from lp.buildmaster.enums import BuildFarmJobType
from lp.buildmaster.interfaces.builder import IBuilder
from lp.soyuz.interfaces.processor import IProcessor


class InconsistentBuildFarmJobError(Exception):
    """Raised when a BuildFarmJob is in an inconsistent state.

    For example, if a BuildFarmJob has a job type for which no adapter
    is yet implemented. Or when adapting the BuildFarmJob to a specific
    type of build job (such as a BinaryPackageBuild) fails.
    """


class IBuildFarmJobOld(Interface):
    """Defines the previous non-database BuildFarmJob interface.

    This interface is still used by the temporary build queue related
    classes (TranslationTemplatesBuildJob, SourcePackageRecipeBuildJob
    and BuildPackageJob).

    XXX 2010-04-28 michael.nelson bug=567922
    This class can be removed (merging all the attributes directly into
    IBuildFarmJob) once all the corresponding *Build classes and the
    BuildQueue have been transitioned to the new database schema.
    """
    processor = Reference(
        IProcessor, title=_("Processor"), required=False, readonly=True,
        description=_(
            "The Processor required by this build farm job. "
            "This should be None for processor-independent job types."))

    virtualized = Bool(
        title=_('Virtualized'), required=False, readonly=True,
        description=_(
            "The virtualization setting required by this build farm job. "
            "This should be None for job types that do not care whether "
            "they run virtualized."))

    def score():
        """Calculate a job score appropriate for the job type in question."""

    def getLogFileName():
        """The preferred file name for this job's log."""

    def getName():
        """An appropriate name for this job."""

    def getTitle():
        """A string to identify and describe the job to users."""

    def jobStarted():
        """'Job started' life cycle event, handle as appropriate."""

    def jobReset():
        """'Job reset' life cycle event, handle as appropriate."""

    def jobAborted():
        """'Job aborted' life cycle event, handle as appropriate."""

    def addCandidateSelectionCriteria(processor, virtualized):
        """Provide a sub-query to refine the candidate job selection.

        Return a sub-query to narrow down the list of candidate jobs.
        The sub-query will become part of an "outer query" and is free to
        refer to the `BuildQueue` and `Job` tables already utilized in the
        latter.

        Example (please see the `BuildPackageJob` implementation for a
        complete example):

            SELECT TRUE
            FROM Archive, Build, BuildPackageJob, DistroArchSeries
            WHERE
            BuildPackageJob.job = Job.id AND
            ..

        :param processor: the type of processor that the candidate jobs are
            expected to run on.
        :param virtualized: whether the candidate jobs are expected to run on
            the `processor` natively or inside a virtual machine.
        :return: a string containing a sub-query that narrows down the list of
            candidate jobs.
        """

    def postprocessCandidate(job, logger):
        """True if the candidate job is fine and should be dispatched
        to a builder, False otherwise.

        :param job: The `BuildQueue` instance to be scrutinized.
        :param logger: The logger to use.

        :return: True if the candidate job should be dispatched
            to a builder, False otherwise.
        """

    def getByJob(job):
        """Get the specific `IBuildFarmJob` for the given `Job`.

        Invoked on the specific `IBuildFarmJob`-implementing class that
        has an entry associated with `job`.
        """

    def generateSlaveBuildCookie():
        """Produce a cookie for the slave as a token of the job it's doing.

        The cookie need not be unique, but should be hard for a
        compromised slave to guess.

        :return: a hard-to-guess ASCII string that can be reproduced
            accurately based on this job's properties.
        """

    def makeJob():
        """Create the specific job relating this with an lp.services.job.

        XXX 2010-04-26 michael.nelson bug=567922
        Once all *Build classes are using BuildFarmJob we can lose the
        'specific_job' attributes and simply have a reference to the
        services job directly on the BuildFarmJob.
        """

    def cleanUp():
        """Job's finished.  Delete its supporting data."""


class IBuildFarmJob(IBuildFarmJobOld):
    """Operations that jobs for the build farm must implement."""

    id = Attribute('The build farm job ID.')

    date_created = exported(
        Datetime(
            title=_("Date created"), required=True, readonly=True,
            description=_(
                "The timestamp when the build farm job was created.")),
        ("1.0", dict(exported=True, exported_as="datecreated")))

    date_started = Datetime(
        title=_("Date started"), required=False, readonly=True,
        description=_("The timestamp when the build farm job was started."))

    date_finished = exported(
        Datetime(
            title=_("Date finished"), required=False, readonly=True,
            description=_(
                "The timestamp when the build farm job was finished.")),
        ("1.0", dict(exported=True, exported_as="datebuilt")))

    duration = Timedelta(
        title=_("Duration"), required=False,
        description=_("Duration interval, calculated when the "
                      "result gets collected."))

    date_first_dispatched = exported(
        Datetime(
            title=_("Date finished"), required=False, readonly=True,
            description=_("The actual build start time. Set when the build "
                          "is dispatched the first time and not changed in "
                          "subsequent build attempts.")))

    builder = Reference(
        title=_("Builder"), schema=IBuilder, required=False, readonly=True,
        description=_("The builder assigned to this job."))

    buildqueue_record = Reference(
        # Really IBuildQueue, set in _schema_circular_imports to avoid
        # circular import.
        schema=Interface, required=True,
        title=_("Corresponding BuildQueue record"))

    status = exported(
        Choice(
            title=_('Status'), required=True,
            # Really BuildStatus, patched in
            # _schema_circular_imports.py
            vocabulary=DBEnumeratedType,
            description=_("The current status of the job.")),
        ("1.0", dict(exported=True, exported_as="buildstate")))

    log = Reference(
        schema=ILibraryFileAlias, required=False,
        title=_(
            "The LibraryFileAlias containing the entire log for this job."))

    log_url = exported(
        TextLine(
            title=_("Build Log URL"), required=False,
            description=_("A URL for the build log. None if there is no "
                          "log available.")),
        ("1.0", dict(exported=True, exported_as="build_log_url")))

    is_private = Bool(
        title=_("is private"), required=False, readonly=True,
        description=_("Whether the build should be treated as private."))

    job_type = Choice(
        title=_("Job type"), required=True, readonly=True,
        vocabulary=BuildFarmJobType,
        description=_("The specific type of job."))

    failure_count = Int(
        title=_("Failure Count"), required=False, readonly=True,
        default=0,
        description=_("Number of consecutive failures for this job."))

    def getSpecificJob():
        """Return the specific build job associated with this record.

        :raises InconsistentBuildFarmJobError: if a specific job could not be
            returned.
        """

    def gotFailure():
        """Increment the failure_count for this job."""

    title = exported(TextLine(title=_("Title"), required=False))

    was_built = Attribute("Whether or not modified by the builddfarm.")

    # This doesn't belong here.  It really belongs in IPackageBuild, but
    # the TAL assumes it can read this directly.
    dependencies = exported(
        TextLine(
            title=_('Dependencies'), required=False,
            description=_(
                'Debian-like dependency line that must be satisfied before '
                'attempting to build this request.')))


class ISpecificBuildFarmJob(IBuildFarmJob):
    """A marker interface with which to define adapters for IBuildFarmJob.

    This enables the registered adapters for ISpecificBuildFarmJob to be
    iterated when calculating IBuildFarmJob.specific_job.
    """


class IBuildFarmJobSource(Interface):
    """A utility of BuildFarmJob used to create _things_."""

    def new(job_type, status=None, processor=None,
            virtualized=None):
        """Create a new `IBuildFarmJob`.

        :param job_type: A `BuildFarmJobType` item.
        :param status: A `BuildStatus` item, defaulting to PENDING.
        :param processor: An optional processor for this job.
        :param virtualized: An optional boolean indicating whether
            this job should be run virtualized.
        """


class IBuildFarmJobSet(Interface):
    """A utility representing a set of build farm jobs."""

    def getBuildsForBuilder(builder_id, status=None, user=None):
        """Return `IBuildFarmJob` records touched by a builder.

        :param builder_id: The id of the builder for which to find builds.
        :param status: If given, limit the search to builds with this status.
        :param user: If given, this will be used to determine private builds
            that should be included.
        :return: a `ResultSet` representing the requested builds.
        """
