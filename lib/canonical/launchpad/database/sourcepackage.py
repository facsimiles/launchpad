# Python imports
from sets import Set
from datetime import datetime

# Zope imports
from zope.interface import implements

# SQLObject/SQLBase
from sqlobject import MultipleJoin, RelatedJoin, AND, LIKE
from sqlobject import StringCol, ForeignKey, IntCol, MultipleJoin, BoolCol, \
                      DateTimeCol

from canonical.database.sqlbase import SQLBase, quote
from canonical.lp import dbschema

# interfaces and database 
from canonical.launchpad.interfaces import ISourcePackageRelease, \
                                           ISourcePackage, \
                                           ISourcePackageName, \
                                           ISourcePackageContainer

from canonical.launchpad.database.product import Product
from canonical.launchpad.database.binarypackage import BinaryPackage


class SourcePackage(SQLBase):
    """A source package, e.g. apache2."""
    implements(ISourcePackage)
    _table = 'SourcePackage'

    #
    # Columns
    #
    shortdesc   = StringCol(dbName='shortdesc', notNull=True)
    description = StringCol(dbName='description', notNull=True)

    distro            = ForeignKey(foreignKey='Distribution', dbName='distro')
    manifest          = ForeignKey(foreignKey='Manifest', dbName='manifest')
    maintainer        = ForeignKey(foreignKey='Person', dbName='maintainer', 
                                   notNull=True)
    sourcepackagename = ForeignKey(foreignKey='SourcePackageName',
                                   dbName='sourcepackagename', notNull=True)

    releases              = MultipleJoin('SourcePackageRelease', 
                                         joinColumn='sourcepackage')
    bugs                  = MultipleJoin('SourcePackageBugAssignment', 
                                         joinColumn='sourcepackage')
    sourcepackagereleases = MultipleJoin('SourcePackageRelease', 
                                         joinColumn='sourcepackage')

    #
    # Properties
    #
    def name(self):
        return self.sourcepackagename.name

    name = property(name)

    def product(self):
        try:
            clauseTables = ('Packaging', 'Product')
            return Product.select("Product.id = Packaging.product AND "
                                  "Packaging.sourcepackage = %d"
                                  % self.id, clauseTables=clauseTables)[0]
        except IndexError:
            # No corresponding product
            return None

    product = property(product)

    #
    # Methods
    #
    def bugsCounter(self):
        # XXXkiko: move to bugassignment?
        from canonical.launchpad.database.bugassignment import \
            SourcePackageBugAssignment

        ret = [len(self.bugs)]

        get = SourcePackageBugAssignment.selectBy
        severities = [
            dbschema.BugSeverity.CRITICAL,
            dbschema.BugSeverity.MAJOR,
            dbschema.BugSeverity.NORMAL,
            dbschema.BugSeverity.MINOR,
            dbschema.BugSeverity.WISHLIST,
            dbschema.BugAssignmentStatus.CLOSED,
            dbschema.BugAssignmentStatus.OPEN,
        ]
        for severity in severities:
            n = get(severity=int(severity), sourcepackageID=self.id).count()
            ret.append(n)
        return ret

    def getRelease(self, version):
        ret = list(SourcePackageRelease.selectBy(version=version))
        assert len(ret) == 1
        return ret[0]

    def uploadsByStatus(self, distroRelease, status, do_sort=False):
        query = (' distrorelease = %d '
                 ' AND sourcepackage = %d'
                 ' AND publishingstatus = %d'
                 % (distroRelease.id, self.id, status))
        if do_sort:
            query += ' ORDER BY dateuploaded DESC'
        ret = SourcePackageRelease.select(query)
        return ret

    def proposed(self, distroRelease):
        return self.uploadsByStatus(distroRelease,
                                    dbschema.PackagePublishingStatus.PROPOSED)

    def current(self, distroRelease):
        """Currently published releases of this package for a given distro.
        
        :returns: iterable of SourcePackageReleases
        """
        return self.uploadsByStatus(distroRelease, 
                                    dbschema.PackagePublishingStatus.PUBLISHED)

    def lastversions(self, distroRelease):
        return self.uploadsByStatus(distroRelease, 
                                    dbschema.PackagePublishingStatus.SUPERCEDED,
                                    do_sort=True)


