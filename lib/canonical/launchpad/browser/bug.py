# Copyright 2004 Canonical Ltd.  All rights reserved.

__metaclass__ = type

__all__ = [
    'BugSetNavigation',
    'BugView',
    'BugSetView',
    'BugEditView',
    'BugLinkView',
    'BugUnlinkView',
    'BugRelatedObjectEditView',
    'BugAlsoReportInView',
    'BugContextMenu',
    'BugWithoutContextView',
    'DeprecatedAssignedBugsView',
    'BugTextView']

from zope.component import getUtility
from zope.security.interfaces import Unauthorized

from canonical.launchpad.webapp import (
    canonical_url, ContextMenu, Link, structured, Navigation, LaunchpadView)
from canonical.launchpad.interfaces import (
    IBug, ILaunchBag, IBugSet, IBugTaskSet, IBugLinkTarget,
    IDistroBugTask, IDistroReleaseBugTask, NotFoundError)
from canonical.launchpad.browser.addview import SQLObjectAddView
from canonical.launchpad.browser.editview import SQLObjectEditView
from canonical.launchpad.webapp import GeneralFormView, stepthrough
from canonical.launchpad.helpers import check_permission


class BugSetNavigation(Navigation):

    usedfor = IBugSet

    # XXX
    # The browser:page declaration should be sufficient, but the traversal
    # takes priority. This is a workaround.
    # https://launchpad.net/products/launchpad/+bug/30238
    # -- Daf 2006/02/01

    @stepthrough('+text')
    def text(self, name):
        try:
            return getUtility(IBugSet).getByNameOrID(name)
        except (NotFoundError, ValueError):
            return None

    def traverse(self, name):
        try:
            return getUtility(IBugSet).getByNameOrID(name)
        except (NotFoundError, ValueError):
            # If the bug is not found, we expect a NotFoundError. If the
            # value of name is not a value that can be used to retrieve
            # a specific bug, we expect a ValueError.
            return None


class BugContextMenu(ContextMenu):
    usedfor = IBug
    links = ['editdescription', 'visibility', 'markduplicate', 'subscription',
             'addsubscriber', 'addattachment', 'linktocve', 'unlinkcve',
             'addwatch', 'filebug', 'activitylog', 'targetfix']

    def __init__(self, context):
        # Always force the context to be the current bugtask, so that we don't
        # have to duplicate menu code.
        ContextMenu.__init__(self, getUtility(ILaunchBag).bugtask)

    def editdescription(self):
        text = 'Edit Description'
        return Link('+edit', text, icon='edit')

    def visibility(self):
        text = 'Bug Visibility'
        return Link('+secrecy', text, icon='edit')

    def markduplicate(self):
        text = 'Mark as Duplicate'
        return Link('+duplicate', text, icon='edit')

    def subscription(self):
        user = getUtility(ILaunchBag).user
        
        if user is None:
            text = 'Your Subscription'
        elif user is not None and self.context.bug.isSubscribed(user):
            text = 'Unsubscribe'
        else:
            text = 'Subscribe'
        return Link('+subscribe', text, icon='add')

    def addsubscriber(self):
        text = 'Subscribe Someone Else'
        return Link('+addsubscriber', text, icon='add')

    def addattachment(self):
        text = 'Add Attachment'
        return Link('+addattachment', text, icon='add')

    def linktocve(self):
        text = structured(
            'Link to '
            '<abbr title="Common Vulnerabilities and Exposures Index">'
            'CVE'
            '</abbr>')
        return Link('+linkcve', text, icon='add')

    def unlinkcve(self):
        enabled = bool(self.context.bug.cves)
        text = 'Remove CVE Link'
        return Link('+unlinkcve', text, icon='edit', enabled=enabled)

    def addwatch(self):
        text = 'Link to Other Bug Tracker'
        return Link('+addwatch', text, icon='add')

    def filebug(self):
        bugtarget = self.context.target
        linktarget = '%s/%s' % (canonical_url(bugtarget), '+filebug')
        text = 'Report a Bug in %s' % bugtarget.displayname
        return Link(linktarget, text, icon='add')

    def activitylog(self):
        text = 'Activity Log'
        return Link('+activity', text, icon='list')

    def targetfix(self):
        enabled = (
            IDistroBugTask.providedBy(self.context) or
            IDistroReleaseBugTask.providedBy(self.context))
        text = 'Target Fix to Releases'
        return Link('+target', text, icon='milestone', enabled=enabled)


