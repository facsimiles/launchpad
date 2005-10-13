# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""Database classes for a distribution release."""

__metaclass__ = type

__all__ = [
    'DistroRelease',
    'DistroReleaseSet',
    ]

from zope.interface import implements
from zope.component import getUtility

from sqlobject import StringCol, ForeignKey, MultipleJoin, IntCol

from canonical.database.sqlbase import SQLBase, sqlvalues
from canonical.database.datetimecol import UtcDateTimeCol
from canonical.lp.dbschema import (
    PackagePublishingStatus, BugTaskStatus, EnumCol, DistributionReleaseStatus)

from canonical.launchpad.interfaces import (
    IDistroRelease, IDistroReleaseSet, ISourcePackageName,
    IPublishedPackageSet, IHasBuildRecords, NotFoundError)

from canonical.launchpad.database.sourcepackageindistro import (
    SourcePackageInDistro)
from canonical.launchpad.database.publishing import (
    BinaryPackagePublishing, SourcePackagePublishing)
from canonical.launchpad.database.distroarchrelease import DistroArchRelease
from canonical.launchpad.database.potemplate import POTemplate
from canonical.launchpad.database.language import Language
from canonical.launchpad.database.distroreleaselanguage import (
    DistroReleaseLanguage, DummyDistroReleaseLanguage)
from canonical.launchpad.database.sourcepackage import SourcePackage
from canonical.launchpad.database.sourcepackagename import (
    SourcePackageName, SourcePackageNameSet)
from canonical.launchpad.database.packaging import Packaging
from canonical.launchpad.database.build import Build
from canonical.launchpad.database.bugtask import BugTaskSet, BugTask
from canonical.launchpad.database.binarypackagerelease import (
        BinaryPackageRelease)
from canonical.launchpad.helpers import shortlist


