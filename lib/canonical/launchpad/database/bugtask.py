
# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

__metaclass__ = type
from sets import Set

from sqlobject import DateTimeCol, ForeignKey, IntCol, StringCol
from sqlobject import MultipleJoin, RelatedJoin, AND, LIKE, OR, IN
from sqlobject import SQLObjectNotFound
from sqlobject.sqlbuilder import table

# Zope
from zope.exceptions import NotFoundError
from zope.security.interfaces import Unauthorized
from zope.component import getUtility
from zope.interface import implements, directlyProvides, directlyProvidedBy
from zope.interface import implements

from canonical.lp import dbschema
from canonical.launchpad.interfaces import IBugTask
from canonical.database.sqlbase import SQLBase, quote
from canonical.database.constants import nowUTC, DEFAULT
from canonical.launchpad.database.sourcepackage import SourcePackage
from canonical.launchpad.searchbuilder import any, NULL

from canonical.launchpad.interfaces import IBugTasksReport, \
    IBugTaskSet, IEditableUpstreamBugTask, IReadOnlyUpstreamBugTask, \
    IEditableDistroBugTask, IReadOnlyDistroBugTask, ILaunchBag

class BugTask(SQLBase):
    implements(IBugTask)
    _table = "BugTask"
    _defaultOrder = "-bug"

    bug = ForeignKey(dbName='bug', foreignKey='Bug')
    product = ForeignKey(
        dbName='product', foreignKey='Product',
        notNull=False, default=None)
    sourcepackagename = ForeignKey(
        dbName='sourcepackagename', foreignKey='SourcePackageName',
        notNull=False, default=None)
    distribution = ForeignKey(
        dbName='distribution', foreignKey='Distribution',
        notNull=False, default=None)
    distrorelease = ForeignKey(
        dbName='distrorelease', foreignKey='DistroRelease',
        notNull=False, default=None)
    milestone = ForeignKey(
        dbName='milestone', foreignKey='Milestone',
        notNull=False, default=None)
    status = IntCol(
        dbName='status', notNull=True,
        default=int(dbschema.BugTaskStatus.NEW))
    priority = IntCol(
        dbName='priority', notNull=True,
        default=int(dbschema.BugPriority.MEDIUM))
    severity = IntCol(
        dbName='severity', notNull=True,
        default=int(dbschema.BugSeverity.NORMAL))
    binarypackagename = ForeignKey(
        dbName='binarypackagename', foreignKey='BinaryPackageName',
        notNull=False, default=None)
    assignee = ForeignKey(
        dbName='assignee', foreignKey='Person',
        notNull=False, default=None)
    dateassigned = DateTimeCol(notNull=False, default=nowUTC)
    datecreated  = DateTimeCol(notNull=False, default=nowUTC)
    owner = ForeignKey(
        foreignKey='Person', dbName='owner', notNull=False, default=None)

    def bugtitle(self):
        return self.bug.title

    def maintainer(self):
        if self.product:
            return self.product.owner
        if self.distribution and self.sourcepackagename:
            query = "distro = %d AND sourcepackagename = %d" % (
                self.distribution.id, self.sourcepackagename.id )
            try:
                return SourcePackage.select(query)[0].maintainer
            except IndexError:
                return None
        return None

    def bugdescription(self):
        if self.bug.messages:
            return self.bug.messages[0].contents

    maintainer = property(maintainer)
    bugtitle = property(bugtitle)
    bugdescription = property(bugdescription)

    def _title(self):
        title = 'Malone Bug #' + str(self.bug.id)
        title += ' (' + self.bug.title + ')' + ' on '
        if self.distribution:
            title += self.distribution.name + ' '
            if self.distrorelease:
                title += self.distrorelease.name + ' '
            if self.sourcepackagename:
                title += self.sourcepackagename.name + ' '
            if self.binarypackagename:
                title += self.binarypackagename.name
        if self.product:
            title += self.product.displayname
        return title
    title = property(_title)



