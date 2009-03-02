# Copyright 2005 Canonical Ltd.  All rights reserved.

"""Base class view for branch listings."""

__metaclass__ = type

__all__ = [
    'BranchListingView',
    'PersonBranchesMenu',
    'PersonBranchesView',
    'PersonCodeSummaryView',
    'PersonOwnedBranchesView',
    'PersonRegisteredBranchesView',
    'PersonSubscribedBranchesView',
    'PersonTeamBranchesView',
    'ProductBranchListingView',
    'ProductBranchOverviewView',
    'ProductBranchesMenu',
    'ProductBranchesView',
    'ProductCodeIndexView',
    'ProjectBranchesView',
    'RecentlyChangedBranchesView',
    'RecentlyImportedBranchesView',
    'RecentlyRegisteredBranchesView',
    'SourcePackageBranchesView',
    ]

from datetime import datetime

from storm.expr import Asc, Desc
import pytz
from zope.component import getUtility
from zope.interface import implements, Interface
from zope.formlib import form
from zope.schema import Choice

from canonical.config import config

from canonical.cachedproperty import cachedproperty
from canonical.launchpad import _
from canonical.launchpad.browser.branch import BranchBadges
from canonical.launchpad.browser.feeds import (
    FeedsMixin, PersonBranchesFeedLink, PersonRevisionsFeedLink,
    ProductBranchesFeedLink, ProductRevisionsFeedLink,
    ProjectBranchesFeedLink, ProjectRevisionsFeedLink)
from canonical.launchpad.browser.product import (
    ProductDownloadFileMixin, SortSeriesMixin)
from canonical.launchpad.interfaces import (
    IBugBranchSet,
    IProductSeriesSet,
    IRevisionSet,
    ISpecificationBranchSet)
from canonical.launchpad.interfaces.branch import (
    bazaar_identity, BranchLifecycleStatus, BranchLifecycleStatusFilter,
    BranchPersonSearchContext, BranchPersonSearchRestriction,
    DEFAULT_BRANCH_STATUS_IN_LISTING, IBranch, IBranchBatchNavigator,
    IBranchSet)
from canonical.launchpad.interfaces.branchmergeproposal import (
    BranchMergeProposalStatus, IBranchMergeProposalGetter)
from canonical.launchpad.interfaces.distroseries import DistroSeriesStatus
from canonical.launchpad.interfaces.person import IPerson, IPersonSet
from canonical.launchpad.interfaces.product import IProduct
from canonical.launchpad.webapp import (
    ApplicationMenu, canonical_url, custom_widget, enabled_with_permission,
    LaunchpadFormView, Link)
from canonical.launchpad.webapp.authorization import check_permission
from canonical.launchpad.webapp.batching import TableBatchNavigator
from canonical.launchpad.webapp.publisher import LaunchpadView
from canonical.lazr.enum import EnumeratedType, Item
from canonical.widgets import LaunchpadDropdownWidget
from lazr.delegates import delegates


class BranchListingItem(BranchBadges):
    """A decorated branch.

    Some attributes that we want to display are too convoluted or expensive
    to get on the fly for each branch in the listing.  These items are
    prefetched by the view and decorate the branch.
    """
    delegates(IBranch, 'context')

    def __init__(self, branch, last_commit, now, show_bug_badge,
                 show_blueprint_badge, is_dev_focus,
                 associated_product_series):
        BranchBadges.__init__(self, branch)
        self.last_commit = last_commit
        self.show_bug_badge = show_bug_badge
        self.show_blueprint_badge = show_blueprint_badge
        self._now = now
        self.is_development_focus = is_dev_focus
        self.associated_product_series = associated_product_series

    @property
    def active_series(self):
        return [series for series in self.associated_product_series
                if series.status != DistroSeriesStatus.OBSOLETE]

    @property
    def bzr_identity(self):
        """Produce the bzr identity from our known associated series."""
        return bazaar_identity(
            self.context, self.associated_product_series,
            self.is_development_focus)

    @property
    def since_updated(self):
        """How long since the branch was last updated."""
        return self._now - self.context.date_last_modified

    @property
    def since_created(self):
        """How long since the branch was created."""
        return self._now - self.context.date_created

    def isBugBadgeVisible(self):
        return self.show_bug_badge

    def isBlueprintBadgeVisible(self):
        return self.show_blueprint_badge

    @property
    def revision_author(self):
        return self.last_commit.revision_author

    @property
    def revision_number(self):
        return self.context.revision_count

    @property
    def revision_log(self):
        return self.last_commit.log_body

    @property
    def revision_date(self):
        return self.last_commit.revision_date

    @property
    def revision_codebrowse_link(self):
        return self.context.codebrowse_url(
            'revision', str(self.context.revision_count))