class BugView:
    """View class for presenting information about an IBug."""

    def __init__(self, context, request):
        self.context = IBug(context)
        self.request = request

    def currentBugTask(self):
        """Return the current IBugTask.

        'current' is determined by simply looking in the ILaunchBag utility.
        """
        return getUtility(ILaunchBag).bugtask

    def taskLink(self, bugtask):
        """Return the proper link to the bugtask whether it's editable"""
        user = getUtility(ILaunchBag).user
        if check_permission('launchpad.Edit', user):
            return canonical_url(bugtask) + "/+editstatus"
        else:
            return canonical_url(bugtask) + "/+viewstatus"

    def getFixRequestRowCSSClassForBugTask(self, bugtask):
        """Return the fix request row CSS class for the bugtask.

        The class is used to style the bugtask's row in the "fix requested for"
        table on the bug page.
        """
        if bugtask == self.currentBugTask():
            # The "current" bugtask is highlighted.
            return 'highlight'
        else:
            # Anything other than the "current" bugtask gets no
            # special row styling.
            return ''

    @property
    def subscription(self):
        """Return whether the current user is subscribed."""
        user = getUtility(ILaunchBag).user
        if user is None:
            return False
        return self.context.isSubscribed(user)

    def duplicates(self):
        """Return a list of dicts with the id and title of this bug dupes.

        If the bug isn't accessible to the user, the title stored in the dict
        will be 'Private Bug'
        """
        dupes = []
        for bug in self.context.duplicates:
            dupe = {}
            try:
                dupe['title'] = bug.title
            except Unauthorized:
                dupe['title'] = 'Private Bug'
            dupe['id'] = bug.id
            dupes.append(dupe)
        return dupes


class BugWithoutContextView:
    """View that redirects to the new bug page.

    The user is redirected, to the oldest IBugTask ('oldest' being
    defined as the IBugTask with the smallest ID.)
    """
    def redirectToNewBugPage(self):
        """Redirect the user to the 'first' report of this bug."""
        # An example of practicality beating purity.
        bugtasks = sorted(self.context.bugtasks, key=lambda task: task.id)

        self.request.response.redirect(canonical_url(bugtasks[0]))


class BugAlsoReportInView(SQLObjectAddView):
    """View class for reporting a bug in other contexts."""

    def create(self, product=None, distribution=None, sourcepackagename=None):
        """Create new bug task.

        Only one of product and distribution may be not None, and
        if product is None, sourcepackagename has to be None.
        """
        self.taskadded = getUtility(IBugTaskSet).createTask(
            self.context.bug,
            getUtility(ILaunchBag).user,
            product=product,
            distribution=distribution, sourcepackagename=sourcepackagename)
        return self.taskadded

    def nextURL(self):
        """Return the user to the URL of the task they just added."""
        return canonical_url(self.taskadded)


class BugSetView:
    """The default view for /malone/bugs.

    Essentially, this exists only to allow forms to post IDs here and be
    redirected to the right place.
    """

    def redirectToBug(self):
        bug_id = self.request.form.get("id")
        if bug_id:
            return self.request.response.redirect(bug_id)
        return self.request.response.redirect("/malone")


class BugEditView(BugView, SQLObjectEditView):
    """The view for the edit bug page."""
    def __init__(self, context, request):
        self.current_bugtask = context
        context = IBug(context)
        BugView.__init__(self, context, request)
        SQLObjectEditView.__init__(self, context, request)

    def changed(self):
        self.request.response.redirect(canonical_url(self.current_bugtask))


