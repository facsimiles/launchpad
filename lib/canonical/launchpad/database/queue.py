# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

__metaclass__ = type
__all__ = [
    'PackageUploadQueue',
    'PackageUpload',
    'PackageUploadBuild',
    'PackageUploadSource',
    'PackageUploadCustom',
    'PackageUploadSet',
    ]

import os
import shutil
import tempfile

from zope.interface import implements
from sqlobject import (
    ForeignKey, SQLMultipleJoin, SQLObjectNotFound)

from canonical.archivepublisher.customupload import CustomUploadError
from canonical.cachedproperty import cachedproperty
from canonical.database.sqlbase import SQLBase, sqlvalues
from canonical.database.constants import UTC_NOW
from canonical.database.enumcol import EnumCol

from canonical.lp.dbschema import (
    PackageUploadStatus, PackageUploadCustomFormat,
    PackagePublishingPocket, PackagePublishingStatus)

from canonical.launchpad.interfaces import (
    IPackageUpload, IPackageUploadBuild, IPackageUploadSource,
    IPackageUploadCustom, NotFoundError, QueueStateWriteProtectedError,
    QueueInconsistentStateError, QueueSourceAcceptError, IPackageUploadQueue,
    QueueBuildAcceptError, IPackageUploadSet, pocketsuffix)
from canonical.launchpad.database.publishing import (
    SecureSourcePackagePublishingHistory,
    SecureBinaryPackagePublishingHistory)
from canonical.librarian.interfaces import DownloadFailed
from canonical.librarian.utils import copy_and_close
from canonical.lp.dbschema import (
    PackageUploadStatus, PackageUploadCustomFormat,
    PackagePublishingPocket, PackagePublishingStatus)

# There are imports below in PackageUploadCustom for various bits
# of the archivepublisher which cause circular import errors if they
# are placed here.


def debug(logger, msg):
    """Shorthand debug notation for publish() methods."""
    if logger is not None:
        logger.debug(msg)

class PackageUploadQueue:

    implements(IPackageUploadQueue)

    def __init__(self, distroseries, status):
        self.distroseries = distroseries
        self.status = status


