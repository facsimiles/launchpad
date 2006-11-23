# Copyright 2004 Canonical Ltd.  All rights reserved.

"""Database classes including and related to Product."""

__metaclass__ = type
__all__ = ['Product', 'ProductSet']

from zope.interface import implements
from zope.component import getUtility

from sqlobject import (
    ForeignKey, StringCol, BoolCol, SQLMultipleJoin, SQLRelatedJoin,
    SQLObjectNotFound, AND)

from canonical.database.sqlbase import quote, SQLBase, sqlvalues
from canonical.database.constants import UTC_NOW
from canonical.database.datetimecol import UtcDateTimeCol

from canonical.launchpad.helpers import shortlist

from canonical.lp.dbschema import (
    EnumCol, TranslationPermission, SpecificationSort, SpecificationFilter,
    SpecificationStatus)
from canonical.launchpad.database.branch import Branch
from canonical.launchpad.components.bugtarget import BugTargetBase
from canonical.launchpad.database.karma import KarmaContextMixin
from canonical.launchpad.database.bug import (
    BugSet, get_bug_tags, get_bug_tags_open_count)
from canonical.launchpad.database.productseries import ProductSeries
from canonical.launchpad.database.productbounty import ProductBounty
from canonical.launchpad.database.distribution import Distribution
from canonical.launchpad.database.productrelease import ProductRelease
from canonical.launchpad.database.bugtask import BugTaskSet
from canonical.launchpad.database.packaging import Packaging
from canonical.launchpad.database.milestone import Milestone
from canonical.launchpad.database.specification import Specification
from canonical.launchpad.database.supportcontact import SupportContact
from canonical.launchpad.database.ticket import Ticket, TicketSet
from canonical.launchpad.database.cal import Calendar
from canonical.launchpad.interfaces import (
    IProduct, IProductSet, ILaunchpadCelebrities, ICalendarOwner,
    ITicketTarget, NotFoundError, TICKET_STATUS_DEFAULT_SEARCH)


