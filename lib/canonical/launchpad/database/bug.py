"""Launchpad Bug-related Database Table Objects

Part of the Launchpad system.

(c) 2004 Canonical, Ltd.
"""

from datetime import datetime
from sets import Set

from zope.interface import implements

from sqlobject import DateTimeCol, ForeignKey, IntCol, StringCol
from sqlobject import MultipleJoin, RelatedJoin, AND, LIKE, OR

from canonical.launchpad.interfaces.bug import IBug, IBugContainer
from canonical.launchpad.interfaces import *

from canonical.database.sqlbase import SQLBase
from canonical.database.constants import nowUTC

from canonical.launchpad.database.bugcontainer import BugContainerBase
from canonical.launchpad.database.bugassignment \
        import SourcePackageBugAssignment, ProductBugAssignment
from canonical.launchpad.database.sourcepackage import SourcePackage
from canonical.launchpad.database.product import Product
from canonical.launchpad.database.bugactivity import BugActivity
from canonical.launchpad.database.bugsubscription import BugSubscription
from canonical.lp.dbschema import BugSubscription as BugSubscriptionVocab

class Bug(SQLBase):
    """A bug."""

    implements(IBug)

    _defaultOrder = '-id'

    # db field names
    name = StringCol(dbName='name', unique=True, default=None)
    title = StringCol(dbName='title', notNull=True)
    shortdesc = StringCol(dbName='shortdesc', notNull=True)
    description = StringCol(dbName='description', notNull=True)
    owner = ForeignKey(dbName='owner', foreignKey='Person', notNull=True)
    duplicateof = ForeignKey(dbName='duplicateof', foreignKey='Bug', default=None)
    datecreated = DateTimeCol(dbName='datecreated', notNull=True)
    communityscore = IntCol(dbName='communityscore', notNull=True, default=0)
    communitytimestamp = DateTimeCol(dbName='communitytimestamp', notNull=True)
    hits = IntCol(dbName='hits', notNull=True, default=0)
    hitstimestamp = DateTimeCol(dbName='hitstimestamp', notNull=True)
    activityscore = IntCol(dbName='activityscore', notNull=True, default=0)
    activitytimestamp = DateTimeCol(dbName='activitytimestamp', notNull = True)
    
    # useful Joins
    activity = MultipleJoin('BugActivity', joinColumn='bug')
    messages = MultipleJoin('BugMessage', joinColumn='bug')
    # TODO: Standardize on pluralization and naming for table relationships
    productassignment = MultipleJoin('ProductBugAssignment', joinColumn='bug')
    packageassignment = MultipleJoin('SourcePackageBugAssignment',
                                    joinColumn='bug')
    productinfestations = MultipleJoin('BugProductInfestation', joinColumn='bug')
    packageinfestations = MultipleJoin('BugPackageInfestation', joinColumn='bug')
    watches = MultipleJoin('BugWatch', joinColumn='bug')
    externalrefs = MultipleJoin('BugExternalRef', joinColumn='bug')
    subscriptions = MultipleJoin('BugSubscription', joinColumn='bug')

    def _set_title(self, value):
        # Record changes of title in activity log
        # TODO: We might want a 'Bug Created' log entry
        if hasattr(self, 'id'):
            log = BugActivity(bug=self.id,
                            datechanged=nowUTC,
                            person=1, # should be the logged in user
                            whatchanged='title',
                            oldvalue=self.title,
                            newvalue=value,
                            message='Message here')
        self._SO_set_title(value)


class MaloneBug(Bug):
    implements(IMaloneBug)

    _table = 'Bug'

    def __init__(self, **kw):
        # TODO: Fix Z3 so these can use defaults set in the schema.
        # Currently can't use a callable.
        kw['datecreated'] = datetime.utcnow()
        kw['communitytimestamp'] = datetime.utcnow()
        kw['hitstimestamp'] = datetime.utcnow()
        kw['activitytimestamp'] = datetime.utcnow()
        Bug.__init__(self, **kw)

    def add(self, ob):
        return ob

    def nextURL(self):
        return '.'