class PackageUpload(SQLBase):
    """A Queue item for Lucille."""
    implements(IPackageUpload)

    _defaultOrder = ['id']

    status = EnumCol(dbName='status', unique=False, notNull=True,
                     default=PackageUploadStatus.NEW,
                     schema=PackageUploadStatus)

    distroseries = ForeignKey(dbName="distrorelease",
                               foreignKey='DistroSeries')

    pocket = EnumCol(dbName='pocket', unique=False, notNull=True,
                     schema=PackagePublishingPocket)

    # XXX: this is NULLable. Fix sampledata?
    changesfile = ForeignKey(dbName='changesfile',
                             foreignKey="LibraryFileAlias")

    archive = ForeignKey(dbName="archive", foreignKey="Archive", notNull=True)

    signing_key = ForeignKey(foreignKey='GPGKey', dbName='signing_key',
                             notNull=False)


    # Join this table to the PackageUploadBuild and the
    # PackageUploadSource objects which are related.
    sources = SQLMultipleJoin('PackageUploadSource',
                              joinColumn='packageupload')
    builds = SQLMultipleJoin('PackageUploadBuild',
                             joinColumn='packageupload')

    # Also the custom files associated with the build.
    customfiles = SQLMultipleJoin('PackageUploadCustom',
                                  joinColumn='packageupload')


    def _set_status(self, value):
        """Directly write on 'status' is forbidden.

        Force user to use the provided machine-state methods.
        Raises QueueStateWriteProtectedError.
        """
        # XXX: bug #29663: this is a bit evil, but does the job. Andrew
        # has suggested using immutable=True in the column definition.
        #   -- kiko, 2006-01-25
        # allow 'status' write only in creation process.
        if self._SO_creating:
            self._SO_set_status(value)
            return
        # been fascist
        raise QueueStateWriteProtectedError(
            'Directly write on queue status is forbidden use the '
            'provided methods to set it.')

    def setNew(self):
        """See IPackageUpload."""
        if self.status == PackageUploadStatus.NEW:
            raise QueueInconsistentStateError(
                'Queue item already new')
        self._SO_set_status(PackageUploadStatus.NEW)

    def setUnapproved(self):
        """See IPackageUpload."""
        if self.status == PackageUploadStatus.UNAPPROVED:
            raise QueueInconsistentStateError(
                'Queue item already unapproved')
        self._SO_set_status(PackageUploadStatus.UNAPPROVED)

    def setAccepted(self):
        """See IPackageUpload."""
        # Explode if something wrong like warty/RELEASE pass through
        # NascentUpload/UploadPolicies checks for 'ubuntu' main distro.
        if self.archive.id == self.distroseries.distribution.main_archive.id:
            assert self.distroseries.canUploadToPocket(self.pocket), (
                "Not permitted acceptance in the %s pocket in a "
                "series in the '%s' state." % (
                self.pocket.name, self.distroseries.status.name))

        if self.status == PackageUploadStatus.ACCEPTED:
            raise QueueInconsistentStateError(
                'Queue item already accepted')

        for source in self.sources:
            # If two queue items have the same (name, version) pair,
            # then there is an inconsistency.  Check the accepted & done
            # queue items for each distro series for such duplicates
            # and raise an exception if any are found.
            # See bug #31038 & #62976 for details.
            for distroseries in self.distroseries.distribution:
                if distroseries.getQueueItems(
                    status=[PackageUploadStatus.ACCEPTED,
                            PackageUploadStatus.DONE],
                    name=source.sourcepackagerelease.name,
                    version=source.sourcepackagerelease.version,
                    archive=self.archive, exact_match=True).count() > 0:
                    raise QueueInconsistentStateError(
                        'This sourcepackagerelease is already accepted in %s.'
                        % distroseries.name)

            # if something goes wrong we will raise an exception
            # (QueueSourceAcceptError) before setting any value.
            # Mask the error with state-machine default exception
            try:
                source.checkComponentAndSection()
            except QueueSourceAcceptError, info:
                raise QueueInconsistentStateError(info)

        for build in self.builds:
            # as before, but for QueueBuildAcceptError
            try:
                build.checkComponentAndSection()
            except QueueBuildAcceptError, info:
                raise QueueInconsistentStateError(info)

        # if the previous checks applied and pass we do set the value
        self._SO_set_status(PackageUploadStatus.ACCEPTED)

    def setDone(self):
        """See IPackageUpload."""
        if self.status == PackageUploadStatus.DONE:
            raise QueueInconsistentStateError(
                'Queue item already done')
        self._SO_set_status(PackageUploadStatus.DONE)

    def setRejected(self):
        """See IPackageUpload."""
        if self.status == PackageUploadStatus.REJECTED:
            raise QueueInconsistentStateError(
                'Queue item already rejected')
        self._SO_set_status(PackageUploadStatus.REJECTED)

    # XXX cprov 20060314: following properties should be redesigned to
    # reduce the duplicated code.
    @cachedproperty
    def containsSource(self):
        """See IPackageUpload."""
        return self.sources

    @cachedproperty
    def containsBuild(self):
        """See IPackageUpload."""
        return self.builds

    @cachedproperty
    def _customFormats(self):
        """Return the custom upload formats contained in this upload."""
        return [custom.customformat for custom in self.customfiles]

    @cachedproperty
    def containsInstaller(self):
        """See IPackageUpload."""
        return (PackageUploadCustomFormat.DEBIAN_INSTALLER
                in self._customFormats)

    @cachedproperty
    def containsTranslation(self):
        """See IPackageUpload."""
        return (PackageUploadCustomFormat.ROSETTA_TRANSLATIONS
                in self._customFormats)

    @cachedproperty
    def containsUpgrader(self):
        """See IPackageUpload."""
        return (PackageUploadCustomFormat.DIST_UPGRADER
                in self._customFormats)

    @cachedproperty
    def containsDdtp(self):
        """See IPackageUpload."""
        return (PackageUploadCustomFormat.DDTP_TARBALL
                in self._customFormats)

    @cachedproperty
    def datecreated(self):
        """See IPackageUpload."""
        return self.changesfile.content.datecreated

    @cachedproperty
    def displayname(self):
        """See IPackageUpload"""
        names = []
        for queue_source in self.sources:
            names.append(queue_source.sourcepackagerelease.name)
        for queue_build in  self.builds:
            names.append(queue_build.build.sourcepackagerelease.name)
        for queue_custom in self.customfiles:
            names.append(queue_custom.libraryfilealias.filename)
        return ",".join(names)

    @cachedproperty
    def displayarchs(self):
        """See IPackageUpload"""
        archs = []
        for queue_source in self.sources:
            archs.append('source')
        for queue_build in self.builds:
            archs.append(queue_build.build.distroarchseries.architecturetag)
        for queue_custom in self.customfiles:
            archs.append(queue_custom.customformat.title)
        return ",".join(archs)

    @cachedproperty
    def displayversion(self):
        """See IPackageUpload"""
        if self.sources:
            return self.sources[0].sourcepackagerelease.version
        if self.builds:
            return self.builds[0].build.sourcepackagerelease.version
        if self.customfiles:
            return '-'

    @cachedproperty
    def sourcepackagerelease(self):
        """The source package release related to this queue item.

        This is currently heuristic but may be more easily calculated later.
        """
        assert self.sources or self.builds, ('No source available.')
        if self.sources:
            return self.sources[0].sourcepackagerelease
        if self.builds:
            return self.builds[0].build.sourcepackagerelease

    def realiseUpload(self, logger=None):
        """See IPackageUpload."""
        assert self.status == PackageUploadStatus.ACCEPTED, (
            "Can not publish a non-ACCEPTED queue record (%s)" % self.id)
        # Explode if something wrong like warty/RELEASE pass through
        # NascentUpload/UploadPolicies checks
        if self.archive.id == self.distroseries.distribution.main_archive.id:
            assert self.distroseries.canUploadToPocket(self.pocket), (
                "Not permitted to publish to the %s pocket in a "
                "series in the '%s' state." % (
                self.pocket.name, self.distroseries.status.name))

        # In realising an upload we first load all the sources into
        # the publishing tables, then the binaries, then we attempt
        # to publish the custom objects.
        for queue_source in self.sources:
            queue_source.publish(logger)
        for queue_build in self.builds:
            queue_build.publish(logger)
        for customfile in self.customfiles:
            try:
                customfile.publish(logger)
            except CustomUploadError, e:
                logger.error("Queue item ignored: %s" % e)
                return

        self.setDone()

    def addSource(self, spr):
        """See IPackageUpload."""
        return PackageUploadSource(packageupload=self,
                            sourcepackagerelease=spr.id)

    def addBuild(self, build):
        """See IPackageUpload."""
        return PackageUploadBuild(packageupload=self,
                           build=build.id)

    def addCustom(self, library_file, custom_type):
        """See IPackageUpload."""
        return PackageUploadCustom(packageupload=self,
                            libraryfilealias=library_file.id,
                            customformat=custom_type)