class BranchListingSort(EnumeratedType):
    """Choices for how to sort branch listings."""

    # XXX: MichaelHudson 2007-10-17 bug=153891: We allow sorting on quantities
    # that are not visible in the listing!

    DEFAULT = Item("""
        by most interesting

        Sort branches by the default ordering for the view.
        """)

    PRODUCT = Item("""
        by project name

        Sort branches by name of the project the branch is for.
        """)

    LIFECYCLE = Item("""
        by lifecycle status

        Sort branches by the lifecycle status.
        """)

    NAME = Item("""
        by branch name

        Sort branches by the display name of the registrant.
        """)

    REGISTRANT = Item("""
        by registrant name

        Sort branches by the display name of the registrant.
        """)

    MOST_RECENTLY_CHANGED_FIRST = Item("""
        most recently changed first

        Sort branches from the most recently to the least recently
        changed.
        """)

    LEAST_RECENTLY_CHANGED_FIRST = Item("""
        least recently changed first

        Sort branches from the least recently to the most recently
        changed.
        """)

    NEWEST_FIRST = Item("""
        newest first

        Sort branches from newest to oldest.
        """)

    OLDEST_FIRST = Item("""
        oldest first

        Sort branches from oldest to newest.
        """)


class IBranchListingFilter(Interface):
    """The schema for the branch listing filtering/ordering form."""

    # Stats and status attributes
    lifecycle = Choice(
        title=_('Lifecycle Filter'), vocabulary=BranchLifecycleStatusFilter,
        default=BranchLifecycleStatusFilter.CURRENT,
        description=_(
        "The author's assessment of the branch's maturity. "
        " Mature: recommend for production use."
        " Development: useful work that is expected to be merged eventually."
        " Experimental: not recommended for merging yet, and maybe ever."
        " Merged: integrated into mainline, of historical interest only."
        " Abandoned: no longer considered relevant by the author."
        " New: unspecified maturity."))

    sort_by = Choice(
        title=_('ordered by'), vocabulary=BranchListingSort,
        default=BranchListingSort.LIFECYCLE)


class BranchListingBatchNavigator(TableBatchNavigator):
    """Batch up the branch listings."""
    implements(IBranchBatchNavigator)

    def __init__(self, view):
        TableBatchNavigator.__init__(
            self, view.getVisibleBranchesForUser(), view.request,
            columns_to_show=view.extra_columns,
            size=config.launchpad.branchlisting_batch_size)
        self.view = view
        self.column_count = 4 + len(view.extra_columns)
        self._now = datetime.now(pytz.UTC)
        self._dev_series_map = {}

    @cachedproperty
    def _branches_for_current_batch(self):
        return list(self.currentBatch())

    @cachedproperty
    def has_bug_branch_links(self):
        """Return a set of branch ids that should show bug badges."""
        bug_branches = getUtility(IBugBranchSet).getBugBranchesForBranches(
            self._branches_for_current_batch, self.view.user)
        result = set()
        for bug_branch in bug_branches:
            result.add(bug_branch.branch.id)
        return result

    @cachedproperty
    def has_branch_spec_links(self):
        """Return a set of branch ids that should show blueprint badges."""
        spec_branches = getUtility(
            ISpecificationBranchSet).getSpecificationBranchesForBranches(
            self._branches_for_current_batch, self.view.user)
        result = set()
        for spec_branch in spec_branches:
            result.add(spec_branch.branch.id)
        return result

    @cachedproperty
    def tip_revisions(self):
        """Return a set of branch ids that should show blueprint badges."""
        revisions = getUtility(IRevisionSet).getTipRevisionsForBranches(
            self._branches_for_current_batch)
        if revisions is None:
            revision_map = {}
        else:
            # Key the revisions by revision id.
            revision_map = dict((revision.revision_id, revision)
                                for revision in revisions)
        # Return a dict keyed on branch id.
        return dict((branch.id, revision_map.get(branch.last_scanned_id))
                     for branch in self._branches_for_current_batch)

    @cachedproperty
    def product_series_map(self):
        """Return a map of branch id to a list of product series."""
        series_resultset = getUtility(IProductSeriesSet).getSeriesForBranches(
            self._branches_for_current_batch)
        result = {}
        for series in series_resultset:
            result.setdefault(series.series_branch.id, []).append(series)
        return result

    def getProductSeries(self, branch):
        """Get the associated product series for the branch.

        If the branch has more than one associated product series
        they are listed in alphabetical order, unless one of them is
        the current development focus, in which case that comes first.
        """
        series = self.product_series_map.get(branch.id, [])
        if len(series) > 1:
            # Check for development focus.
            dev_focus = branch.product.development_focus
            if dev_focus is not None and dev_focus in series:
                series.remove(dev_focus)
                series.insert(0, dev_focus)
        return series

    def getDevFocusBranch(self, branch):
        """Get the development focus branch that relates to `branch`."""
        if branch.product is None:
            return None
        try:
            return self._dev_series_map[branch.product]
        except KeyError:
            result = branch.product.development_focus.series_branch
            self._dev_series_map[branch.product] = result
            return result

    def _createItem(self, branch):
        last_commit = self.tip_revisions[branch.id]
        show_bug_badge = branch.id in self.has_bug_branch_links
        show_blueprint_badge = branch.id in self.has_branch_spec_links
        associated_product_series = self.getProductSeries(branch)
        is_dev_focus = (self.getDevFocusBranch(branch) == branch)
        return BranchListingItem(
            branch, last_commit, self._now, show_bug_badge,
            show_blueprint_badge, is_dev_focus, associated_product_series)

    def branches(self):
        """Return a list of BranchListingItems."""
        return [self._createItem(branch)
                for branch in self._branches_for_current_batch]

    @cachedproperty
    def multiple_pages(self):
        return self.batch.total() > self.batch.size

    @property
    def table_class(self):
        # XXX: MichaelHudson 2007-10-18 bug=153894: This means there are two
        # ways of sorting a one-page branch listing, which is a confusing and
        # incoherent.
        if self.multiple_pages:
            return "listing"
        else:
            return "listing sortable"


