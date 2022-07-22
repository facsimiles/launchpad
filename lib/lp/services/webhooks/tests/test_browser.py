# Copyright 2015-2021 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Unit tests for Webhook views."""

import re

import soupmatchers
import transaction
from testtools.matchers import MatchesAll, MatchesStructure, Not
from zope.component import getUtility

from lp.charms.interfaces.charmrecipe import (
    CHARM_RECIPE_ALLOW_CREATE,
    CHARM_RECIPE_WEBHOOKS_FEATURE_FLAG,
)
from lp.oci.interfaces.ocirecipe import (
    OCI_RECIPE_ALLOW_CREATE,
    OCI_RECIPE_WEBHOOKS_FEATURE_FLAG,
)
from lp.services.features.testing import FeatureFixture
from lp.services.webapp.interfaces import IPlacelessAuthUtility
from lp.services.webapp.publisher import canonical_url
from lp.soyuz.interfaces.livefs import (
    LIVEFS_FEATURE_FLAG,
    LIVEFS_WEBHOOKS_FEATURE_FLAG,
)
from lp.testing import TestCaseWithFactory, login_person, record_two_runs
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.matchers import HasQueryCount
from lp.testing.pages import extract_text
from lp.testing.views import create_view

breadcrumbs_tag = soupmatchers.Tag(
    "breadcrumbs", "ol", attrs={"class": "breadcrumbs"}
)
webhooks_page_crumb_tag = soupmatchers.Tag(
    "webhooks page breadcrumb", "li", text=re.compile("Webhooks")
)
webhooks_collection_crumb_tag = soupmatchers.Tag(
    "webhooks page breadcrumb",
    "a",
    text=re.compile("Webhooks"),
    attrs={"href": re.compile(r"/\+webhooks$")},
)
add_webhook_tag = soupmatchers.Tag(
    "add webhook",
    "a",
    text="Add webhook",
    attrs={"href": re.compile(r"/\+new-webhook$")},
)
webhook_listing_constants = soupmatchers.HTMLContains(
    soupmatchers.Within(breadcrumbs_tag, webhooks_page_crumb_tag),
    add_webhook_tag,
)

webhook_listing_tag = soupmatchers.Tag(
    "webhook listing", "table", attrs={"class": "listing"}
)
batch_nav_tag = soupmatchers.Tag(
    "batch nav links", "td", attrs={"class": "batch-navigation-links"}
)


class GitRepositoryTestHelpers:

    event_type = "git:push:0.1"
    expected_event_types = [
        ("git:push:0.1", "Git push"),
        ("merge-proposal:0.1", "Merge proposal"),
    ]

    def makeTarget(self):
        return self.factory.makeGitRepository()

    def getTraversalStack(self, obj):
        return [obj.target, obj]


class BranchTestHelpers:

    event_type = "bzr:push:0.1"
    expected_event_types = [
        ("bzr:push:0.1", "Bazaar push"),
        ("merge-proposal:0.1", "Merge proposal"),
    ]

    def makeTarget(self):
        return self.factory.makeBranch()

    def getTraversalStack(self, obj):
        return [obj.target, obj]


class SnapTestHelpers:

    event_type = "snap:build:0.1"
    expected_event_types = [
        ("snap:build:0.1", "Snap build"),
    ]

    def makeTarget(self):
        self.useFixture(
            FeatureFixture(
                {
                    "webhooks.new.enabled": "true",
                }
            )
        )
        owner = self.factory.makePerson()
        return self.factory.makeSnap(registrant=owner, owner=owner)

    def getTraversalStack(self, obj):
        return [obj]


class LiveFSTestHelpers:
    event_type = "livefs:build:0.1"
    expected_event_types = [
        ("livefs:build:0.1", "Live filesystem build"),
    ]

    def setUp(self):
        super().setUp()

    def makeTarget(self):
        self.useFixture(
            FeatureFixture(
                {
                    "webhooks.new.enabled": "true",
                    LIVEFS_FEATURE_FLAG: "on",
                    LIVEFS_WEBHOOKS_FEATURE_FLAG: "on",
                }
            )
        )
        owner = self.factory.makePerson()
        return self.factory.makeLiveFS(registrant=owner, owner=owner)

    def getTraversalStack(self, obj):
        return [obj]


class OCIRecipeTestHelpers:
    event_type = "oci-recipe:build:0.1"
    expected_event_types = [
        ("oci-recipe:build:0.1", "OCI recipe build"),
    ]

    def setUp(self):
        super().setUp()

    def makeTarget(self):
        self.useFixture(
            FeatureFixture(
                {
                    "webhooks.new.enabled": "true",
                    OCI_RECIPE_WEBHOOKS_FEATURE_FLAG: "on",
                    OCI_RECIPE_ALLOW_CREATE: "on",
                }
            )
        )
        owner = self.factory.makePerson()
        return self.factory.makeOCIRecipe(registrant=owner, owner=owner)

    def getTraversalStack(self, obj):
        return [obj]