class PackageUploadBuild(SQLBase):
    """A Queue item's related builds (for Lucille)."""
    implements(IPackageUploadBuild)

    _defaultOrder = ['id']

    packageupload = ForeignKey(
        dbName='packageupload',
        foreignKey='PackageUpload'
        )

    build = ForeignKey(dbName='build', foreignKey='Build')

    def checkComponentAndSection(self):
        """See IPackageUploadBuild."""
        distroseries = self.packageupload.distroseries
        for binary in self.build.binarypackages:
            if binary.component not in distroseries.components:
                raise QueueBuildAcceptError(
                    'Component "%s" is not allowed in %s'
                    % (binary.component.name, distroseries.name))
            if binary.section not in distroseries.sections:
                raise QueueBuildAcceptError(
                    'Section "%s" is not allowed in %s' % (binary.section.name,
                                                           distroseries.name))

    def publish(self, logger=None):
        """See IPackageUploadBuild."""
        # Determine the build's architecturetag
        build_archtag = self.build.distroarchseries.architecturetag
        # Determine the target arch series.
        # This will raise NotFoundError if anything odd happens.
        target_dar = self.packageupload.distroseries[build_archtag]
        debug(logger, "Publishing build to %s/%s/%s" % (
            target_dar.distroseries.distribution.name,
            target_dar.distroseries.name,
            build_archtag))
        # And get the other distroarchseriess
        other_dars = set(self.packageupload.distroseries.architectures)
        other_dars = other_dars - set([target_dar])
        # First up, publish everything in this build into that dar.
        published_binaries = []
        for binary in self.build.binarypackages:
            target_dars = set([target_dar])
            if not binary.architecturespecific:
                target_dars = target_dars.union(other_dars)
                debug(logger, "... %s/%s (Arch Independent)" % (
                    binary.binarypackagename.name,
                    binary.version))
            else:
                debug(logger, "... %s/%s (Arch Specific)" % (
                    binary.binarypackagename.name,
                    binary.version))
            for each_target_dar in target_dars:
                # XXX: dsilvers: 20051020: What do we do about embargoed
                # binaries here? bug 3408
                sbpph = SecureBinaryPackagePublishingHistory(
                    binarypackagerelease=binary,
                    distroarchseries=each_target_dar,
                    component=binary.component,
                    section=binary.section,
                    priority=binary.priority,
                    status=PackagePublishingStatus.PENDING,
                    datecreated=UTC_NOW,
                    pocket=self.packageupload.pocket,
                    embargo=False,
                    archive=self.packageupload.archive
                    )
                published_binaries.append(sbpph)
        return published_binaries