class BranchListingView(LaunchpadFormView, FeedsMixin):
    """A base class for views of branch listings."""
    schema = IBranchListingFilter
    field_names = ['lifecycle', 'sort_by']
    development_focus_branch = None
    show_set_development_focus = False
    custom_widget('lifecycle', LaunchpadDropdownWidget)
    custom_widget('sort_by', LaunchpadDropdownWidget)
    # Showing the series links is only really useful on product listing
    # pages.  Derived views can override this value to have the series links
    # shown in the branch listings.
    show_series_links = False
    extra_columns = []
    heading_template = 'Bazaar branches for %(displayname)s'
    # no_sort_by is a sequence of items from the BranchListingSort
    # enumeration to not offer in the sort_by widget.
    no_sort_by = ()

    # Set the feed types to be only the various branches feed links.  The
    # `feed_links` property will screen this list and produce only the feeds
    # appropriate to the context.
    feed_types = (
        ProjectBranchesFeedLink,
        ProjectRevisionsFeedLink,
        ProductBranchesFeedLink,
        ProductRevisionsFeedLink,
        PersonBranchesFeedLink,
        PersonRevisionsFeedLink,
        )

    @property
    def heading(self):
        return self.heading_template % {
            'displayname': self.context.displayname}

    @property
    def initial_values(self):
        return {
            'lifecycle': BranchLifecycleStatusFilter.CURRENT,
            }

    @cachedproperty
    def selected_lifecycle_status(self):
        widget = self.widgets['lifecycle']

        if widget.hasValidInput():
            lifecycle_filter = widget.getInputValue()
        else:
            lifecycle_filter = BranchLifecycleStatusFilter.CURRENT

        if lifecycle_filter == BranchLifecycleStatusFilter.ALL:
            return None
        elif lifecycle_filter == BranchLifecycleStatusFilter.CURRENT:
            return DEFAULT_BRANCH_STATUS_IN_LISTING
        else:
            return (BranchLifecycleStatus.items[lifecycle_filter.name], )

    def branches(self):
        """All branches related to this target, sorted for display."""
        # Separate the public property from the underlying virtual method.
        return BranchListingBatchNavigator(self)

    def getVisibleBranchesForUser(self):
        """Get branches visible to the user.

        This method is called from the `BranchListingBatchNavigator` to
        get the branches to show in the listing.
        """
        return self._branches(self.selected_lifecycle_status)

    def hasAnyBranchesVisibleByUser(self):
        """Does the context have any branches that are visible to the user?"""
        return self._branches(None).count() > 0

    @property
    def branch_search_context(self):
        """The context used for the branch search."""
        return self.context

    def _branches(self, lifecycle_status):
        """Return a sequence of branches.

        This method is overridden in the derived classes to perform the
        specific query.

        :param lifecycle_status: A filter of the branch's lifecycle status.
        """
        branches = getUtility(IBranchSet).getBranchesForContext(
            self.branch_search_context, lifecycle_status, self.user)
        return branches.order_by(self._listingSortToOrderBy(self.sort_by))

    @property
    def no_branch_message(self):
        """This may also be overridden in derived classes to provide
        context relevant messages if there are no branches returned."""
        if (self.selected_lifecycle_status is not None
            and self.hasAnyBranchesVisibleByUser()):
            message = (
                'There are branches related to %s but none of them match the '
                'current filter criteria for this page. '
                'Try filtering on "Any Status".')
        else:
            message = (
                'There are no branches related to %s '
                'in Launchpad today. You can use Launchpad as a registry for '
                'Bazaar branches, and encourage broader community '
                'participation in your project using '
                'distributed version control.')
        return message % self.context.displayname

    @property
    def branch_listing_sort_values(self):
        """The enum items we should present in the 'sort_by' widget.

        Subclasses get the chance to avoid some sort options (it makes no
        sense to offer to sort the product branch listing by product name!)
        and if we're filtering to a single lifecycle status it doesn't make
        much sense to sort by lifecycle.
        """
        # This is pretty painful.
        # First we find the items which are not excluded for this view.
        vocab_items = [item for item in BranchListingSort.items.items
                       if item not in self.no_sort_by]
        # Finding the value of the lifecycle_filter widget is awkward as we do
        # this when the widgets are being set up.  We go digging in the
        # request.
        lifecycle_field = IBranchListingFilter['lifecycle']
        name = self.prefix + '.' + lifecycle_field.__name__
        form_value = self.request.form.get(name)
        if form_value is not None:
            try:
                status_filter = BranchLifecycleStatusFilter.getTermByToken(
                    form_value).value
            except LookupError:
                # We explicitly support bogus values in field.lifecycle --
                # they are treated the same as "CURRENT", which includes more
                # than one lifecycle.
                pass
            else:
                if status_filter not in (BranchLifecycleStatusFilter.ALL,
                                         BranchLifecycleStatusFilter.CURRENT):
                    vocab_items.remove(BranchListingSort.LIFECYCLE)
        return vocab_items

    @property
    def sort_by_field(self):
        """The zope.schema field for the 'sort_by' widget."""
        orig_field = IBranchListingFilter['sort_by']
        values = self.branch_listing_sort_values
        return Choice(__name__=orig_field.__name__,
                      title=orig_field.title,
                      required=True, values=values, default=values[0])

    @property
    def sort_by(self):
        """The value of the `sort_by` widget, or None if none was present."""
        widget = self.widgets['sort_by']
        if widget.hasValidInput():
            return widget.getInputValue()
        else:
            return None

    @staticmethod
    def _listingSortToOrderBy(sort_by):
        """Compute a value to pass as orderBy to Branch.select().

        :param sort_by: an item from the BranchListingSort enumeration.
        """
        from canonical.launchpad.database.branch import Branch
        from canonical.launchpad.database.person import Owner
        from canonical.launchpad.database.product import Product

        DEFAULT_BRANCH_LISTING_SORT = [
            BranchListingSort.PRODUCT,
            BranchListingSort.LIFECYCLE,
            BranchListingSort.REGISTRANT,
            BranchListingSort.NAME,
            ]

        LISTING_SORT_TO_COLUMN = {
            BranchListingSort.PRODUCT: (Asc, Product.name),
            BranchListingSort.LIFECYCLE: (Desc, Branch.lifecycle_status),
            BranchListingSort.NAME: (Asc, Branch.name),
            BranchListingSort.REGISTRANT: (Asc, Owner.name),
            BranchListingSort.MOST_RECENTLY_CHANGED_FIRST: (
                Desc, Branch.date_last_modified),
            BranchListingSort.LEAST_RECENTLY_CHANGED_FIRST: (
                Asc, Branch.date_last_modified),
            BranchListingSort.NEWEST_FIRST: (Desc, Branch.date_created),
            BranchListingSort.OLDEST_FIRST: (Asc, Branch.date_created),
            }

        order_by = map(
            LISTING_SORT_TO_COLUMN.get, DEFAULT_BRANCH_LISTING_SORT)

        if sort_by is not None:
            direction, column = LISTING_SORT_TO_COLUMN[sort_by]
            order_by = (
                [(direction, column)] +
                [sort for sort in order_by if sort[1] is not column])
        return [direction(column) for direction, column in order_by]

    def setUpWidgets(self, context=None):
        """Set up the 'sort_by' widget with only the applicable choices."""
        fields = []
        for field_name in self.field_names:
            if field_name == 'sort_by':
                field = form.FormField(self.sort_by_field)
            else:
                field = self.form_fields[field_name]
            fields.append(field)
        self.form_fields = form.Fields(*fields)
        super(BranchListingView, self).setUpWidgets(context)