class BugTaskSet:

    implements(IBugTaskSet)

    table = BugTask

    def __init__(self, bug=None):
        self.bug = bug
        self.title = 'A Set of Bug Tasks'

    def __getitem__(self, id):
        """See canonical.launchpad.interfaces.IBugTaskSet."""
        principal = _get_authenticated_principal()
        try:
            task = self.table.select(self.table.q.id == id)[0]
            if task.product:
                # upstream task
                if principal and (
                    (principal.id == task.product.owner.id) or
                    (task.assignee and principal.id == task.assignee.id)):
                    mark_as_editable_upstream_task(task)
                else:
                    mark_as_readonly_upstream_task(task)
            else:
                # sourcepackage task
                if principal:
                    mark_as_editable_sourcepackage_task(task)
                else:
                    mark_as_readonly_sourcepackage_task(task)

            return task
        except IndexError:
            # Convert IndexError to KeyErrors to get Zope's NotFound page
            raise KeyError, id

    def __iter__(self):
        """See canonical.launchpad.interfaces.IBugTaskSet."""
        principal = _get_authenticated_principal()

        for row in self.table.select(self.table.q.bugID == self.bug):
            if row.product:
                # upstream task
                if principal and principal.id == row.product.owner.id:
                    mark_as_editable_upstream_task(row)
                else:
                    mark_as_readonly_upstream_task(row)
            else:
                # sourcepackage task
                if principal:
                    mark_as_editable_sourcepackage_task(task)
                else:
                    mark_as_readonly_sourcepackage_task(task)

            yield row

    def get(self, id):
        """See canonical.launchpad.interfaces.IBugTaskSet."""
        try:
            bugtask = self.table.get(id)
        except SQLObjectNotFound, err:
            raise NotFoundError("BugTask with ID %s does not exist" % str(id))

        return bugtask

    def search(self, bug=None, searchtext=None, status=None, priority=None,
               severity=None, product=None, milestone=None, assignee=None,
               submitter=None, orderby=None):
        """See canonical.launchpad.interfaces.IBugTaskSet."""
        query = ""

        if searchtext:
            query += "Bug.fti @@ ftq(%s)" % quote(searchtext)

        # build the part of the query for FK columns
        for arg in ('bug', 'product', 'milestone', 'assignee', 'submitter'):
            query_arg = eval(arg)
            if query_arg is not None:
                if query:
                    query += " AND "

                fragment = ""
                if isinstance(query_arg, any):
                    quoted_ids = [quote(obj.id) for obj in query_arg.query_values]
                    query_values = ", ".join(quoted_ids)
                    fragment = "(BugTask.%s IN (%s))" % (arg, query_values)
                else:
                    if query_arg == NULL:
                        fragment = "(BugTask.%s IS NULL)" % (arg)
                    else:
                        fragment = "(BugTask.%s = %s)" % (arg, str(quote(query_arg.id)))

                query += fragment

        # build the part of the query for the db schema columns
        for arg in ('status', 'priority', 'severity'):
            query_arg = eval(arg)
            if query_arg is not None:
                if query:
                    query += " AND "

                fragment = ""
                if isinstance(query_arg, any):
                    quoted_ids = [quote(obj) for obj in query_arg.query_values]
                    query_values = ", ".join(quoted_ids)
                    fragment = "(BugTask.%s IN (%s))" % (arg, query_values)
                else:
                    fragment = "(BugTask.%s = %s)" % (arg, str(quote(query_arg)))

                query += fragment

        user = getUtility(ILaunchBag).user

        if query:
            query += " AND "

        if user:
            query += "("
        query += "(BugTask.bug = Bug.id AND Bug.private = FALSE)"
        
        # XXX: Brad Bollenbach, 2005-02-03: The subselect here is due to what
        # appears to be a bug in sqlobject not taking distinct into
        # consideration when doing counts.
        if user:
            query += ((
                " OR ((BugTask.bug = Bug.id AND Bug.private = TRUE) AND "
                "     (Bug.id in (SELECT Bug.id FROM Bug, BugSubscription WHERE "
                "                (Bug.id = BugSubscription.bug) AND "
                "                (BugSubscription.person = %(personid)d) AND "
                "                (BugSubscription.subscription IN (%(cc)d, %(watch)d))))))") %
                {'personid' : user.id,
                 'cc' : dbschema.BugSubscription.CC.value,
                 'watch' : dbschema.BugSubscription.WATCH.value})

        bugtasks = BugTask.select(
            query, clauseTables = ["Bug", "BugTask"])
        if orderby:
            bugtasks = bugtasks.orderBy(orderby)

        return bugtasks

    def createTask(self, bug, product=None, distribution=None, distrorelease=None,
                   sourcepackagename=None, binarypackagename=None, status=None,
                   priority=None, severity=None, assignee=None, owner=None,
                   milestone=None):
        """See canonical.launchpad.interfaces.IBugTaskSet."""
        bugtask_args = {
            'bug' : getattr(bug, 'id', None),
            'product' : getattr(product, 'id', None),
            'distribution' : getattr(distribution, 'id', None),
            'distrorelease' : getattr(distrorelease, 'id', None),
            'sourcepackagename' : getattr(sourcepackagename, 'id', None),
            'binarypackagename' : getattr(binarypackagename, 'id', None),
            'status' : status,
            'priority' : priority,
            'severity' : severity,
            'assignee' : getattr(assignee, 'id', None),
            'owner' : getattr(owner, 'id', None),
            'milestone' : getattr(milestone, 'id', None)
        }

        return BugTask(**bugtask_args)

    def add(self, ob):
        return ob

    def nextURL(self):
        return '.'