class CharmRecipeTestHelpers:

    event_type = "charm-recipe:build:0.1"
    expected_event_types = [
        ("charm-recipe:build:0.1", "Charm recipe build"),
    ]

    def setUp(self):
        super().setUp()

    def makeTarget(self):
        self.useFixture(
            FeatureFixture(
                {
                    "webhooks.new.enabled": "true",
                    CHARM_RECIPE_ALLOW_CREATE: "on",
                    CHARM_RECIPE_WEBHOOKS_FEATURE_FLAG: "on",
                }
            )
        )
        owner = self.factory.makePerson()
        return self.factory.makeCharmRecipe(registrant=owner, owner=owner)

    def getTraversalStack(self, obj):
        return [obj]


class WebhookTargetViewTestHelpers:
    def setUp(self):
        super().setUp()
        self.useFixture(FeatureFixture({"webhooks.new.enabled": "true"}))
        self.target = self.makeTarget()
        self.owner = self.target.owner
        login_person(self.owner)

    def makeView(self, name, **kwargs):
        # XXX cjwatson 2020-02-06: We need to give the view a
        # LaunchpadPrincipal rather than just a person, since otherwise bits
        # of the navigation menu machinery try to use the scope_url
        # attribute on the principal and fail.  This should probably be done
        # in create_view instead, but that approach needs care to avoid
        # adding an extra query to tests that might be sensitive to that.
        principal = getUtility(IPlacelessAuthUtility).getPrincipal(
            self.owner.accountID
        )
        view = create_view(
            self.target,
            name,
            principal=principal,
            current_request=True,
            **kwargs,
        )
        # To test the breadcrumbs we need a correct traversal stack.
        view.request.traversed_objects = self.getTraversalStack(
            self.target
        ) + [view]
        # The navigation menu machinery needs this to find the view from the
        # request.
        view.request._last_obj_traversed = view
        view.initialize()
        return view


class TestWebhooksViewBase(WebhookTargetViewTestHelpers):

    layer = DatabaseFunctionalLayer

    def makeHooksAndMatchers(self, count):
        hooks = [
            self.factory.makeWebhook(
                target=self.target, delivery_url="http://example.com/%d" % i
            )
            for i in range(count)
        ]
        # There is a link to each webhook.
        link_matchers = [
            soupmatchers.Tag(
                "webhook link",
                "a",
                text=hook.delivery_url,
                attrs={
                    "href": canonical_url(hook, path_only_if_possible=True)
                },
            )
            for hook in hooks
        ]
        return link_matchers

    def test_navigation_from_context(self):
        # The context object's index page shows a "Manage webhooks" link.
        self.assertThat(
            self.makeView("+index")(),
            soupmatchers.HTMLContains(
                soupmatchers.Tag(
                    "manage webhooks link",
                    "a",
                    text="Manage webhooks",
                    attrs={
                        "href": canonical_url(
                            self.target, view_name="+webhooks"
                        ),
                    },
                )
            ),
        )

    def test_empty(self):
        # The table isn't shown if there are no webhooks yet.
        self.assertThat(
            self.makeView("+webhooks")(),
            MatchesAll(
                webhook_listing_constants,
                Not(soupmatchers.HTMLContains(webhook_listing_tag)),
            ),
        )

    def test_few_hooks(self):
        # The table is just a simple table if there is only one batch.
        link_matchers = self.makeHooksAndMatchers(3)
        self.assertThat(
            self.makeView("+webhooks")(),
            MatchesAll(
                webhook_listing_constants,
                soupmatchers.HTMLContains(webhook_listing_tag, *link_matchers),
                Not(soupmatchers.HTMLContains(batch_nav_tag)),
            ),
        )

    def test_many_hooks(self):
        # Batch navigation controls are shown once there are enough.
        link_matchers = self.makeHooksAndMatchers(10)
        self.assertThat(
            self.makeView("+webhooks")(),
            MatchesAll(
                webhook_listing_constants,
                soupmatchers.HTMLContains(
                    webhook_listing_tag, batch_nav_tag, *link_matchers[:5]
                ),
                Not(soupmatchers.HTMLContains(*link_matchers[5:])),
            ),
        )

    def test_query_count(self):
        # The query count is constant with number of webhooks.
        def create_webhook():
            self.factory.makeWebhook(target=self.target)

        # Run once to get things stable, then check that adding more
        # webhooks doesn't inflate the count.
        self.makeView("+webhooks")()
        recorder1, recorder2 = record_two_runs(
            lambda: self.makeView("+webhooks")(), create_webhook, 10
        )
        self.assertThat(recorder2, HasQueryCount.byEquality(recorder1))