class NoContextBranchListingView(BranchListingView):
    """A branch listing that has no associated product or person."""

    field_names = ['lifecycle']
    no_sort_by = (BranchListingSort.DEFAULT,)

    no_branch_message = (
        'There are no branches that match the current status filter.')
    extra_columns = ('author', 'product', 'date_created')


class RecentlyRegisteredBranchesView(NoContextBranchListingView):
    """A batched view of branches orded by registration date."""

    page_title = 'Recently registered branches'

    def _branches(self, lifecycle_status):
        """Return the branches ordered by date created."""
        return getUtility(IBranchSet).getRecentlyRegisteredBranches(
            lifecycle_statuses=lifecycle_status,
            visible_by_user=self.user)


class RecentlyImportedBranchesView(NoContextBranchListingView):
    """A batched view of imported branches ordered by last scanned time."""

    page_title = 'Recently imported branches'
    extra_columns = ('product', 'date_created')

    def _branches(self, lifecycle_status):
        """Return imported branches ordered by last update."""
        return getUtility(IBranchSet).getRecentlyImportedBranches(
            lifecycle_statuses=lifecycle_status,
            visible_by_user=self.user)


class RecentlyChangedBranchesView(NoContextBranchListingView):
    """Batched view of non-imported branches ordered by last scanned time."""

    page_title = 'Recently changed branches'

    def _branches(self, lifecycle_status):
        """Return non-imported branches orded by last commit."""
        return getUtility(IBranchSet).getRecentlyChangedBranches(
            lifecycle_statuses=lifecycle_status,
            visible_by_user=self.user)