class SourcePackageInDistro(SourcePackage):
    """
    Represents source packages that have releases published in the
    specified distribution. This view's contents are uniqued, for the
    following reason: a certain package can have multiple releases in a
    certain distribution release.
    """
    _table = 'VSourcePackageInDistro'
   
    #
    # Columns
    #
    name = StringCol(dbName='name', notNull=True)

    #
    # Class Methods
    #
    def getByName(klass, distrorelease, name):
        """Get A SourcePackageRelease in a distrorelease by its name"""
        ret = klass.getReleases(distrorelease, name)
        assert len(list(ret)) == 1
        return ret[0]

    getByName = classmethod(getByName)

    def getReleases(klass, distrorelease, name=None):
        """
        Answers the question: what source packages have releases
        published in the specified distribution (optionally named)
        """
        query = 'distrorelease = %d ' \
                % distrorelease.id
        if name is not None:
            query += ' AND name = %s' % quote(name)
        return klass.select(query, orderBy='name')

    getReleases = classmethod(getReleases)

    def getByPersonID(klass, personID):
        # XXXkiko: we should allow supplying a distrorelease here and
        # get packages by distro
        return klass.select("maintainer = %d" % personID, orderBy='name')

    getByPersonID = classmethod(getByPersonID)

    def findSourcesByName(klass, distroRelease, pattern):
        """Search for SourcePackages in a distrorelease that matches"""
        pattern = quote("%%" + pattern.replace('%', '%%') + "%%")
        query = ('distrorelease = %d AND '
                 '(name ILIKE %s OR shortdesc ILIKE %s)' %
                 (distroRelease.id, pattern, pattern))
        return SourcePackageRelease.select(query, orderBy='name')

    findSourcesByName = classmethod(findSourcesByName)


class SourcePackageContainer(object):
    """A container for SourcePackage objects."""

    implements(ISourcePackageContainer)
    table = SourcePackage

    #
    # We need to return a SourcePackage given a name. For phase 1 (warty)
    # we can assume that there is only one package with a given name, but
    # later (XXX) we will have to deal with multiple source packages with
    # the same name.
    #
    def __getitem__(self, name):
        clauseTables = ('SourcePackageName', 'SourcePackage')
        return self.table.select("SourcePackage.sourcepackagename = \
        SourcePackageName.id AND SourcePackageName.name = %s" %     \
        quote(name))[0]

    def __iter__(self):
        for row in self.table.select():
            yield row

    def withBugs(self):
        pkgset = Set()
        results = self.table.select("SourcePackage.id = \
                                     SourcePackageBugAssignment.sourcepackage")
        for pkg in results:
            pkgset.add(pkg)
        return pkgset


class SourcePackageName(SQLBase):
    implements(ISourcePackageName)
    _table = 'SourcePackageName'

    name = StringCol(dbName='name', notNull=True)


