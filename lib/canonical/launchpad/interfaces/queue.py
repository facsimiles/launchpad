# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""Queue interfaces."""

__metaclass__ = type

__all__ = [
    'QueueStateWriteProtectedError',
    'QueueInconsistentStateError',
    'QueueSourceAcceptError',
    'QueueBuildAcceptError',
    'IUpload',
    'IUploadBuild',
    'IUploadSource',
    'IUploadCustom',
    'IUploadSet',
    'IHasQueueItems',
    ]

from zope.schema import Int, TextLine
from zope.interface import Interface, Attribute
from canonical.launchpad import _


class QueueStateWriteProtectedError(Exception):
    """This exception prevent directly set operation in queue state.

    The queue state machine is controlled by its specific provided methods,
    like: setNew, setAccepted and so on.
    """


class QueueInconsistentStateError(Exception):
    """Queue state machine error.

    It's generated when the solicited state makes the record
    inconsistent against the current system constraints.
    """


class QueueSourceAcceptError(Exception):
    """It prevents a UploadSource from being ACCEPTED.

    It is generated by Component and/or Section mismatching in a DistroRelease.
    """

class QueueBuildAcceptError(Exception):
    """It prevents a UploadBuild from being ACCEPTED.

    It is generated by Component and/or Section mismatching in a DistroRelease.
    """


class IUpload(Interface):
    """A Queue item for Lucille"""

    id = Int(
            title=_("ID"), required=True, readonly=True,
            )

    status = Int(
            title=_("Queue status"), required=False, readonly=True,
            )

    distrorelease = Int(
            title=_("Distribution release"), required=True, readonly=False,
            )

    pocket = Int(
            title=_("The pocket"), required=True, readonly=False,
            )

    changesfile = Attribute("The librarian alias for the changes file "
                            "associated with this upload")

    archive = Int(
            title=_("Archive"), required=True, readonly=False,
            )

    sources = Attribute("The queue sources associated with this queue item")
    builds = Attribute("The queue builds associated with the queue item")
    customfiles = Attribute("Custom upload files associated with this "
                            "queue item")

    datecreated = Attribute("The date on which this queue was created.")
    displayname = TextLine(
        title=_("Generic displayname for a queue item"), readonly=True)
    displayversion = TextLine(
        title=_("The source package version for this item"), readonly=True)
    displayarchs = TextLine(
        title=_("Architetures related to this item"), readonly=True)

    sourcepackagerelease = Attribute(
        "The source package release for this item")

    containsSource = Attribute("whether or not this upload contains sources")
    containsBuild = Attribute("whether or not this upload contains binaries")
    containsInstaller = Attribute(
        "whether or not this upload contains installers images")
    containsTranslation = Attribute(
        "whether or not this upload contains translations")
    containsUpgrader = Attribute(
        "wheter or not this upload contains upgrader images")

    def setNew():
        """Set queue state to NEW."""

    def setUnapproved():
        """Set queue state to UNAPPROVED."""

    def setAccepted():
        """Set queue state to ACCEPTED.

        Preform the required checks on its content, so we garantee data
        integrity by code.
        """

    def setDone():
        """Set queue state to DONE."""

    def setRejected():
        """Set queue state to REJECTED."""

    def realiseUpload(logger=None):
        """Take this ACCEPTED upload and create the publishing records for it
        as appropriate.

        When derivation is taken into account, this may result in queue items
        being created for derived distributions.

        If a logger is provided, messages will be written to it as the upload
        is entered into the publishing records.
        """

    def addSource(spr):
        """Add the provided source package release to this queue entry."""

    def addBuild(build):
        """Add the provided build to this queue entry."""

    def addCustom(library_file, custom_type):
        """Add the provided library file alias as a custom queue entry of
        the given custom type.
        """

    def syncUpdate():
        """Write updates made on this object to the database.

        This should be used when you can't wait until the transaction is
        committed to have some updates actually written to the database.
        """