class PackageUploadSource(SQLBase):
    """A Queue item's related sourcepackagereleases (for Lucille)."""
    implements(IPackageUploadSource)

    _defaultOrder = ['id']

    packageupload = ForeignKey(
        dbName='packageupload',
        foreignKey='PackageUpload'
        )

    sourcepackagerelease = ForeignKey(
        dbName='sourcepackagerelease',
        foreignKey='SourcePackageRelease'
        )

    def checkComponentAndSection(self):
        """See IPackageUploadSource."""
        distroseries = self.packageupload.distroseries
        component = self.sourcepackagerelease.component
        section = self.sourcepackagerelease.section

        if component not in distroseries.components:
            raise QueueSourceAcceptError(
                'Component "%s" is not allowed in %s' % (component.name,
                                                         distroseries.name))

        if section not in distroseries.sections:
            raise QueueSourceAcceptError(
                'Section "%s" is not allowed in %s' % (section.name,
                                                       distroseries.name))

    def publish(self, logger=None):
        """See IPackageUploadSource."""
        # Publish myself in the distroseries pointed at by my queue item.
        # XXX: dsilvers: 20051020: What do we do here to support embargoed
        # sources? bug 3408
        debug(logger, "Publishing source %s/%s to %s/%s" % (
            self.sourcepackagerelease.name,
            self.sourcepackagerelease.version,
            self.packageupload.distroseries.distribution.name,
            self.packageupload.distroseries.name))

        return SecureSourcePackagePublishingHistory(
            distroseries=self.packageupload.distroseries,
            sourcepackagerelease=self.sourcepackagerelease,
            component=self.sourcepackagerelease.component,
            section=self.sourcepackagerelease.section,
            status=PackagePublishingStatus.PENDING,
            datecreated=UTC_NOW,
            pocket=self.packageupload.pocket,
            embargo=False,
            archive=self.packageupload.archive)