class PersonBranchCountMixin:
    """A mixin class for person branch listings."""

    @cachedproperty
    def total_branch_count(self):
        """Return the number of branches related to the person."""
        query = getUtility(IBranchSet).getBranchesForContext(
            self.context, visible_by_user=self.user)
        return query.count()

    @cachedproperty
    def registered_branch_count(self):
        """Return the number of branches registered by the person."""
        query = getUtility(IBranchSet).getBranchesForContext(
            BranchPersonSearchContext(
                self.context, BranchPersonSearchRestriction.REGISTERED),
            visible_by_user=self.user)
        return query.count()

    @cachedproperty
    def owned_branch_count(self):
        """Return the number of branches owned by the person."""
        query = getUtility(IBranchSet).getBranchesForContext(
            BranchPersonSearchContext(
                self.context, BranchPersonSearchRestriction.OWNED),
            visible_by_user=self.user)
        return query.count()

    @cachedproperty
    def subscribed_branch_count(self):
        """Return the number of branches subscribed to by the person."""
        query = getUtility(IBranchSet).getBranchesForContext(
            BranchPersonSearchContext(
                self.context, BranchPersonSearchRestriction.SUBSCRIBED),
            visible_by_user=self.user)
        return query.count()

    @property
    def user_in_context_team(self):
        if self.user is None:
            return False
        return self.user.inTeam(self.context)

    @cachedproperty
    def active_review_count(self):
        """Return the number of active reviews for the user."""
        query = getUtility(IBranchMergeProposalGetter).getProposalsForContext(
            self.context, [BranchMergeProposalStatus.NEEDS_REVIEW], self.user)
        return query.count()

    @cachedproperty
    def approved_merge_count(self):
        """Return the number of active reviews for the user."""
        query = getUtility(IBranchMergeProposalGetter).getProposalsForContext(
            self.context, [BranchMergeProposalStatus.CODE_APPROVED],
            self.user)
        return query.count()

    @cachedproperty
    def requested_review_count(self):
        """Return the number of active reviews for the user."""
        utility = getUtility(IBranchMergeProposalGetter)
        query = utility.getProposalsForReviewer(
            self.context, [
                BranchMergeProposalStatus.CODE_APPROVED,
                BranchMergeProposalStatus.NEEDS_REVIEW],
            self.user)
        return query.count()


class PersonBranchesMenu(ApplicationMenu, PersonBranchCountMixin):

    usedfor = IPerson
    facet = 'branches'
    links = ['all_related', 'registered', 'owned', 'subscribed', 'addbranch',
             'active_reviews', 'approved_merges', 'requested_reviews']

    def all_related(self):
        return Link(canonical_url(self.context, rootsite='code'),
                    'Related branches')

    def owned(self):
        return Link('+ownedbranches', 'owned')

    def registered(self):
        return Link('+registeredbranches', 'registered')

    def subscribed(self):
        return Link('+subscribedbranches', 'subscribed')

    def active_reviews(self):
        if self.active_review_count == 1:
            text = 'active proposal'
        else:
            text = 'active proposals'
        if self.user == self.context:
            summary = 'Proposals I have submitted'
        else:
            summary = 'Proposals %s has submitted' % self.context.displayname
        return Link('+activereviews', text, summary=summary)

    def approved_merges(self):
        if self.approved_merge_count == 1:
            text = 'approved merge'
        else:
            text = 'approved merges'
        return Link('+approvedmerges', text)

    def addbranch(self):
        if self.user is None:
            enabled = False
        else:
            enabled = self.user.inTeam(self.context)
        text = 'Register branch'
        return Link('+addbranch', text, icon='add', enabled=enabled)

    def requested_reviews(self):
        if self.requested_review_count == 1:
            text = 'requested review'
        else:
            text = 'requested reviews'
        if self.user == self.context:
            summary = 'Proposals I am reviewing'
        else:
            summary = 'Proposals %s is reviewing' % self.context.displayname
        return Link('+requestedreviews', text, summary=summary)