class SourcePackageRelease(SQLBase):
    implements(ISourcePackageRelease)
    _table = 'VSourcePackageReleasePublishing'
  
    #
    # Columns
    #
    # XXXkiko: IDs in this table are *NOT* unique!
    # XXXkiko: clean up notNulls
    status = IntCol(dbName='publishingstatus', notNull=True)
    urgency = IntCol(dbName='urgency', notNull=True)

    name              = StringCol(dbName='name', notNull=True)
    # XXXkiko: move to property
    changelog         = StringCol(dbName='changelog')
    shortdesc         = StringCol(dbName='shortdesc', notNull=True)
    description       = StringCol(dbName='description', notNull=True)
    version           = StringCol(dbName='version', notNull=True)
    componentname     = StringCol(dbName='componentname', notNull=True)
    componenttitle    = StringCol(dbName='componenttitle', notNull=True)
    componentdesc     = StringCol(dbName='componentdesc', notNull=True)
    builddepends      = StringCol(dbName='builddepends')
    builddependsindep = StringCol(dbName='builddependsindep')

    dateuploaded   = DateTimeCol(dbName='dateuploaded', notNull=True,
                                 default='NOW')

    creator       = ForeignKey(foreignKey='Person', dbName='creator')
    maintainer    = ForeignKey(foreignKey='Person', dbName='maintainer')
    # XXXkiko: remove in lieu of expanded crap
    component     = ForeignKey(foreignKey='Component', dbName='component')
    section       = ForeignKey(foreignKey='Section', dbName='section')
    distrorelease = ForeignKey(foreignKey='DistroRelease', dbName='distrorelease')
    sourcepackage = ForeignKey(foreignKey='SourcePackage', dbName='sourcepackage')

    builds = MultipleJoin('Build', joinColumn='sourcepackagerelease')

    #
    # Properties
    #
    def _urgency(self):
        for urgency in dbschema.SourcePackageUrgency.items:
            if urgency.value == self.urgency:
                return urgency.title
        return 'Unknown (%d)' %self.urgency

    def binaries(self):
        clauseTables = ('SourcePackageRelease', 'BinaryPackage', 'Build')
        
        query = ('SourcePackageRelease.id = Build.sourcepackagerelease'
                 ' AND BinaryPackage.build = Build.id '
                 ' AND Build.sourcepackagerelease = %i' % self.id)

        return BinaryPackage.select(query, clauseTables=clauseTables)
        
    binaries = property(binaries)

    pkgurgency = property(_urgency)

    #
    # Methods
    #
    def architecturesReleased(self, distroRelease):
        # The import is here to avoid a circular import. See top of module.
        from canonical.launchpad.database.distro import DistroArchRelease
        clauseTables = ('PackagePublishing', 'BinaryPackage', 'Build')
        
        archReleases = Set(DistroArchRelease.select(
            'PackagePublishing.distroarchrelease = DistroArchRelease.id '
            'AND DistroArchRelease.distrorelease = %d '
            'AND PackagePublishing.binarypackage = BinaryPackage.id '
            'AND BinaryPackage.build = Build.id '
            'AND Build.sourcepackagerelease = %d'
            % (distroRelease.id, self.id), clauseTables=clauseTables))
        return archReleases

    #
    # Class Methods
    #
    def selectByVersion(klass, sourcereleases, version):
        """Select from SourcePackageRelease.SelectResult that have
        version=version"""
        
        query = sourcereleases.clause + \
                ' AND version = %s' % quote(version)

        return klass.select(query)

    selectByVersion = classmethod(selectByVersion)

    def selectByBinaryVersion(klass, sourcereleases, version):
        """Select from SourcePackageRelease.SelectResult that have
        BinaryPackage.version=version"""
        query = sourcereleases.clause + \
                '''AND Build.id = BinaryPackage.build
                   AND Build.sourcepackagerelease = 
                       VSourcePackageReleasePublishing.id
                   AND BinaryPackage.version = %s''' % quote(version)
        return klass.select(query)

    selectByBinaryVersion = classmethod(selectByBinaryVersion)



# XXX Mark Shuttleworth: this is somewhat misleading as there
# will likely be several versions of a source package with the
# same name, please consider getSourcePackages() 21/10/04
def getSourcePackage(name):
    return SourcePackage.selectBy(name=name)


def createSourcePackage(name, maintainer=0):
    # FIXME: maintainer=0 is a hack.  It should be required (or the DB shouldn't
    #        have NOT NULL on that column).
    return SourcePackage(
        name=name, 
        maintainer=maintainer,
        title='', # FIXME
        description='', # FIXME
    )