class PackageUploadCustom(SQLBase):
    """A Queue item's related custom format uploads."""
    implements(IPackageUploadCustom)

    _defaultOrder = ['id']

    packageupload = ForeignKey(
        dbName='packageupload',
        foreignKey='PackageUpload'
        )

    customformat = EnumCol(dbName='customformat', unique=False,
                           notNull=True, schema=PackageUploadCustomFormat)

    libraryfilealias = ForeignKey(dbName='libraryfilealias',
                                  foreignKey="LibraryFileAlias",
                                  notNull=True)

    def publish(self, logger=None):
        """See IPackageUploadCustom."""
        # This is a marker as per the comment in dbschema.py.
        ##CUSTOMFORMAT##
        # Essentially, if you alter anything to do with what custom formats
        # are, what their tags are, or anything along those lines, you should
        # grep for the marker in the source tree and fix it up in every place
        # so marked.
        debug(logger, "Publishing custom %s to %s/%s" % (
            self.packageupload.displayname,
            self.packageupload.distroseries.distribution.name,
            self.packageupload.distroseries.name))

        name = "publish_" + self.customformat.name
        method = getattr(self, name, None)
        if method is not None:
            method(logger)
        else:
            raise NotFoundError("Unable to find a publisher method for %s" % (
                self.customformat.name))

    def temp_filename(self):
        """See IPackageUploadCustom."""
        temp_dir = tempfile.mkdtemp()
        temp_file_name = os.path.join(temp_dir, self.libraryfilealias.filename)
        temp_file = file(temp_file_name, "wb")
        self.libraryfilealias.open()
        copy_and_close(self.libraryfilealias, temp_file)
        return temp_file_name

    @property
    def archive_config(self):
        """See IPackageUploadCustom."""
        distribution = self.packageupload.distroseries.distribution
        archive = self.packageupload.archive
        return archive.getPubConfig(distribution)

    def _publishCustom(self, action_method):
        """Publish custom formats.

        Publish Either an installer, an upgrader or a ddtp upload using the
        supplied action method.
        """
        temp_filename = self.temp_filename()
        full_suite_name = "%s%s" % (
            self.packageupload.distroseries.name,
            pocketsuffix[self.packageupload.pocket])
        try:
            action_method(
                self.archive_config.archiveroot, temp_filename,
                full_suite_name)
        finally:
            shutil.rmtree(os.path.dirname(temp_filename))

    def publish_DEBIAN_INSTALLER(self, logger=None):
        """See IPackageUploadCustom."""
        # XXX cprov 20050303: We need to use the Zope Component Lookup
        # to instantiate the object in question and avoid circular imports
        from canonical.archivepublisher.debian_installer import (
            process_debian_installer)

        self._publishCustom(process_debian_installer)

    def publish_DIST_UPGRADER(self, logger=None):
        """See IPackageUploadCustom."""
        # XXX cprov 20050303: We need to use the Zope Component Lookup
        # to instantiate the object in question and avoid circular imports
        from canonical.archivepublisher.dist_upgrader import (
            process_dist_upgrader)

        self._publishCustom(process_dist_upgrader)

    def publish_DDTP_TARBALL(self, logger=None):
        """See IPackageUploadCustom."""
        # XXX cprov 20050303: We need to use the Zope Component Lookup
        # to instantiate the object in question and avoid circular imports
        from canonical.archivepublisher.ddtp_tarball import (
            process_ddtp_tarball)

        self._publishCustom(process_ddtp_tarball)

    def publish_ROSETTA_TRANSLATIONS(self, logger=None):
        """See IPackageUploadCustom."""
        # XXX: dsilvers: 20051115: We should be able to get a
        # sourcepackagerelease directly.
        sourcepackagerelease = (
            self.packageupload.builds[0].build.sourcepackagerelease)

        # Ignore translation coming from PPA.
        target_archive = self.packageupload.archive
        main_archive = self.packageupload.distroseries.main_archive
        if target_archive.id != main_archive.id:
            debug(logger, "Skipping translations since it is a PPA.")
            return

        valid_pockets = (
            PackagePublishingPocket.RELEASE, PackagePublishingPocket.SECURITY,
            PackagePublishingPocket.UPDATES, PackagePublishingPocket.PROPOSED)
        if (self.packageupload.pocket not in valid_pockets or
            sourcepackagerelease.component.name != 'main'):
            # XXX: CarlosPerelloMarin 20060216 This should be implemented
            # using a more general rule to accept different policies depending
            # on the distribution. See bug #31665 for more details.
            # Ubuntu's MOTU told us that they are not able to handle
            # translations like we do in main. We are going to import only
            # packages in main.
            return

        # Attach the translation tarball. It's always published.
        try:
            sourcepackagerelease.attachTranslationFiles(
                self.libraryfilealias, True)
        except DownloadFailed:
            if logger is not None:
                debug(logger, "Unable to fetch %s to import it into Rosetta" %
                    self.libraryfilealias.http_url)


class PackageUploadSet:
    """See IPackageUploadSet"""
    implements(IPackageUploadSet)

    def __iter__(self):
        """See IPackageUploadSet."""
        return iter(PackageUpload.select())

    def __getitem__(self, queue_id):
        """See IPackageUploadSet."""
        try:
            return PackageUpload.get(queue_id)
        except SQLObjectNotFound:
            raise NotFoundError(queue_id)

    def get(self, queue_id):
        """See IPackageUploadSet."""
        try:
            return PackageUpload.get(queue_id)
        except SQLObjectNotFound:
            raise NotFoundError(queue_id)

    def count(self, status=None, distroseries=None, pocket=None):
        """See IPackageUploadSet."""
        clauses = []
        if status:
            clauses.append("status=%s" % sqlvalues(status))

        if distroseries:
            clauses.append("distrorelease=%s" % sqlvalues(distroseries))

        if pocket:
            clauses.append("pocket=%s" % sqlvalues(pocket))

        query = " AND ".join(clauses)
        return PackageUpload.select(query).count()