class PersonBranchesView(BranchListingView, PersonBranchCountMixin):
    """View for branch listing for a person."""

    no_sort_by = (BranchListingSort.DEFAULT,)
    heading_template = 'Bazaar branches related to %(displayname)s'


class PersonRegisteredBranchesView(BranchListingView, PersonBranchCountMixin):
    """View for branch listing for a person's registered branches."""

    heading_template = 'Bazaar branches registered by %(displayname)s'
    no_sort_by = (BranchListingSort.DEFAULT, BranchListingSort.REGISTRANT)

    @property
    def branch_search_context(self):
        """See `BranchListingView`."""
        return BranchPersonSearchContext(
            self.context, BranchPersonSearchRestriction.REGISTERED)


class PersonOwnedBranchesView(BranchListingView, PersonBranchCountMixin):
    """View for branch listing for a person's owned branches."""

    heading_template = 'Bazaar branches owned by %(displayname)s'
    no_sort_by = (BranchListingSort.DEFAULT, BranchListingSort.REGISTRANT)

    @property
    def branch_search_context(self):
        """See `BranchListingView`."""
        return BranchPersonSearchContext(
            self.context, BranchPersonSearchRestriction.OWNED)


class PersonSubscribedBranchesView(BranchListingView, PersonBranchCountMixin):
    """View for branch listing for a person's subscribed branches."""

    heading_template = 'Bazaar branches subscribed to by %(displayname)s'
    no_sort_by = (BranchListingSort.DEFAULT,)

    @property
    def branch_search_context(self):
        """See `BranchListingView`."""
        return BranchPersonSearchContext(
            self.context, BranchPersonSearchRestriction.SUBSCRIBED)


class PersonTeamBranchesView(LaunchpadView):
    """View for team branches portlet."""

    @cachedproperty
    def teams_with_branches(self):
        def team_has_branches(team):
            branches = getUtility(IBranchSet).getBranchesForContext(
                team, visible_by_user=self.user)
            return branches.count() > 0
        return [team for team in self.context.teams_participated_in
                if team_has_branches(team) and team != self.context]


class PersonCodeSummaryView(LaunchpadView, PersonBranchCountMixin):
    """A view to render the code page summary for a person."""

    __used_for__ = IPerson

    @property
    def show_summary(self):
        """Right now we show the summary if the person has branches.

        When we add support for reviews commented on, we'll want to add
        support for showing the summary even if there are no branches.
        """
        return self.total_branch_count or self.requested_review_count


class ProductReviewCountMixin:
    """A mixin used by the menu and the code index view."""

    @cachedproperty
    def active_review_count(self):
        """Return the number of active reviews for the user."""
        query = getUtility(IBranchMergeProposalGetter).getProposalsForContext(
            self.context, [BranchMergeProposalStatus.NEEDS_REVIEW], self.user)
        return query.count()

    @cachedproperty
    def approved_merge_count(self):
        """Return the number of active reviews for the user."""
        query = getUtility(IBranchMergeProposalGetter).getProposalsForContext(
            self.context, [BranchMergeProposalStatus.CODE_APPROVED],
            self.user)
        return query.count()


class ProductBranchesMenu(ApplicationMenu, ProductReviewCountMixin):

    usedfor = IProduct
    facet = 'branches'
    links = [
        'branch_add',
        'list_branches',
        'active_reviews',
        'approved_merges',
        'code_import',
        'branch_visibility',
        ]

    def branch_add(self):
        text = 'Register a branch'
        summary = 'Register a new Bazaar branch for this project'
        return Link('+addbranch', text, summary, icon='add')

    def list_branches(self):
        text = 'List branches'
        summary = 'List the branches for this project'
        return Link('+branches', text, summary, icon='add')

    def active_reviews(self):
        if self.active_review_count == 1:
            text = 'pending proposal'
        else:
            text = 'pending proposals'
        return Link('+activereviews', text)

    def approved_merges(self):
        if self.approved_merge_count == 1:
            text = 'unmerged proposal'
        else:
            text = 'unmerged proposals'
        return Link('+approvedmerges', text)

    @enabled_with_permission('launchpad.Admin')
    def branch_visibility(self):
        text = 'Define branch visibility'
        return Link('+branchvisibility', text, icon='edit')

    def code_import(self):
        text = 'Import your project'
        enabled = not self.context.official_codehosting
        return Link('/+code-imports/+new', text, icon='add', enabled=enabled)