class TestWebhooksViewGitRepository(
    TestWebhooksViewBase, GitRepositoryTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhooksViewBranch(
    TestWebhooksViewBase, BranchTestHelpers, TestCaseWithFactory
):
    pass


class TestWebhooksViewSnap(
    TestWebhooksViewBase, SnapTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhooksViewLiveFS(
    TestWebhooksViewBase, LiveFSTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhooksViewOCIRecipe(
    TestWebhooksViewBase, OCIRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhooksViewCharmRecipe(
    TestWebhooksViewBase, CharmRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewBase(WebhookTargetViewTestHelpers):

    layer = DatabaseFunctionalLayer

    def test_rendering(self):
        self.assertThat(
            self.makeView("+new-webhook")(),
            soupmatchers.HTMLContains(
                soupmatchers.Within(
                    breadcrumbs_tag, webhooks_collection_crumb_tag
                ),
                soupmatchers.Within(
                    breadcrumbs_tag,
                    soupmatchers.Tag(
                        "add webhook breadcrumb",
                        "li",
                        text=re.compile("Add webhook"),
                    ),
                ),
                soupmatchers.Tag(
                    "cancel link",
                    "a",
                    text="Cancel",
                    attrs={"href": re.compile(r"/\+webhooks$")},
                ),
            ),
        )

    def test_creates(self):
        view = self.makeView(
            "+new-webhook",
            method="POST",
            form={
                "field.delivery_url": "http://example.com/test",
                "field.active": "on",
                "field.event_types-empty-marker": "1",
                "field.event_types": self.event_type,
                "field.secret": "secret code",
                "field.actions.new": "Add webhook",
            },
        )
        self.assertEqual([], view.errors)
        hook = self.target.webhooks.one()
        self.assertThat(
            hook,
            MatchesStructure.byEquality(
                target=self.target,
                registrant=self.owner,
                delivery_url="http://example.com/test",
                active=True,
                event_types=[self.event_type],
                secret="secret code",
            ),
        )

    def test_rejects_bad_scheme(self):
        transaction.commit()
        view = self.makeView(
            "+new-webhook",
            method="POST",
            form={
                "field.delivery_url": "ftp://example.com/test",
                "field.active": "on",
                "field.event_types-empty-marker": "1",
                "field.actions.new": "Add webhook",
            },
        )
        self.assertEqual(
            ["delivery_url"], [error.field_name for error in view.errors]
        )
        self.assertIs(None, self.target.webhooks.one())

    def test_no_secret(self):
        # If the secret field is left empty, the secret is set to None
        # rather than to the empty string.
        view = self.makeView(
            "+new-webhook",
            method="POST",
            form={
                "field.delivery_url": "http://example.com/test",
                "field.active": "on",
                "field.event_types-empty-marker": "1",
                "field.event_types": self.event_type,
                "field.secret": "",
                "field.actions.new": "Add webhook",
            },
        )
        self.assertEqual([], view.errors)
        hook = self.target.webhooks.one()
        self.assertIsNone(hook.secret)

    def test_event_types(self):
        # Only event types that are valid for the target are offered.
        browser = self.getUserBrowser(
            canonical_url(self.target, view_name="+new-webhook"),
            user=self.owner,
        )
        event_types = browser.getControl(name="field.event_types")
        display_options = [
            extract_text(option) for option in event_types.displayOptions
        ]
        self.assertContentEqual(
            self.expected_event_types,
            zip(event_types.options, display_options),
        )


class TestWebhookAddViewGitRepository(
    TestWebhookAddViewBase, GitRepositoryTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewBranch(
    TestWebhookAddViewBase, BranchTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewSnap(
    TestWebhookAddViewBase, SnapTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewLiveFS(
    TestWebhookAddViewBase, LiveFSTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewOCIRecipe(
    TestWebhookAddViewBase, OCIRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookAddViewCharmRecipe(
    TestWebhookAddViewBase, CharmRecipeTestHelpers, TestCaseWithFactory
):

    pass


class WebhookViewTestHelpers:
    def setUp(self):
        super().setUp()
        self.useFixture(FeatureFixture({"webhooks.new.enabled": "true"}))
        self.target = self.makeTarget()
        self.owner = self.target.owner
        self.webhook = self.factory.makeWebhook(
            target=self.target, delivery_url="http://example.com/original"
        )
        login_person(self.owner)

    def makeView(self, name, **kwargs):
        view = create_view(self.webhook, name, principal=self.owner, **kwargs)
        # To test the breadcrumbs we need a correct traversal stack.
        view.request.traversed_objects = self.getTraversalStack(
            self.target
        ) + [self.webhook, view]
        view.initialize()
        return view


class TestWebhookViewBase(WebhookViewTestHelpers):

    layer = DatabaseFunctionalLayer

    def test_rendering(self):
        self.assertThat(
            self.makeView("+index")(),
            soupmatchers.HTMLContains(
                soupmatchers.Within(
                    breadcrumbs_tag, webhooks_collection_crumb_tag
                ),
                soupmatchers.Within(
                    breadcrumbs_tag,
                    soupmatchers.Tag(
                        "webhook breadcrumb",
                        "li",
                        text=re.compile(re.escape(self.webhook.delivery_url)),
                    ),
                ),
                soupmatchers.Tag(
                    "delete link",
                    "a",
                    text="Delete webhook",
                    attrs={"href": re.compile(r"/\+delete$")},
                ),
            ),
        )

    def test_saves(self):
        view = self.makeView(
            "+index",
            method="POST",
            form={
                "field.delivery_url": "http://example.com/edited",
                "field.active": "off",
                "field.event_types-empty-marker": "1",
                "field.actions.save": "Save webhook",
            },
        )
        self.assertEqual([], view.errors)
        self.assertThat(
            self.webhook,
            MatchesStructure.byEquality(
                delivery_url="http://example.com/edited",
                active=False,
                event_types=[],
            ),
        )

    def test_rejects_bad_scheme(self):
        transaction.commit()
        view = self.makeView(
            "+index",
            method="POST",
            form={
                "field.delivery_url": "ftp://example.com/edited",
                "field.active": "off",
                "field.event_types-empty-marker": "1",
                "field.actions.save": "Save webhook",
            },
        )
        self.assertEqual(
            ["delivery_url"], [error.field_name for error in view.errors]
        )
        self.assertThat(
            self.webhook,
            MatchesStructure.byEquality(
                delivery_url="http://example.com/original",
                active=True,
                event_types=[],
            ),
        )

    def test_event_types(self):
        # Only event types that are valid for the target are offered.
        browser = self.getUserBrowser(
            canonical_url(self.webhook, view_name="+index"), user=self.owner
        )
        event_types = browser.getControl(name="field.event_types")
        display_options = [
            extract_text(option) for option in event_types.displayOptions
        ]
        self.assertContentEqual(
            self.expected_event_types,
            zip(event_types.options, display_options),
        )


class TestWebhookViewGitRepository(
    TestWebhookViewBase, GitRepositoryTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookViewBranch(
    TestWebhookViewBase, BranchTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookViewSnap(
    TestWebhookViewBase, SnapTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookViewLiveFS(
    TestWebhookViewBase, LiveFSTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookViewOCIRecipe(
    TestWebhookViewBase, OCIRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookViewCharmRecipe(
    TestWebhookViewBase, CharmRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewBase(WebhookViewTestHelpers):

    layer = DatabaseFunctionalLayer

    def test_rendering(self):
        self.assertThat(
            self.makeView("+delete")(),
            soupmatchers.HTMLContains(
                soupmatchers.Within(
                    breadcrumbs_tag, webhooks_collection_crumb_tag
                ),
                soupmatchers.Within(
                    breadcrumbs_tag,
                    soupmatchers.Tag(
                        "webhook breadcrumb",
                        "a",
                        text=re.compile(re.escape(self.webhook.delivery_url)),
                        attrs={"href": canonical_url(self.webhook)},
                    ),
                ),
                soupmatchers.Within(
                    breadcrumbs_tag,
                    soupmatchers.Tag(
                        "delete breadcrumb",
                        "li",
                        text=re.compile("Delete webhook"),
                    ),
                ),
                soupmatchers.Tag(
                    "cancel link",
                    "a",
                    text="Cancel",
                    attrs={"href": canonical_url(self.webhook)},
                ),
            ),
        )

    def test_deletes(self):
        view = self.makeView(
            "+delete",
            method="POST",
            form={"field.actions.delete": "Delete webhook"},
        )
        self.assertEqual([], view.errors)
        self.assertIs(None, self.target.webhooks.one())


class TestWebhookDeleteViewGitRepository(
    TestWebhookDeleteViewBase, GitRepositoryTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewBranch(
    TestWebhookDeleteViewBase, BranchTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewSnap(
    TestWebhookDeleteViewBase, SnapTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewLiveFS(
    TestWebhookDeleteViewBase, LiveFSTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewOCIRecipe(
    TestWebhookDeleteViewBase, OCIRecipeTestHelpers, TestCaseWithFactory
):

    pass


class TestWebhookDeleteViewCharmRecipe(
    TestWebhookDeleteViewBase, CharmRecipeTestHelpers, TestCaseWithFactory
):

    pass