class Product(SQLBase, BugTargetBase, KarmaContextMixin):
    """A Product."""

    implements(IProduct, ICalendarOwner, ITicketTarget)

    _table = 'Product'

    project = ForeignKey(
        foreignKey="Project", dbName="project", notNull=False, default=None)
    owner = ForeignKey(
        foreignKey="Person", dbName="owner", notNull=True)
    bugcontact = ForeignKey(
        dbName='bugcontact', foreignKey='Person', notNull=False, default=None)
    security_contact = ForeignKey(
        dbName='security_contact', foreignKey='Person', notNull=False,
        default=None)
    driver = ForeignKey(
        foreignKey="Person", dbName="driver", notNull=False, default=None)
    name = StringCol(
        dbName='name', notNull=True, alternateID=True, unique=True)
    displayname = StringCol(dbName='displayname', notNull=True)
    title = StringCol(dbName='title', notNull=True)
    summary = StringCol(dbName='summary', notNull=True)
    description = StringCol(notNull=False, default=None)
    datecreated = UtcDateTimeCol(
        dbName='datecreated', notNull=True, default=UTC_NOW)
    homepageurl = StringCol(dbName='homepageurl', notNull=False, default=None)
    homepage_content = StringCol(default=None)
    emblem = ForeignKey(
        dbName='emblem', foreignKey='LibraryFileAlias', default=None)
    gotchi = ForeignKey(
        dbName='gotchi', foreignKey='LibraryFileAlias', default=None)
    screenshotsurl = StringCol(
        dbName='screenshotsurl', notNull=False, default=None)
    wikiurl =  StringCol(dbName='wikiurl', notNull=False, default=None)
    programminglang = StringCol(
        dbName='programminglang', notNull=False, default=None)
    downloadurl = StringCol(dbName='downloadurl', notNull=False, default=None)
    lastdoap = StringCol(dbName='lastdoap', notNull=False, default=None)
    translationgroup = ForeignKey(dbName='translationgroup',
        foreignKey='TranslationGroup', notNull=False, default=None)
    translationpermission = EnumCol(dbName='translationpermission',
        notNull=True, schema=TranslationPermission,
        default=TranslationPermission.OPEN)
    bugtracker = ForeignKey(
        foreignKey="BugTracker", dbName="bugtracker", notNull=False,
        default=None)
    official_malone = BoolCol(dbName='official_malone', notNull=True,
        default=False)
    official_rosetta = BoolCol(dbName='official_rosetta', notNull=True,
        default=False)
    active = BoolCol(dbName='active', notNull=True, default=True)
    reviewed = BoolCol(dbName='reviewed', notNull=True, default=False)
    autoupdate = BoolCol(dbName='autoupdate', notNull=True, default=False)
    freshmeatproject = StringCol(notNull=False, default=None)
    sourceforgeproject = StringCol(notNull=False, default=None)
    # While the interface defines this field as required, we need to
    # allow it to be NULL so we can create new product records before
    # the corresponding series records.
    development_focus = ForeignKey(foreignKey="ProductSeries",
                                   dbName="development_focus",
                                   notNull=False, default=None)

    calendar = ForeignKey(dbName='calendar', foreignKey='Calendar',
                          default=None, forceDBName=True)

    def getExternalBugTracker(self):
        """See IProduct."""
        if self.official_malone:
            return None
        elif self.bugtracker is not None:
            return self.bugtracker
        elif self.project is not None:
            return self.project.bugtracker
        else:
            return None

    def searchTasks(self, search_params):
        """See canonical.launchpad.interfaces.IBugTarget."""
        search_params.setProduct(self)
        return BugTaskSet().search(search_params)

    def getUsedBugTags(self):
        """See IBugTarget."""
        return get_bug_tags("BugTask.product = %s" % sqlvalues(self))

    def getUsedBugTagsWithOpenCounts(self, user):
        """See IBugTarget."""
        return get_bug_tags_open_count(
            "BugTask.product = %s" % sqlvalues(self), user)

    def getOrCreateCalendar(self):
        if not self.calendar:
            self.calendar = Calendar(
                title='%s Product Calendar' % self.displayname,
                revision=0)
        return self.calendar

    branches = SQLMultipleJoin('Branch', joinColumn='product',
        orderBy='id')
    serieslist = SQLMultipleJoin('ProductSeries', joinColumn='product',
        orderBy='name')

    @property
    def name_with_project(self):
        """See lib.canonical.launchpad.interfaces.IProduct"""
        if self.project and self.project.name != self.name:
            return self.project.name + ": " + self.name
        return self.name

    @property
    def releases(self):
        return ProductRelease.select(
            AND(ProductRelease.q.productseriesID == ProductSeries.q.id,
                ProductSeries.q.productID == self.id),
            clauseTables=['ProductSeries'],
            orderBy=['version']
            )

    @property
    def drivers(self):
        """See IProduct."""
        drivers = set()
        drivers.add(self.driver)
        if self.project is not None:
            drivers.add(self.project.driver)
        drivers.discard(None)
        if len(drivers) == 0:
            if self.project is not None:
                drivers.add(self.project.owner)
            else:
                drivers.add(self.owner)
        return sorted(drivers, key=lambda driver: driver.browsername)

    milestones = SQLMultipleJoin('Milestone', joinColumn = 'product',
        orderBy=['dateexpected', 'name'])

    bounties = SQLRelatedJoin(
        'Bounty', joinColumn='product', otherColumn='bounty',
        intermediateTable='ProductBounty')

    @property
    def sourcepackages(self):
        # XXX: SteveAlexander, 2005-04-25, this needs a system doc test.
        from canonical.launchpad.database.sourcepackage import SourcePackage
        clause = """ProductSeries.id=Packaging.productseries AND
                    ProductSeries.product = %s
                    """ % sqlvalues(self.id)
        clauseTables = ['ProductSeries']
        ret = Packaging.select(clause, clauseTables)
        return [SourcePackage(sourcepackagename=r.sourcepackagename,
                              distrorelease=r.distrorelease)
                for r in ret]

    @property
    def bugtargetname(self):
        """See IBugTarget."""
        return '%s (upstream)' % self.name

    def getLatestBranches(self, quantity=5):
        """See IProduct."""
        # XXX Should use Branch.date_created. See bug 38598.
        # -- David Allouche 2006-04-11
        return shortlist(Branch.selectBy(product=self,
            orderBy='-id').limit(quantity))

    def getPackage(self, distrorelease):
        """See IProduct."""
        if isinstance(distrorelease, Distribution):
            distrorelease = distrorelease.currentrelease
        for pkg in self.sourcepackages:
            if pkg.distrorelease == distrorelease:
                return pkg
        else:
            raise NotFoundError(distrorelease)

    def getMilestone(self, name):
        """See IProduct."""
        return Milestone.selectOne("""
            product = %s AND
            name = %s
            """ % sqlvalues(self.id, name))

    def createBug(self, bug_params):
        """See IBugTarget."""
        bug_params.setBugTarget(product=self)
        return BugSet().createBug(bug_params)

    def newTicket(self, owner, title, description, datecreated=None):
        """See ITicketTarget."""
        return TicketSet.new(title=title, description=description,
            owner=owner, product=self, datecreated=datecreated)

    def getTicket(self, ticket_id):
        """See ITicketTarget."""
        # first see if there is a ticket with that number
        try:
            ticket = Ticket.get(ticket_id)
        except SQLObjectNotFound:
            return None
        # now verify that that ticket is actually for this target
        if ticket.target != self:
            return None
        return ticket

    def searchTickets(self, search_text=None,
                      status=TICKET_STATUS_DEFAULT_SEARCH, owner=None,
                      sort=None):
        """See ITicketTarget."""
        return TicketSet.search(
            product=self, search_text=search_text, status=status,
            owner=owner, sort=sort)

    def findSimilarTickets(self, title):
        """See ITicketTarget."""
        return TicketSet.findSimilar(title, product=self)

    def addSupportContact(self, person):
        """See ITicketTarget."""
        if person in self.support_contacts:
            return False
        SupportContact(
            product=self, person=person,
            sourcepackagename=None, distribution=None)
        return True

    def removeSupportContact(self, person):
        """See ITicketTarget."""
        if person not in self.support_contacts:
            return False
        support_contact_entry = SupportContact.selectOneBy(
            product=self, person=person)
        support_contact_entry.destroySelf()
        return True

    @property
    def support_contacts(self):
        """See ITicketTarget."""
        support_contacts = SupportContact.selectBy(product=self)

        return shortlist([
            support_contact.person for support_contact in support_contacts
            ],
            longest_expected=100)

    @property
    def translatable_packages(self):
        """See IProduct."""
        packages = set(package for package in self.sourcepackages
                       if len(package.currentpotemplates) > 0)
        # Sort packages by distrorelease.name and package.name
        return sorted(packages, key=lambda p: (p.distrorelease.name, p.name))

    @property
    def translatable_series(self):
        """See IProduct."""
        series = ProductSeries.select('''
            POTemplate.productseries = ProductSeries.id AND
            ProductSeries.product = %d
            ''' % self.id,
            clauseTables=['POTemplate'],
            orderBy='datecreated', distinct=True)
        return list(series)

    @property
    def primary_translatable(self):
        """See IProduct."""
        packages = self.translatable_packages
        ubuntu = getUtility(ILaunchpadCelebrities).ubuntu
        targetrelease = ubuntu.currentrelease
        # First, go with the latest product series that has templates:
        series = self.translatable_series
        if series:
            return series[0]
        # Otherwise, look for an Ubuntu package in the current distrorelease:
        for package in packages:
            if package.distrorelease == targetrelease:
                return package
        # now let's make do with any ubuntu package
        for package in packages:
            if package.distribution == ubuntu:
                return package
        # or just any package
        if len(packages) > 0:
            return packages[0]
        # capitulate
        return None

    @property
    def translationgroups(self):
        tg = []
        if self.translationgroup:
            tg.append(self.translationgroup)
        if self.project:
            if self.project.translationgroup:
                if self.project.translationgroup not in tg:
                    tg.append(self.project.translationgroup)

    @property
    def aggregatetranslationpermission(self):
        perms = [self.translationpermission]
        if self.project:
            perms.append(self.project.translationpermission)
        # XXX reviewer please describe a better way to explicitly order
        # the enums. The spec describes the order, and the values make
        # it work, and there is space left for new values so we can
        # ensure a consistent sort order in future, but there should be
        # a better way.
        return max(perms)

    @property
    def has_any_specifications(self):
        """See IHasSpecifications."""
        return self.all_specifications.count()

    @property
    def all_specifications(self):
        return self.specifications(filter=[SpecificationFilter.ALL])

    @property
    def valid_specifications(self):
        return self.specifications(filter=[SpecificationFilter.VALID])

    def specifications(self, sort=None, quantity=None, filter=None):
        """See IHasSpecifications."""

        # Make a new list of the filter, so that we do not mutate what we
        # were passed as a filter
        if not filter:
            # filter could be None or [] then we decide the default
            # which for a product is to show incomplete specs
            filter = [SpecificationFilter.INCOMPLETE]

        # now look at the filter and fill in the unsaid bits

        # defaults for completeness: if nothing is said about completeness
        # then we want to show INCOMPLETE
        completeness = False
        for option in [
            SpecificationFilter.COMPLETE,
            SpecificationFilter.INCOMPLETE]:
            if option in filter:
                completeness = True
        if completeness is False:
            filter.append(SpecificationFilter.INCOMPLETE)

        # defaults for acceptance: in this case we have nothing to do
        # because specs are not accepted/declined against a distro

        # defaults for informationalness: we don't have to do anything
        # because the default if nothing is said is ANY

        # sort by priority descending, by default
        if sort is None or sort == SpecificationSort.PRIORITY:
            order = ['-priority', 'Specification.status', 'Specification.name']
        elif sort == SpecificationSort.DATE:
            order = ['-Specification.datecreated', 'Specification.id']

        # figure out what set of specifications we are interested in. for
        # products, we need to be able to filter on the basis of:
        #
        #  - completeness.
        #  - informational.
        #
        base = 'Specification.product = %s' % self.id
        query = base
        # look for informational specs
        if SpecificationFilter.INFORMATIONAL in filter:
            query += ' AND Specification.informational IS TRUE'

        # filter based on completion. see the implementation of
        # Specification.is_complete() for more details
        completeness =  Specification.completeness_clause

        if SpecificationFilter.COMPLETE in filter:
            query += ' AND ( %s ) ' % completeness
        elif SpecificationFilter.INCOMPLETE in filter:
            query += ' AND NOT ( %s ) ' % completeness

        # Filter for validity. If we want valid specs only then we should
        # exclude all OBSOLETE or SUPERSEDED specs
        if SpecificationFilter.VALID in filter:
            query += ' AND Specification.status NOT IN ( %s, %s ) ' % \
                sqlvalues(SpecificationStatus.OBSOLETE,
                          SpecificationStatus.SUPERSEDED)

        # ALL is the trump card
        if SpecificationFilter.ALL in filter:
            query = base

        # Filter for specification text
        for constraint in filter:
            if isinstance(constraint, basestring):
                # a string in the filter is a text search filter
                query += ' AND Specification.fti @@ ftq(%s) ' % quote(
                    constraint)

        # now do the query, and remember to prejoin to people
        results = Specification.select(query, orderBy=order, limit=quantity)
        return results.prejoin(['assignee', 'approver', 'drafter'])

    def getSpecification(self, name):
        """See ISpecificationTarget."""
        return Specification.selectOneBy(product=self, name=name)

    def getSeries(self, name):
        """See IProduct."""
        return ProductSeries.selectOneBy(product=self, name=name)

    def newSeries(self, owner, name, summary, branch=None):
        return ProductSeries(product=self, owner=owner, name=name,
                             summary=summary, user_branch=branch)

    def getRelease(self, version):
        return ProductRelease.selectOne("""
            ProductRelease.productseries = ProductSeries.id AND
            ProductSeries.product = %s AND
            ProductRelease.version = %s
            """ % sqlvalues(self.id, version),
            clauseTables=['ProductSeries'])

    def packagedInDistros(self):
        distros = Distribution.select(
            "Packaging.productseries = ProductSeries.id AND "
            "ProductSeries.product = %s AND "
            "Packaging.distrorelease = DistroRelease.id AND "
            "DistroRelease.distribution = Distribution.id"
            "" % sqlvalues(self.id),
            clauseTables=['Packaging', 'ProductSeries', 'DistroRelease'],
            orderBy='name',
            distinct=True
            )
        return distros

    def ensureRelatedBounty(self, bounty):
        """See IProduct."""
        for curr_bounty in self.bounties:
            if bounty.id == curr_bounty.id:
                return None
        ProductBounty(product=self, bounty=bounty)
        return None

    def newBranch(self, name, title, url, home_page, lifecycle_status,
                  summary, whiteboard):
        """See IProduct."""
        from canonical.launchpad.database import Branch
        return Branch(
            product=self, name=name, title=title, url=url, home_page=home_page,
            lifecycle_status=lifecycle_status, summary=summary,
            whiteboard=whiteboard)