class ProductBranchOverviewView(LaunchpadView, SortSeriesMixin, FeedsMixin):
    """View for the product code overview."""

    __used_for__ = IProduct

    feed_types = (
        ProductBranchesFeedLink,
        )

    def initialize(self):
        self.product = self.context


class ProductBranchListingView(BranchListingView):
    """A base class for product branch listings."""

    show_series_links = True
    no_sort_by = (BranchListingSort.PRODUCT,)

    @cachedproperty
    def branch_count(self):
        """The number of total branches the user can see."""
        return getUtility(IBranchSet).getBranchesForContext(
            context=self.context, visible_by_user=self.user).count()

    @cachedproperty
    def development_focus_branch(self):
        dev_focus_branch = self.context.development_focus.series_branch
        if dev_focus_branch is None:
            return None
        elif check_permission('launchpad.View', dev_focus_branch):
            return dev_focus_branch
        else:
            return None

    @property
    def no_branch_message(self):
        if (self.selected_lifecycle_status is not None
            and self.hasAnyBranchesVisibleByUser()):
            message = (
                'There are branches registered for %s '
                'but none of them match the current filter criteria '
                'for this page. Try filtering on "Any Status".')
        else:
            message = (
                'There are no branches registered for %s '
                'in Launchpad today. We recommend you visit '
                '<a href="http://www.bazaar-vcs.org">www.bazaar-vcs.org</a> '
                'for more information about how you can use the Bazaar '
                'revision control system to improve community participation '
                'in this project.')
        return message % self.context.displayname


class ProductCodeIndexView(ProductBranchListingView, SortSeriesMixin,
                           ProductDownloadFileMixin, ProductReviewCountMixin):
    """Initial view for products on the code virtual host."""

    show_set_development_focus = True

    def initialize(self):
        ProductBranchListingView.initialize(self)
        self.product = self.context

    @property
    def form_action(self):
        return "+branches"

    @property
    def initial_values(self):
        return {
            'lifecycle': BranchLifecycleStatusFilter.CURRENT,
            'sort_by': BranchListingSort.DEFAULT,
            }

    @cachedproperty
    def _recent_revisions(self):
        """Revisions for this project created in the last 30 days."""
        # The actual number of revisions for any given project are likely
        # to be small(ish).  We also need to be able to traverse over the
        # actual revision authors in order to get an accurate count.
        revisions = list(
            getUtility(IRevisionSet).getRecentRevisionsForProduct(
                product=self.context, days=30))
        # XXX: thumper 2008-04-24
        # How best to warn if the limit is getting too large?
        # And how much is too much anyway.
        return revisions

    @property
    def commit_count(self):
        """The number of new revisions in the last 30 days."""
        return len(self._recent_revisions)

    @cachedproperty
    def committer_count(self):
        """The number of committers in the last 30 days."""
        # Record a set of tuples where the first part is a launchpad
        # person name if know, and the second part is the revision author
        # text.  Only one part of the tuple will be set.
        committers = set()
        for (revision, author) in self._recent_revisions:
            if author.personID is None:
                committers.add((None, author.name))
            else:
                committers.add((author.personID, None))
        return len(committers)

    @cachedproperty
    def _branch_owners(self):
        """The owners of branches."""
        # Listify the owners, there really shouldn't be that many for any
        # one project.
        return list(getUtility(IPersonSet).getPeopleWithBranches(
            product=self.context))

    @cachedproperty
    def person_owner_count(self):
        """The number of individual people who own branches."""
        return len([person for person in self._branch_owners
                    if not person.isTeam()])

    @cachedproperty
    def team_owner_count(self):
        """The number of teams who own branches."""
        return len([person for person in self._branch_owners
                    if person.isTeam()])

    def _getSeriesBranches(self):
        """Get the series branches for the product, dev focus first."""
        # We want to show each series branch only once, always show the
        # development focus branch, no matter what's it lifecycle status, and
        # skip subsequent series where the lifecycle status is Merged or
        # Abandoned
        sorted_series = self.sorted_active_series_list
        def show_branch(branch):
            if self.selected_lifecycle_status is None:
                return True
            else:
                return (branch.lifecycle_status in
                    self.selected_lifecycle_status)
        # The series will always have at least one series, that of the
        # development focus.
        dev_focus_branch = sorted_series[0].series_branch
        if not check_permission('launchpad.View', dev_focus_branch):
            dev_focus_branch = None
        result = []
        if dev_focus_branch is not None and show_branch(dev_focus_branch):
            result.append(dev_focus_branch)
        for series in sorted_series[1:]:
            branch = series.series_branch
            if (branch is not None and
                branch not in result and
                check_permission('launchpad.View', branch) and
                show_branch(branch)):
                result.append(branch)
        return result

    @cachedproperty
    def initial_branches(self):
        """Return the series branches, followed by most recently changed."""
        series_branches = self._getSeriesBranches()
        branch_query = getUtility(IBranchSet).getBranchesForContext(
            context=self.context, visible_by_user=self.user,
            lifecycle_statuses=self.selected_lifecycle_status)
        branch_query.order_by(self._listingSortToOrderBy(
            BranchListingSort.MOST_RECENTLY_CHANGED_FIRST))
        # We don't want the initial branch listing to be batched, so only get
        # the batch size - the number of series_branches.
        batch_size = config.launchpad.branchlisting_batch_size
        max_branches_from_query = batch_size - len(series_branches)
        # Since series branches are actual branches, and the query
        # returns the bastardised BranchWithSortColumns, we need to
        # check branch ids in the following list comprehension.
        series_branch_ids = set(branch.id for branch in series_branches)
        # We want to make sure that the series branches do not appear
        # in our branch list.
        branches = [
            branch for branch in branch_query[:max_branches_from_query]
            if branch.id not in series_branch_ids]
        series_branches.extend(branches)
        return series_branches

    def _branches(self, lifecycle_status):
        """Return the series branches, followed by most recently changed."""
        # The params are ignored, and only used by the listing view.
        return self.initial_branches

    @property
    def unseen_branch_count(self):
        """How many branches are not shown."""
        return self.branch_count - len(self.initial_branches)

    def hasAnyBranchesVisibleByUser(self):
        """See `BranchListingView`."""
        return self.branch_count > 0

    @property
    def has_development_focus_branch(self):
        """Is there a branch assigned as development focus?"""
        return self.development_focus_branch is not None

    def _getPluralText(self, count, singular, plural):
        if count == 1:
            return singular
        else:
            return plural

    @property
    def branch_text(self):
        return self._getPluralText(
            self.branch_count, _('branch'), _('branches'))

    @property
    def person_text(self):
        return self._getPluralText(
            self.person_owner_count, _('person'), _('people'))

    @property
    def team_text(self):
        return self._getPluralText(
            self.team_owner_count, _('team'), _('teams'))

    @property
    def commit_text(self):
        return self._getPluralText(
            self.commit_count, _('commit'), _('commits'))

    @property
    def committer_text(self):
        return self._getPluralText(
            self.committer_count, _('person'), _('people'))