def _get_authenticated_principal():
    # XXX, Brad Bollenbach, 2005-01-05: should possible move this into some api
    # module that contains shortcut functions for getting at stuff in the
    # launchbag
    launchbag = getUtility(ILaunchBag)
    if launchbag.login:
        return launchbag.user

def mark_task(obj, iface):
    directlyProvides(obj, iface + directlyProvidedBy(obj))

def mark_as_editable_upstream_task(task):
    mark_task(task, IEditableUpstreamBugTask)

def mark_as_readonly_upstream_task(task):
    mark_task(task, IReadOnlyUpstreamBugTask)

def mark_as_editable_sourcepackage_task(task):
    mark_task(task, IEditableDistroBugTask)

def mark_as_readonly_sourcepackage_task(task):
    mark_task(task, IReadOnlyDistroBugTask)

def BugTaskFactory(context, **kw):
    return BugTask(bugID=context.context.bug, **kw)

# REPORTS
class BugTasksReport(object):

    implements(IBugTasksReport)

    def __init__(self):
        # initialise the user to None, will raise an exception if the
        # calling class does not set this to a person.id
        from canonical.launchpad.database import BugTask, Bug
        self.user = None
        self.minseverity = 0
        self.minpriority = 0
        self.Bug = Bug
        self.BT = BugTask
        self.showclosed = False

    # bugs assigned (i.e. tasks) to packages maintained by the user
    def maintainedPackageBugs(self):
        querystr = (
            "BugTask.sourcepackagename = SourcePackage.sourcepackagename AND "
            "BugTask.distribution = SourcePackage.distro AND "
            "SourcePackage.maintainer = %s AND "
            "BugTask.severity >= %s AND "
            "BugTask.priority >= %s") % (
            self.user.id, self.minseverity, self.minpriority)
        clauseTables = ('SourcePackage',)

        if not self.showclosed:
            querystr = querystr + ' AND BugTask.status < 30'
        return list(self.BT.select(querystr, clauseTables=clauseTables))

    # bugs assigned (i.e. tasks) to products owned by the user
    def maintainedProductBugs(self):
        querystr = (
            "BugTask.product = Product.id AND "
            "Product.owner = %s AND "
            "BugTask.severity >= %s AND "
            "BugTask.priority >= %s") % (
            self.user.id, self.minseverity, self.minpriority)
        
        clauseTables = ('Product',)

        if not self.showclosed:
            querystr = querystr + ' AND BugTask.status < 30'
        return list(self.BT.select(querystr, clauseTables=clauseTables))

    # package bugs assigned specifically to the user
    def packageAssigneeBugs(self):
        querystr = (
            "BugTask.sourcepackagename IS NOT NULL AND "
            "BugTask.assignee = %s AND "
            "BugTask.severity >= %s AND "
            "BugTask.priority >= %s") % (
            self.user.id, self.minseverity, self.minpriority)
        if not self.showclosed:
            querystr = querystr + ' AND BugTask.status < 30'
        return list(self.BT.select(querystr))

    # product bugs assigned specifically to the user
    def productAssigneeBugs(self):
        querystr = (
            "BugTask.product IS NOT NULL AND "
            "BugTask.assignee =%s AND "
            "BugTask.severity >=%s AND "
            "BugTask.priority >=%s") % (
            self.user.id, self.minseverity, self.minpriority)
        if not self.showclosed:
            querystr = querystr + ' AND BugTask.status < 30'
        return list(self.BT.select(querystr))

    # all bugs assigned to a user
    def assignedBugs(self):
        bugs = Set()
        for bugtask in self.maintainedPackageBugs():
            bugs.add(bugtask.bug)
        for bugtask in self.maintainedProductBugs():
            bugs.add(bugtask.bug)
        for bugtask in self.packageAssigneeBugs():
            bugs.add(bugtask.bug)
        for bugtask in self.productAssigneeBugs():
            bugs.add(bugtask.bug)
        buglistwithdates = [ (bug.datecreated, bug) for bug in bugs ]
        buglistwithdates.sort()
        buglistwithdates.reverse()
        bugs = [bug[1] for bug in buglistwithdates]
        return bugs