def BugFactory(*args, **kw):
    """Create a bug from an IBugAddForm"""
    bug = MaloneBug(
        title = kw['title'],
        shortdesc = kw['shortdesc'],
        description = kw['description'],
        owner = kw['owner'])

    # If the user has specified a product, create the ProductBugAssignment
    if kw.get('product', None):
        ProductBugAssignment(bug=bug, product=kw['product'])

    if kw.get('sourcepackage', None):
        SourcePackageBugAssignment(
            bug=bug, sourcepackage=kw['sourcepackage'], binarypackagename=None)

    BugSubscription(
        person = kw['owner'], bugID = bug.id,
        subscription = BugSubscriptionVocab.CC.value)

    class BugAdded(object):
        implements(IBugAddForm)
        def __init__(self, **kw):
            for attr, val in kw.items():
                setattr(self, attr, val)

    bug_added = BugAdded(**kw)
    bug_added.id = bug.id

    return bug_added

class BugContainer(BugContainerBase):
    """A container for bugs."""

    implements(IBugContainer)
    table = MaloneBug

    def __getitem__(self, id):
        try:
            return self.table.select(self.table.q.id==id)[0]
        except IndexError:
            # Convert IndexError to KeyErrors to get Zope's NotFound page
            raise KeyError, id

    def __iter__(self):
        for row in self.table.select():
            yield row

def MaloneBugFactory(context, **kw):
    now = datetime.utcnow()
    # TODO: How do we handle this email address?
    # If the user is not logged in, we might want to create a Person for
    # them (although we really want to link their email address to their
    # existing Person).
    # If the user is not logged in, and the email address they entered is
    # already in the system, do we create the Bug as that Person?
    # If the user is logged in, we want to validate the email address is one
    # of theirs.
    #
    #email = kw.get('email', None)
    #del kw['email']
    #if email:
    #    e = EmailAddress.select(EmailAddress.q.email==email)
    submitterid = context.request.principal.id
    bug = MaloneBug(
            datecreated=now,
            communityscore=0,
            communitytimestamp=now,
            duplicateof=None,
            hits=0,
            hitstimestamp=now,
            activityscore=0,
            activitytimestamp=now,
            owner=submitterid,
            **kw
            )
    return bug




# REPORTS
# TODO: Mark Shuttleworth 24/10/04 this should be in bugassignment.py but
# it creates circular imports


class BugsAssignedReport(object):

    implements(IBugsAssignedReport)

    def __init__(self):
        # initialise the user to None, will raise an exception if the
        # calling class does not set this to a person.id
        self.user = None
        self.minseverity = 0
        self.BSA = SourcePackageBugAssignment
        self.BPA = ProductBugAssignment

    # bugs on packages maintained by the user
    def maintainedPackageBugs(self):
        return Bug.select("""Bug.id=SourcePackageBugAssignment.bug AND
                             SourcePackageBugAssignment.sourcepackage=SourcePackage.id AND
                             SourcePackage.maintainer=%s AND
                             SourcePackageBugAssignment.severity>=%s""" % (self.user.id,
                             self.minseverity))

    # bugs on products owned by the user
    def maintainedProductBugs(self):
        return Bug.select("""Bug.id=ProductBugAssignment.bug AND
                             ProductBugAssignment.product=Product.id AND
                             Product.owner=%s AND
                             ProductBugAssignment.severity>=%s""" % (self.user.id,
                             self.minseverity))

    # package bugs assigned specifically to the user
    def packageAssigneeBugs(self):
        return Bug.select("""Bug.id=SourcePackageBugAssignment.bug AND
                             SourcePackageBugAssignment.assignee=%s AND
                             SourcePackageBugAssignment.severity>=%s""" %
                             (self.user.id, self.minseverity))

    # product bugs assigned specifically to the user
    def productAssigneeBugs(self):
        return Bug.select("""Bug.id=ProductBugAssignment.bug AND
                             ProductBugAssignment.assignee=%s AND
                             ProductBugAssignment.severity>=%s""" %
                             (self.user.id, self.minseverity))


    # all bugs assigned to a user
    def assignedBugs(self):
        bugs = Set()
        for bug in self.maintainedPackageBugs():
            bugs.add(bug)
        for bug in self.maintainedProductBugs():
            bugs.add(bug)
        for bug in self.packageAssigneeBugs():
            bugs.add(bug)
        for bug in self.productAssigneeBugs():
            bugs.add(bug)
        return bugs