class DistroRelease(SQLBase):
    """A particular release of a distribution."""
    implements(IDistroRelease, IHasBuildRecords)

    _table = 'DistroRelease'
    _defaultOrder = ['distribution', 'version']

    distribution = ForeignKey(dbName='distribution',
                              foreignKey='Distribution', notNull=True)
    bugtasks = MultipleJoin('BugTask', joinColumn='distrorelease')
    name = StringCol(notNull=True)
    displayname = StringCol(notNull=True)
    title = StringCol(notNull=True)
    summary = StringCol(notNull=True)
    description = StringCol(notNull=True)
    version = StringCol(notNull=True)
    components = ForeignKey(
        dbName='components', foreignKey='Schema', notNull=True)
    sections = ForeignKey(
        dbName='sections', foreignKey='Schema', notNull=True)
    releasestatus = EnumCol(notNull=True, schema=DistributionReleaseStatus)
    datereleased = UtcDateTimeCol(notNull=False, default=None)
    parentrelease =  ForeignKey(
        dbName='parentrelease', foreignKey='DistroRelease', notNull=False)
    owner = ForeignKey(
        dbName='owner', foreignKey='Person', notNull=True)
    lucilleconfig = StringCol(notNull=False, default=None)
    changeslist = StringCol(notNull=False, default=None)
    architectures = MultipleJoin(
        'DistroArchRelease', joinColumn='distrorelease',
        orderBy='architecturetag')
    nominatedarchindep = ForeignKey(
        dbName='nominatedarchindep',foreignKey='DistroArchRelease',
        notNull=False, default=None)
    specifications = MultipleJoin('Specification',
        joinColumn='distrorelease', orderBy='-datecreated')
    datelastlangpack = UtcDateTimeCol(dbName='datelastlangpack', notNull=False,
                                   default=None)
    messagecount = IntCol(notNull=True, default=0)

    @property
    def packagings(self):
        packagings = list(Packaging.selectBy(distroreleaseID=self.id))
        packagings.sort(key=lambda a:a.sourcepackagename.name)
        return packagings

    @property
    def distroreleaselanguages(self):
        result = DistroReleaseLanguage.selectBy(distroreleaseID=self.id)
        return sorted(result, key=lambda a: a.language.englishname)

    @property
    def translatable_sourcepackages(self):
        """See IDistroRelease."""
        result = SourcePackageName.select("""
            POTemplate.sourcepackagename = SourcePackageName.id AND
            POTemplate.distrorelease = %s
            """ % sqlvalues(self.id),
            clauseTables=['POTemplate'],
            orderBy=['name'])
        return [SourcePackage(sourcepackagename=spn, distrorelease=self) for
            spn in result]

    @property
    def previous_releases(self):
        """See IDistroRelease."""
        datereleased = self.datereleased
        # if this one is unreleased, use the last released one
        if not datereleased:
            datereleased = 'NOW'
        return DistroRelease.select('''
                distribution = %s AND 
                datereleased < %s
                ''' % sqlvalues(self.distribution.id, datereleased),
                orderBy=['-datereleased'])

    @property
    def parent(self):
        """See IDistroRelease."""
        if self.parentrelease:
            return self.parentrelease.title
        return ''

    @property
    def status(self):
        return self.releasestatus.title

    @property
    def sourcecount(self):
        query = ('SourcePackagePublishing.status = %s '
                 'AND SourcePackagePublishing.distrorelease = %s'
                 % sqlvalues(PackagePublishingStatus.PUBLISHED, self.id))
        return SourcePackagePublishing.select(query).count()

    @property
    def binarycount(self):
        """See IDistroRelease."""
        clauseTables = ['DistroArchRelease']
        query = ('BinaryPackagePublishing.status = %s '
                 'AND BinaryPackagePublishing.distroarchrelease = '
                 'DistroArchRelease.id '
                 'AND DistroArchRelease.distrorelease = %s'
                 % sqlvalues(PackagePublishingStatus.PUBLISHED, self.id))
        return BinaryPackagePublishing.select(
            query, clauseTables=clauseTables).count()

    @property
    def architecturecount(self):
        """See IDistroRelease."""
        return len(list(self.architectures))

    @property
    def potemplates(self):
        result = POTemplate.selectBy(distroreleaseID=self.id)
        result = list(result)
        return sorted(result, key=lambda x: x.potemplatename.name)

    @property
    def currentpotemplates(self):
        result = POTemplate.selectBy(distroreleaseID=self.id, iscurrent=True)
        result = list(result)
        return sorted(result, key=lambda x: x.potemplatename.name)

    @property
    def fullreleasename(self):
        return "%s %s" % (
            self.distribution.name.capitalize(), self.name.capitalize())

    def searchTasks(self, search_params):
        """See canonical.launchpad.interfaces.IBugTarget."""
        search_params.setDistributionRelease(self)
        return BugTaskSet().search(search_params)

    def getSpecification(self, name):
        """See ISpecificationTarget."""
        return self.distribution.getSpecification(name)

    def getBugSourcePackages(self):
        """See IDistroRelease."""
        query = ("VSourcePackageInDistro.distrorelease = %i AND "
                 "VSourcePackageInDistro.distro = BugTask.distribution AND "
                 "VSourcePackageInDistro.name = BugTask.sourcepackagename AND "
                 "(BugTask.status != %i OR BugTask.status != %i)"
                 % sqlvalues(
                    self.id, BugTaskStatus.FIXED, BugTaskStatus.REJECTED))

        return SourcePackageInDistro.select(
            query, clauseTables=["BugTask"], distinct=True)

    @property
    def open_cve_bugtasks(self):
        """See IDistroRelease."""
        result = BugTask.select("""
            CVE.id = BugCve.cve AND
            BugCve.bug = Bug.id AND
            BugTask.bug = Bug.id AND
            BugTask.distrorelease=%s AND
            BugTask.status IN (%s, %s)
            """ % sqlvalues(
                self.id,
                BugTaskStatus.NEW,
                BugTaskStatus.ACCEPTED),
            clauseTables=['Bug', 'Cve', 'BugCve'],
            orderBy=['-severity', 'datecreated'])
        return result

    @property
    def resolved_cve_bugtasks(self):
        """See IDistroRelease."""
        result = BugTask.select("""
            CVE.id = BugCve.cve AND
            BugCve.bug = Bug.id AND
            BugTask.bug = Bug.id AND
            BugTask.distrorelease=%s AND
            BugTask.status IN (%s, %s, %s)
            """ % sqlvalues(
                self.id,
                BugTaskStatus.REJECTED,
                BugTaskStatus.FIXED,
                BugTaskStatus.PENDINGUPLOAD),
            clauseTables=['Bug', 'Cve', 'BugCve'],
            orderBy=['-severity', 'datecreated'])
        return result

    def getDistroReleaseLanguage(self, language):
        """See IDistroRelease."""
        return DistroReleaseLanguage.selectOneBy(
            distroreleaseID=self.id,
            languageID=language.id)

    def getDistroReleaseLanguageOrDummy(self, language):
        """See IDistroRelease."""
        drl = self.getDistroReleaseLanguage(language)
        if drl is not None:
            return drl
        return DummyDistroReleaseLanguage(self, language)

    def updateStatistics(self, ztm):
        """See IDistroRelease."""
        # first find the set of all languages for which we have pofiles in
        # the distribution
        langidset = set([
            language.id for language in Language.select('''
                Language.id = POFile.language AND
                POFile.potemplate = POTemplate.id AND
                POTemplate.distrorelease = %s
                ''' % sqlvalues(self.id),
                orderBy=['code'],
                distinct=True,
                clauseTables=['POFile', 'POTemplate'])
            ])
        # now run through the existing DistroReleaseLanguages for the
        # distrorelease, and update their stats, and remove them from the
        # list of languages we need to have stats for
        for distroreleaselanguage in self.distroreleaselanguages:
            distroreleaselanguage.updateStatistics(ztm)
            langidset.discard(distroreleaselanguage.language.id)
        # now we should have a set of languages for which we NEED
        # to have a DistroReleaseLanguage
        for langid in langidset:
            drl = DistroReleaseLanguage(distrorelease=self, languageID=langid)
            drl.updateStatistics(ztm)
        # lastly, we need to update the message count for this distro
        # release itself
        messagecount = 0
        for potemplate in self.potemplates:
            messagecount += potemplate.messageCount()
        self.messagecount = messagecount
        ztm.commit()


    def findSourcesByName(self, pattern):
        """Get SourcePackages in a DistroRelease"""        
        # XXX: Daniel Debonzi 20050711
        # Implement it as soon as SourcePackageSet issue are sorted out.
        raise NotImplemented

    def getSourcePackageByName(self, name):
        """See IDistroRelease."""
        if not ISourcePackageName.providedBy(name):
            name_set = SourcePackageNameSet()

            try:
                name = name_set[name]
            except IndexError:
                raise ValueError('No such source package name %r' % name)

        return SourcePackage(sourcepackagename=name, distrorelease=self)

    def __getitem__(self, arch):
        """Get SourcePackages in a DistroRelease with BugTask"""
        item = DistroArchRelease.selectOneBy(
            distroreleaseID=self.id, architecturetag=arch)
        if item is None:
            raise NotFoundError('Unknown architecture %s for %s %s' % (
                arch, self.distribution.name, self.name))
        return item

    def getPublishedReleases(self, sourcepackage_or_name):
        """See IDistroRelease."""
        if ISourcePackageName.providedBy(sourcepackage_or_name):
            sourcepackage = sourcepackage_or_name
        else:
            sourcepackage = sourcepackage_or_name.name
        published = SourcePackagePublishing.select(
            """
            distrorelease = %s AND
            status = %s AND
            sourcepackagerelease = sourcepackagerelease.id AND
            sourcepackagerelease.sourcepackagename = %s
            """ % sqlvalues(self.id,
                            PackagePublishingStatus.PUBLISHED,
                            sourcepackage.id),
            clauseTables = ['SourcePackageRelease'])
        return shortlist(published)

    def publishedBinaryPackages(self, component=None):
        """See IDistroRelease."""
        # XXX sabdfl 04/07/05 this can become a utility when that works
        # this is used by the debbugs import process, mkdebwatches
        pubpkgset = getUtility(IPublishedPackageSet)
        result = pubpkgset.query(distrorelease=self, component=component)
        return [BinaryPackageRelease.get(pubrecord.binarypackagerelease)
                for pubrecord in result]

    def getWorkedBuildRecords(self, status=None, limit=10):
        """See IHasBuildRecords"""
        # find out the distroarchrelease in question
        arch_ids = ','.join(
            '%d' % arch.id for arch in self.architectures)

        # if no distroarchrelease was found return None
        if not arch_ids:
            return None

        # specific status or simply worked 
        if status:
            status_clause = "buildstate=%s" % sqlvalues(status)
        else:
            status_clause = "builder is not NULL"

        return Build.select(
            "distroarchrelease IN (%s) AND %s" % (arch_ids, status_clause),
            limit=limit, orderBy="-datebuilt")