class BugRelatedObjectEditView(SQLObjectEditView):
    """View class for edit views of bug-related object.

    Examples would include the edit cve page, edit subscription page,
    etc.
    """
    def __init__(self, context, request):
        SQLObjectEditView.__init__(self, context, request)
        # Store the current bug in an attribute of the view, so that
        # ZPT rendering code can access it.
        self.bug = getUtility(ILaunchBag).bug

    def changed(self):
        """Redirect to the bug page."""
        bugtask = getUtility(ILaunchBag).bugtask
        self.request.response.redirect(canonical_url(bugtask))


class BugLinkView(GeneralFormView):
    """This view will be used for objects that support IBugLinkTarget, and
    so can be linked and unlinked from bugs.
    """

    def process(self, bug):
        # we are not creating, but we need to find the bug from the bug num
        try:
            malone_bug = getUtility(IBugSet).get(bug)
        except NotFoundError:
            return 'No malone bug #%s' % str(bug)
        user = getUtility(ILaunchBag).user
        assert IBugLinkTarget.providedBy(self.context)
        self._nextURL = canonical_url(self.context)
        return self.context.linkBug(malone_bug, user)


class BugUnlinkView(GeneralFormView):
    """This view will be used for objects that support IBugLinkTarget, and
    thus can be unlinked from bugs.
    """

    def process(self, bug):
        try:
            malone_bug = getUtility(IBugSet).get(bug)
        except NotFoundError:
            return 'No malone bug #%s' % str(bug)
        user = getUtility(ILaunchBag).user
        self._nextURL = canonical_url(self.context)
        return self.context.unlinkBug(malone_bug, user)


class DeprecatedAssignedBugsView:
    """Deprecate the /malone/assigned namespace.

    It's important to ensure that this namespace continues to work, to
    prevent linkrot, but since FOAF seems to be a more natural place
    to put the assigned bugs report, we'll redirect to the appropriate
    FOAF URL.
    """
    def __init__(self, context, request):
        """Redirect the user to their assigned bugs report."""
        self.context = context
        self.request = request

    def redirect_to_assignedbugs(self):
        self.request.response.redirect(
            canonical_url(getUtility(ILaunchBag).user) +
            "/+assignedbugs")


class BugTextView(LaunchpadView):
    """View for simple text page displaying information for a bug."""

    def person_text(self, person):
        return '%s (%s)' % (person.displayname, person.name)

    def bug_text(self, bug):
        text = []
        text.append('bug: %d' % bug.id)
        text.append('title: %s' % bug.title)
        text.append('reporter: %s' % self.person_text(bug.owner))

        if bug.duplicateof:
            text.append('duplicate-of: %d' % bug.duplicateof.id)
        else:
            text.append('duplicate-of: ')

        text.append('subscribers: ')

        for subscription in bug.subscriptions:
            text.append(' %s' % self.person_text(subscription.person))

        return ''.join(line + '\n' for line in text)

    def bugtask_text(self, task):
        text = []
        text.append('task: %s' % task.targetname)
        text.append('status: %s' % task.status.title)
        text.append('reporter: %s' % self.person_text(task.owner))

        if task.priority:
            text.append('priority: %s' % task.priority.title)
        else:
            text.append('priority: ')

        text.append('severity: %s' % task.severity.title)

        if task.assignee:
            text.append('assignee: %s' % self.person_text(task.assignee))
        else:
            text.append('assignee: ')

        if task.milestone:
            text.append('milestone: %s' % task.milestone.name)
        else:
            text.append('milestone: ')

        return ''.join(line + '\n' for line in text)

    def render(self):
        self.request.response.setHeader('Content-type', 'text/plain')
        texts = (
            [self.bug_text(self.context)] +
            [self.bugtask_text(task) for task in self.context.bugtasks])
        return u'\n'.join(texts)

