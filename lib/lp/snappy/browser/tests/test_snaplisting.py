# Copyright 2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test snap package listings."""

__metaclass__ = type

import soupmatchers
from testtools.matchers import (
    Equals,
    Not,
    )

from lp.services.database.constants import (
    ONE_DAY_AGO,
    UTC_NOW,
    )
from lp.services.features.testing import FeatureFixture
from lp.services.webapp import canonical_url
from lp.snappy.interfaces.snap import SNAP_FEATURE_FLAG
from lp.testing import (
    ANONYMOUS,
    BrowserTestCase,
    login,
    person_logged_in,
    record_two_runs,
    )
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.matchers import HasQueryCount


class TestSnapListing(BrowserTestCase):

    layer = DatabaseFunctionalLayer

    def makeSnap(self, **kwargs):
        """Create a snap package, enabling the feature flag.

        We do things this way rather than by calling self.useFixture because
        opening a URL in a test browser loses the thread-local feature flag.
        """
        with FeatureFixture({SNAP_FEATURE_FLAG: u"on"}):
            return self.factory.makeSnap(**kwargs)

    def assertSnapsLink(self, context, link_text, link_has_context=False,
                        **kwargs):
        if link_has_context:
            expected_href = canonical_url(context, view_name="+snaps")
        else:
            expected_href = "+snaps"
        matcher = soupmatchers.HTMLContains(
            soupmatchers.Tag(
                "View snap packages link", "a", text=link_text,
                attrs={"href": expected_href}))
        self.assertThat(self.getViewBrowser(context).contents, Not(matcher))
        login(ANONYMOUS)
        self.makeSnap(**kwargs)
        self.assertThat(self.getViewBrowser(context).contents, matcher)

    def test_branch_links_to_snaps(self):
        branch = self.factory.makeAnyBranch()
        self.assertSnapsLink(branch, "1 snap package", branch=branch)

    def test_git_repository_links_to_snaps(self):
        repository = self.factory.makeGitRepository()
        [ref] = self.factory.makeGitRefs(repository=repository)
        self.assertSnapsLink(repository, "1 snap package", git_ref=ref)

    def test_git_ref_links_to_snaps(self):
        [ref] = self.factory.makeGitRefs()
        self.assertSnapsLink(ref, "1 snap package", git_ref=ref)

    def test_person_links_to_snaps(self):
        person = self.factory.makePerson()
        self.assertSnapsLink(
            person, "View snap packages", link_has_context=True,
            registrant=person, owner=person)

    def test_project_links_to_snaps(self):
        project = self.factory.makeProduct()
        [ref] = self.factory.makeGitRefs(target=project)
        self.assertSnapsLink(
            project, "View snap packages", link_has_context=True, git_ref=ref)

    def test_branch_snap_listing(self):
        # We can see snap packages for a Bazaar branch.  We need to create
        # two, since if there's only one then +snaps will redirect to that
        # package.
        branch = self.factory.makeAnyBranch()
        for _ in range(2):
            self.makeSnap(branch=branch)
        text = self.getMainText(branch, "+snaps")
        self.assertTextMatchesExpressionIgnoreWhitespace("""
            Snap packages for lp:.*
            Name            Owner           Registered
            snap-name.*     Team Name.*     .*
            snap-name.*     Team Name.*     .*""", text)

    def test_git_repository_snap_listing(self):
        # We can see snap packages for a Git repository.  We need to create
        # two, since if there's only one then +snaps will redirect to that
        # package.
        repository = self.factory.makeGitRepository()
        ref1, ref2 = self.factory.makeGitRefs(
            repository=repository,
            paths=[u"refs/heads/branch-1", u"refs/heads/branch-2"])
        for ref in ref1, ref2:
            self.makeSnap(git_ref=ref)
        text = self.getMainText(repository, "+snaps")
        self.assertTextMatchesExpressionIgnoreWhitespace("""
            Snap packages for lp:~.*
            Name            Owner           Registered
            snap-name.*     Team Name.*     .*
            snap-name.*     Team Name.*     .*""", text)

    def test_git_ref_snap_listing(self):
        # We can see snap packages for a Git reference.  We need to create
        # two, since if there's only one then +snaps will redirect to that
        # package.
        [ref] = self.factory.makeGitRefs()
        for _ in range(2):
            self.makeSnap(git_ref=ref)
        text = self.getMainText(ref, "+snaps")
        self.assertTextMatchesExpressionIgnoreWhitespace("""
            Snap packages for ~.*:.*
            Name            Owner           Registered
            snap-name.*     Team Name.*     .*
            snap-name.*     Team Name.*     .*""", text)

    def test_person_snap_listing(self):
        # We can see snap packages for a person.  We need to create two,
        # since if there's only one then +snaps will redirect to that
        # package.
        owner = self.factory.makePerson(displayname="Snap Owner")
        self.makeSnap(
            registrant=owner, owner=owner, branch=self.factory.makeAnyBranch(),
            date_created=ONE_DAY_AGO)
        [ref] = self.factory.makeGitRefs()
        self.makeSnap(
            registrant=owner, owner=owner, git_ref=ref, date_created=UTC_NOW)
        text = self.getMainText(owner, "+snaps")
        self.assertTextMatchesExpressionIgnoreWhitespace("""
            Snap packages for Snap Owner
            Name            Source          Registered
            snap-name.*     ~.*:.*          .*
            snap-name.*     lp:.*           .*""", text)

    def test_project_snap_listing(self):
        # We can see snap packages for a project.  We need to create two,
        # since if there's only one then +snaps will redirect to that
        # package.
        project = self.factory.makeProduct(displayname="Snappable")
        self.makeSnap(
            branch=self.factory.makeProductBranch(product=project),
            date_created=ONE_DAY_AGO)
        [ref] = self.factory.makeGitRefs(target=project)
        self.makeSnap(git_ref=ref, date_created=UTC_NOW)
        text = self.getMainText(project, "+snaps")
        self.assertTextMatchesExpressionIgnoreWhitespace("""
            Snap packages for Snappable
            Name            Owner           Source          Registered
            snap-name.*     Team Name.*     ~.*:.*          .*
            snap-name.*     Team Name.*     lp:.*           .*""", text)

    def assertSnapsQueryCount(self, context, item_creator):
        recorder1, recorder2 = record_two_runs(
            lambda: self.getMainText(context, "+snaps"), item_creator, 5)
        self.assertThat(recorder2, HasQueryCount(Equals(recorder1.count)))

    def test_branch_query_count(self):
        # The number of queries required to render the list of all snap
        # packages for a Bazaar branch is constant in the number of owners
        # and snap packages.
        person = self.factory.makePerson()
        branch = self.factory.makeAnyBranch(owner=person)

        def create_snap():
            with person_logged_in(person):
                self.makeSnap(branch=branch)

        self.assertSnapsQueryCount(branch, create_snap)

    def test_git_repository_query_count(self):
        # The number of queries required to render the list of all snap
        # packages for a Git repository is constant in the number of owners
        # and snap packages.
        person = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=person)

        def create_snap():
            with person_logged_in(person):
                [ref] = self.factory.makeGitRefs(repository=repository)
                self.makeSnap(git_ref=ref)

        self.assertSnapsQueryCount(repository, create_snap)

    def test_git_ref_query_count(self):
        # The number of queries required to render the list of all snap
        # packages for a Git reference is constant in the number of owners
        # and snap packages.
        person = self.factory.makePerson()
        [ref] = self.factory.makeGitRefs(owner=person)

        def create_snap():
            with person_logged_in(person):
                self.makeSnap(git_ref=ref)

        self.assertSnapsQueryCount(ref, create_snap)

    def test_person_query_count(self):
        # The number of queries required to render the list of all snap
        # packages for a person is constant in the number of projects,
        # sources, and snap packages.
        person = self.factory.makePerson()
        i = 0

        def create_snap():
            with person_logged_in(person):
                project = self.factory.makeProduct()
                if (i % 2) == 0:
                    branch = self.factory.makeProductBranch(
                        owner=person, product=project)
                    self.makeSnap(branch=branch)
                else:
                    [ref] = self.factory.makeGitRefs(
                        owner=person, target=project)
                    self.makeSnap(git_ref=ref)

        self.assertSnapsQueryCount(person, create_snap)

    def test_project_query_count(self):
        # The number of queries required to render the list of all snap
        # packages for a person is constant in the number of owners,
        # sources, and snap packages.
        person = self.factory.makePerson()
        project = self.factory.makeProduct(owner=person)
        i = 0

        def create_snap():
            with person_logged_in(person):
                if (i % 2) == 0:
                    branch = self.factory.makeProductBranch(product=project)
                    self.makeSnap(branch=branch)
                else:
                    [ref] = self.factory.makeGitRefs(target=project)
                    self.makeSnap(git_ref=ref)

        self.assertSnapsQueryCount(project, create_snap)