class IUploadBuild(Interface):
    """A Queue item's related builds (for Lucille)"""

    id = Int(
            title=_("ID"), required=True, readonly=True,
            )


    upload = Int(
            title=_("Upload"), required=True,
            readonly=False,
            )

    build = Int(
            title=_("The related build"), required=True, readonly=False,
            )

    def publish(logger=None):
        """Publish this queued source in the distrorelease referred to by
        the parent queue item.

        We determine the distroarchrelease by matching architecturetags against
        the distroarchrelease the build was compiled for.

        This method can raise NotFoundError if the architecturetag can't be
        matched up in the queue item's distrorelease.

        Returns a list of the secure binary package publishing history
        objects in case it is of use to the caller. This may include records
        published into other distroarchreleases if this build contained arch
        independant packages.

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """

class IUploadSource(Interface):
    """A Queue item's related sourcepackagereleases (for Lucille)"""

    id = Int(
            title=_("ID"), required=True, readonly=True,
            )


    upload = Int(
            title=_("Upload"), required=True,
            readonly=False,
            )

    sourcepackagerelease = Int(
            title=_("The related source package release"), required=True,
            readonly=False,
            )
    
    def checkComponentAndSection():
        """Verify the current Component and Section via Selection table.

        Check if the current sourcepackagerelease component and section
        matches with those included in the target distribution release,
        if not raise QueueSourceAcceptError exception.
        """

    def publish(logger=None):
        """Publish this queued source in the distrorelease referred to by
        the parent queue item.

        Returns the secure source package publishing history object in case
        it is of use to the caller.

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """


class IUploadCustom(Interface):
    """A Queue item's related custom format files (for uploader/queue)"""

    id = Int(
            title=_("ID"), required=True, readonly=True,
            )

    upload = Int(
            title=_("Upload"), required=True,
            readonly=False,
            )

    customformat = Int(
            title=_("The custom format for the file"), required=True,
            readonly=False,
            )

    libraryfilealias = Int(
            title=_("The file"), required=True, readonly=False,
            )

    # useful properties
    archive_config = Attribute("Build and return an ArchiveConfig object.")

    def temp_filename():
        """Return a filename containing the libraryfile for this upload.

        This filename will be in a temporary directory and can be the
        ensure dir can be deleted once whatever needed the file is finished
        with it.
        """

    def publish(logger=None):
        """Publish this custom item directly into the filesystem.

        This can only be run by a process which has filesystem access to
        the archive (or wherever else the content will go).

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """

    def publish_DEBIAN_INSTALLER(logger=None):
        """Publish this custom item as a raw installer tarball.

        This will write the installer tarball out to the right part of
        the archive.

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """

    def publish_DIST_UPGRADER(logger=None):
        """Publish this custom item as a raw dist-upgrader tarball.

        This will write the dist-upgrader tarball out to the right part of
        the archive.

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """

    def publish_ROSETTA_TRANSLATIONS(logger=None):
        """Publish this custom item as a rosetta tarball.

        Essentially this imports the tarball into rosetta.

        If a logger is provided, information pertaining to the publishing
        process will be logged to it.
        """

class IUploadSet(Interface):
    """Represents a set of IUploads"""

    def __iter__():
        """IUpload iterator"""

    def __getitem__(queue_id):
        """Retrieve an IUpload by a given id"""

    def get(queue_id):
        """Retrieve an IUpload by a given id"""

    def count(status=None, distrorelease=None):
        """Number of IUpload present in a given status.

        If status is ommitted return the number of all entries.
        'distrorelease' is optional and restrict the results in given
        distrorelease.
        """

class IHasQueueItems(Interface):
    """An Object that has queue items"""

    def getQueueItems(status=None, name=None, version=None,
                      exact_match=False, pocket=None):
        """Get the union of builds, sources and custom queue items.

        Returns builds, sources and custom queue items in a given state,
        matching a give name and version terms. If 'status' is not supplied,
        return all items in the queues. if 'name' and 'version'
        are supplied return only items which the sourcepackage name or
        binarypackage name or the filename match (SQL LIKE).
        'name' doesn't require 'version'
        'version' doesn't has effect on custom queue items
        If pocket is specified return only queue items inside it, otherwise
        return all pockets.
        Use 'exact_match' argument for precise results.
        """
