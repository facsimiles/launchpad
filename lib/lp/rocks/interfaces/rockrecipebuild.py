# Copyright 2024 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Rock recipe build interfaces."""

__all__ = [
    "IRockFile",
    "IRockRecipeBuild",
    "IRockRecipeBuildSet",
]

from lazr.restful.declarations import (
    export_read_operation,
    exported,
    exported_as_webservice_entry,
    operation_for_version,
)
from lazr.restful.fields import Reference
from zope.interface import Attribute, Interface
from zope.schema import Bool, Datetime, Dict, Int, TextLine

from lp import _
from lp.buildmaster.interfaces.buildfarmjob import (
    IBuildFarmJobEdit,
    ISpecificBuildFarmJobSource,
)
from lp.buildmaster.interfaces.packagebuild import (
    IPackageBuild,
    IPackageBuildView,
)
from lp.registry.interfaces.person import IPerson
from lp.rocks.interfaces.rockrecipe import IRockRecipe, IRockRecipeBuildRequest
from lp.services.database.constants import DEFAULT
from lp.services.librarian.interfaces import ILibraryFileAlias
from lp.soyuz.interfaces.distroarchseries import IDistroArchSeries


class IRockRecipeBuildView(IPackageBuildView):
    """`IRockRecipeBuild` attributes that require launchpad.View."""

    build_request = Reference(
        IRockRecipeBuildRequest,
        title=_("The build request that caused this build to be created."),
        required=True,
        readonly=True,
    )

    requester = exported(
        Reference(
            IPerson,
            title=_("The person who requested this build."),
            required=True,
            readonly=True,
        )
    )

    recipe = exported(
        Reference(
            IRockRecipe,
            title=_("The rock recipe to build."),
            required=True,
            readonly=True,
        )
    )

    distro_arch_series = exported(
        Reference(
            IDistroArchSeries,
            title=_("The series and architecture for which to build."),
            required=True,
            readonly=True,
        )
    )

    arch_tag = exported(
        TextLine(title=_("Architecture tag"), required=True, readonly=True)
    )

    channels = exported(
        Dict(
            title=_("Source snap channels to use for this build."),
            description=_(
                "A dictionary mapping snap names to channels to use for this "
                "build.  Currently only 'core', 'core18', 'core20', "
                "and 'rockcraft' keys are supported."
            ),
            key_type=TextLine(),
        )
    )

    virtualized = Bool(
        title=_("If True, this build is virtualized."), readonly=True
    )

    score = exported(
        Int(
            title=_("Score of the related build farm job (if any)."),
            required=False,
            readonly=True,
        )
    )

    eta = Datetime(
        title=_("The datetime when the build job is estimated to complete."),
        readonly=True,
    )

    estimate = Bool(
        title=_("If true, the date value is an estimate."), readonly=True
    )

    date = Datetime(
        title=_(
            "The date when the build completed or is estimated to complete."
        ),
        readonly=True,
    )

    revision_id = exported(
        TextLine(
            title=_("Revision ID"),
            required=False,
            readonly=True,
            description=_(
                "The revision ID of the branch used for this build, if "
                "available."
            ),
        )
    )

    store_upload_metadata = Attribute(
        _("A dict of data about store upload progress.")
    )

    build_metadata_url = exported(
        TextLine(
            title=_("URL of the build metadata file"),
            description=_(
                "URL of the metadata file generated by the fetch service, if "
                "it exists."
            ),
            required=False,
            readonly=True,
        )
    )

    def getFiles():
        """Retrieve the build's `IRockFile` records.

        :return: A result set of (`IRockFile`, `ILibraryFileAlias`,
            `ILibraryFileContent`).
        """

    def getFileByName(filename):
        """Return the corresponding `ILibraryFileAlias` in this context.

        The following file types (and extension) can be looked up:

         * Build log: '.txt.gz'
         * Upload log: '_log.txt'

        Any filename not matching one of these extensions is looked up as a
        rock recipe output file.

        :param filename: The filename to look up.
        :raises NotFoundError: if no file exists with the given name.
        :return: The corresponding `ILibraryFileAlias`.
        """

    @export_read_operation()
    @operation_for_version("devel")
    def getFileUrls():
        """URLs for all the files produced by this build.

        :return: A collection of URLs for this build."""


class IRockRecipeBuildEdit(IBuildFarmJobEdit):
    """`IRockRecipeBuild` methods that require launchpad.Edit."""

    def addFile(lfa):
        """Add a file to this build.

        :param lfa: An `ILibraryFileAlias`.
        :return: An `IRockFile`.
        """


class IRockRecipeBuildAdmin(Interface):
    """`IRockRecipeBuild` methods that require launchpad.Admin."""

    def rescore(score):
        """Change the build's score."""


# XXX jugmac00 2024-09-16 see "beta" is a lie to get WADL generation working,
# see https://bugs.launchpad.net/lazr.restful/+bug/760849
# Individual attributes must set their version to "devel".
@exported_as_webservice_entry(as_of="beta")
class IRockRecipeBuild(
    IRockRecipeBuildView,
    IRockRecipeBuildEdit,
    IRockRecipeBuildAdmin,
    IPackageBuild,
):
    """A build record for a rock recipe."""


class IRockRecipeBuildSet(ISpecificBuildFarmJobSource):
    """Utility to create and access `IRockRecipeBuild`s."""

    def new(
        build_request,
        recipe,
        distro_arch_series,
        channels=None,
        store_upload_metadata=None,
        date_created=DEFAULT,
    ):
        """Create an `IRockRecipeBuild`."""

    def preloadBuildsData(builds):
        """Load the data related to a list of rock recipe builds."""


class IRockFile(Interface):
    """A file produced by a rock recipe build."""

    build = Reference(
        IRockRecipeBuild,
        title=_("The rock recipe build producing this file."),
        required=True,
        readonly=True,
    )

    library_file = Reference(
        ILibraryFileAlias,
        title=_("The library file alias for this file."),
        required=True,
        readonly=True,
    )