class DistroReleaseSet:
    implements(IDistroReleaseSet)

    def get(self, distroreleaseid):
        """See IDistroReleaseSet."""
        return DistroRelease.get(distroreleaseid)

    def translatables(self):
        """See IDistroReleaseSet."""
        return DistroRelease.select(
            "POTemplate.distrorelease=DistroRelease.id",
            clauseTables=['POTemplate'], distinct=True)

    def findByName(self, name):
        """See IDistroReleaseSet."""
        return DistroRelease.selectBy(name=name)

    def queryByName(self, distribution, name):
        """See IDistroReleaseSet."""
        return DistroRelease.selectOneBy(
            distributionID=distribution.id, name=name)

    def findByVersion(self, version):
        """See IDistroReleaseSet."""
        return DistroRelease.selectBy(version=version)

    def search(self, distribution=None, isreleased=None, orderBy=None):
        """See IDistroReleaseSet."""
        where_clause = ""
        if distribution is not None:
            where_clause += "distribution = %s" % sqlvalues(distribution.id)
        if isreleased is not None:
            if where_clause:
                where_clause += " AND "
            if isreleased:
                # The query is filtered on released releases.
                where_clause += "releasestatus in (%s, %s)" % sqlvalues(
                    DistributionReleaseStatus.CURRENT,
                    DistributionReleaseStatus.SUPPORTED)
            else:
                # The query is filtered on unreleased releases.
                where_clause += "releasestatus in (%s, %s, %s)" % sqlvalues(
                    DistributionReleaseStatus.EXPERIMENTAL,
                    DistributionReleaseStatus.DEVELOPMENT,
                    DistributionReleaseStatus.FROZEN)
        if orderBy is not None:
            return DistroRelease.select(where_clause, orderBy=orderBy)
        else:
            return DistroRelease.select(where_clause)

    def new(self, distribution, name, displayname, title, summary, description,
            version, components, sections, parentrelease, owner):
        """See IDistroReleaseSet."""
        return DistroRelease(
            distribution = distribution,
            name = name, 
            displayname = displayname, 
            title = title, 
            summary = summary,
            description = description,
            version = version,
            components = components,
            sections = sections,
            releasestatus = DistributionReleaseStatus.EXPERIMENTAL,
            parentrelease =  parentrelease,
            owner = owner)