class ProductSet:
    implements(IProductSet)

    def __init__(self):
        self.title = "Products registered in Launchpad"

    def __getitem__(self, name):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        item = Product.selectOneBy(name=name, active=True)
        if item is None:
            raise NotFoundError(name)
        return item

    def __iter__(self):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        return iter(self._getProducts())

    def latest(self, quantity=5):
        return self._getProducts()[:quantity]

    def _getProducts(self):
        results = Product.selectBy(active=True, orderBy="-Product.datecreated")
        # The main product listings include owner, so we prejoin it in
        return results.prejoin(["owner"])

    def get(self, productid):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        try:
            return Product.get(productid)
        except SQLObjectNotFound:
            raise NotFoundError("Product with ID %s does not exist" %
                                str(productid))

    def getByName(self, name, default=None, ignore_inactive=False):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        if ignore_inactive:
            product = Product.selectOneBy(name=name, active=True)
        else:
            product = Product.selectOneBy(name=name)
        if product is None:
            return default
        return product


    def createProduct(self, owner, name, displayname, title, summary,
                      description=None, project=None, homepageurl=None,
                      screenshotsurl=None, wikiurl=None,
                      downloadurl=None, freshmeatproject=None,
                      sourceforgeproject=None, programminglang=None,
                      reviewed=False):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        product = Product(
            owner=owner, name=name, displayname=displayname,
            title=title, project=project, summary=summary,
            description=description, homepageurl=homepageurl,
            screenshotsurl=screenshotsurl, wikiurl=wikiurl,
            downloadurl=downloadurl, freshmeatproject=freshmeatproject,
            sourceforgeproject=sourceforgeproject,
            programminglang=programminglang, reviewed=reviewed)

        # Create a default trunk series and set it as the development focus
        trunk = product.newSeries(owner, 'trunk', 'The "trunk" series '
            'represents the primary line of development rather than '
            'a stable release branch. This is sometimes also called MAIN '
            'or HEAD.')
        product.development_focus = trunk

        return product


    def forReview(self):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        return Product.select("reviewed IS FALSE")

    def search(self, text=None, soyuz=None,
               rosetta=None, malone=None,
               bazaar=None,
               show_inactive=False):
        """See canonical.launchpad.interfaces.product.IProductSet."""
        # XXX: the soyuz argument is unused
        #   -- kiko, 2006-03-22
        clauseTables = set()
        clauseTables.add('Product')
        queries = []
        if text:
            queries.append("Product.fti @@ ftq(%s) " % sqlvalues(text))
        if rosetta:
            clauseTables.add('POTemplate')
            clauseTables.add('ProductRelease')
            clauseTables.add('ProductSeries')
            queries.append("POTemplate.productrelease=ProductRelease.id")
            queries.append("ProductRelease.productseries=ProductSeries.id")
            queries.append("ProductSeries.product=product.id")
        if malone:
            clauseTables.add('BugTask')
            queries.append('BugTask.product=Product.id')
        if bazaar:
            clauseTables.add('ProductSeries')
            queries.append('(ProductSeries.import_branch IS NOT NULL OR '
                           'ProductSeries.user_branch IS NOT NULL)')
        if 'ProductSeries' in clauseTables:
            queries.append('ProductSeries.product=Product.id')
        if not show_inactive:
            queries.append('Product.active IS TRUE')
        query = " AND ".join(queries)
        return Product.select(query, distinct=True,
                              prejoins=["owner"],
                              clauseTables=clauseTables)

    def translatables(self):
        """See IProductSet"""
        upstream = Product.select('''
            Product.id = ProductSeries.product AND
            POTemplate.productseries = ProductSeries.id
            ''',
            clauseTables=['ProductSeries', 'POTemplate'],
            distinct=True)
        distro = Product.select('''
            Product.id = ProductSeries.product AND
            Packaging.productseries = ProductSeries.id AND
            Packaging.sourcepackagename = POTemplate.sourcepackagename
            ''',
            clauseTables=['ProductSeries', 'Packaging', 'POTemplate'],
            distinct=True)
        return upstream.union(distro)

    def count_all(self):
        return Product.select().count()

    def count_translatable(self):
        return self.translatables().count()

    def count_reviewed(self):
        return Product.selectBy(reviewed=True, active=True).count()

    def count_bounties(self):
        return Product.select("ProductBounty.product=Product.id",
            distinct=True, clauseTables=['ProductBounty']).count()

    def count_buggy(self):
        return Product.select("BugTask.product=Product.id",
            distinct=True, clauseTables=['BugTask']).count()

    def count_featureful(self):
        return Product.select("Specification.product=Product.id",
            distinct=True, clauseTables=['Specification']).count()