class ProductBranchesView(ProductBranchListingView):
    """View for branch listing for a product."""

    def initialize(self):
        """Conditionally redirect to the default view.

        If the branch listing requests the default listing, redirect to the
        default view for the product.
        """
        ProductBranchListingView.initialize(self)
        if self.sort_by == BranchListingSort.DEFAULT:
            redirect_url = canonical_url(self.context)
            widget = self.widgets['lifecycle']
            if widget.hasValidInput():
                redirect_url += (
                    '?field.lifecycle=' + widget.getInputValue().name)
            self.request.response.redirect(redirect_url)

    @property
    def initial_values(self):
        return {
            'lifecycle': BranchLifecycleStatusFilter.CURRENT,
            'sort_by': BranchListingSort.LIFECYCLE,
            }


class ProjectBranchesView(BranchListingView):
    """View for branch listing for a project."""

    no_sort_by = (BranchListingSort.DEFAULT,)
    extra_columns = ('author', 'product')

    @property
    def no_branch_message(self):
        if (self.selected_lifecycle_status is not None
            and self.hasAnyBranchesVisibleByUser()):
            message = (
                'There are branches registered for %s '
                'but none of them match the current filter criteria '
                'for this page. Try filtering on "Any Status".')
        else:
            message = (
                'There are no branches registered for %s '
                'in Launchpad today. We recommend you visit '
                '<a href="http://www.bazaar-vcs.org">www.bazaar-vcs.org</a> '
                'for more information about how you can use the Bazaar '
                'revision control system to improve community participation '
                'in this project group.')
        return message % self.context.displayname


class SourcePackageBranchesView(BranchListingView):

    # XXX: "By most interesting" search doesn't work at all

    # XXX: No menu for this page, there should be. And the menu should just
    # have register a branch.

    # XXX: No link back to this page from branches, other than code tab

    # XXX: Show me at the bottom I can see previous/next series or: [dapper]
    # [edgy] feisty [gutsy] [hardy]

    # XXX: deleting a branch takes it back to the person branch listing

    # XXX: no message when there are no branches

    @cachedproperty
    def branch_count(self):
        """The number of total branches the user can see."""
        return getUtility(IBranchSet).getBranchesForContext(
            context=self.context, visible_by_user=self.user).count()
