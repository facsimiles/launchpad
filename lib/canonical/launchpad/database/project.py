"""Launchpad Project-related Database Table Objects

Part of the Launchpad system.

(c) 2004 Canonical, Ltd.
"""

# Zope
from zope.interface import implements

# SQL object
from sqlobject import DateTimeCol, ForeignKey, StringCol, BoolCol
from sqlobject import MultipleJoin, RelatedJoin, AND, LIKE
from canonical.database.sqlbase import SQLBase, quote

# Launchpad interfaces
from canonical.launchpad.interfaces import IProject, IProjectSet, \
                                           IProjectBugTracker

# Import needed database objects
from canonical.lp.dbschema import ImportStatus
from canonical.launchpad.database.product import Product

from sets import Set

class Project(SQLBase):
    """A Project"""

    implements(IProject)

    _table = "Project"

    # db field names
    owner= ForeignKey(foreignKey='Person', dbName='owner', notNull=True)
    name = StringCol(dbName='name', notNull=True)
    displayname = StringCol(dbName='displayname', notNull=True)
    title = StringCol(dbName='title', notNull=True)
    shortdesc = StringCol(dbName='shortdesc', notNull=True)
    description = StringCol(dbName='description', notNull=True)
    # XXX: https://bugzilla.warthogs.hbd.com/bugzilla/show_bug.cgi?id=1968
    datecreated = DateTimeCol(dbName='datecreated', notNull=True)
    homepageurl = StringCol(dbName='homepageurl', notNull=False, default=None)
    wikiurl = StringCol(dbName='wikiurl', notNull=False, default=None)
    lastdoap = StringCol(dbName='lastdoap', notNull=False, default=None)
    active = BoolCol(dbName='active', notNull=True, default=True)
    reviewed = BoolCol(dbName='reviewed', notNull=True, default=False)

    # convenient joins

    bounties = RelatedJoin('Bounty', joinColumn='project',
                            otherColumn='bounty',
                            intermediateTable='ProjectBounty')

    products = MultipleJoin('Product', joinColumn='project')

    bugtrackers = RelatedJoin('BugTracker', joinColumn='project',
                               otherColumn='bugtracker',
                               intermediateTable='ProjectBugTracker')

    def getProduct(self, name):
        try:
            return Product.selectBy(projectID=self.id, name=name)[0]
        except IndexError:
            return None


class ProjectSet:
    implements(IProjectSet)

    def __init__(self):
        self.title = 'Open Source Projects in the Launchpad'

    def __iter__(self):
        return iter(Project.select())

    def __getitem__(self, name):
        ret = Project.selectBy(name=name)

        if ret.count() == 0:
            raise KeyError, name
        else:
            return ret[0]

    def new(self, name, displayname, title, homepageurl, shortdesc, 
            description, owner):
        name = name.encode('ascii')
        displayname = displayname.encode('ascii')
        title = title.encode('ascii')
        if type(url) != NoneType:
            url = url.encode('ascii')
        description = description.encode('ascii')

        if Project.selectBy(name=name).count():
            raise KeyError, "There is already a project with that name"

        return Project(name = name,
                       displayname = displayname,
                       title = title,
                       shortdesc = shortdesc,
                       description = description,
                       homepageurl = url,
                       owner = owner,
                       datecreated = 'now')

    def forReview(self):
        return Project.select("reviewed IS FALSE")


    def forSyncReview(self):
        query = """Product.project=Project.id AND
                   Product.reviewed IS TRUE AND
                   Product.active IS TRUE AND
                   Product.id=ProductSeries.product AND
                   ProductSeries.importstatus IS NOT NULL AND
                   ProductSeries.importstatus <> %d
                   """ % ImportStatus.SYNCING
        clauseTables = ['Project', 'Product', 'ProductSeries']
        results = []
        for project in Project.select(query, clauseTables=clauseTables):
            if project not in results:
                results.append(project)
        return results


    def search(self, text=None, soyuz=None,
                     rosetta=None, malone=None,
                     bazaar=None,
                     search_products=True,
                     show_inactive=False):
        """Search through the DOAP database for projects that match the
        query terms. text is a piece of text in the title / summary /
        description fields of project (and possibly product). soyuz,
        bounties, bazaar, malone etc are hints as to whether the search
        should be limited to projects that are active in those Launchpad
        applications."""
        clauseTables = Set()
        clauseTables.add('Project')
        query = '1=1 '
        if text:
            text = quote(text)
            query += " AND Project.fti @@ ftq(%s) """ % (text,)
        if rosetta:
            clauseTables.add('Product')
            clauseTables.add('POTemplate')
        if malone:
            clauseTables.add('Product')
            clauseTables.add('BugTask')
        if bazaar:
            clauseTables.add('Product')
            clauseTables.add('ProductSeries')
            query += ' AND ProductSeries.branch IS NOT NULL \n'
        if search_products and text:
            clauseTables.add('Product')
            query += " AND Product.fti @@ ftq(%s) " % (text,)
        if 'Product' in clauseTables:
            query += ' AND Product.project=Project.id \n'
        if 'POTemplate' in clauseTables:
            query += ' AND POTemplate.product=Product.id \n'
        if 'BugTask' in clauseTables:
            query += ' AND BugTask.product=Product.id \n'
        if 'ProductSeries' in clauseTables:
            query += ' AND ProductSeries.product=Product.id \n'
        if not show_inactive:
            query += ' AND Project.active IS TRUE \n'
            if 'Product' in clauseTables:
                query += ' AND Product.active IS TRUE \n'
        return Project.select(query, distinct=True, clauseTables=clauseTables)


class ProjectBugTracker(SQLBase):
    """Implements the IProjectBugTracker interface, for access to the
    ProjectBugTracker table."""
    implements(IProjectBugTracker)

    _table = 'ProjectBugTracker'
    
    _columns = [ForeignKey(name='project', foreignKey="Project",
                           dbName="project", notNull=True),
                ForeignKey(name='bugtracker', foreignKey="BugTracker",
                           dbName="bugtracker", notNull=True),]


