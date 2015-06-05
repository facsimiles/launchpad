# Copyright 2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for Git repositories."""

__metaclass__ = type

from datetime import datetime
import email
from functools import partial
import hashlib
import json

from bzrlib import urlutils
from lazr.lifecycle.event import ObjectModifiedEvent
from lazr.lifecycle.snapshot import Snapshot
from sqlobject import SQLObjectNotFound
from storm.store import Store
import transaction
import pytz
from testtools.matchers import (
    EndsWith,
    MatchesSetwise,
    MatchesStructure,
    )
from zope.component import getUtility
from zope.event import notify
from zope.interface import providedBy
from zope.security.interfaces import Unauthorized
from zope.security.proxy import removeSecurityProxy

from lp import _
from lp.app.enums import (
    InformationType,
    PRIVATE_INFORMATION_TYPES,
    PUBLIC_INFORMATION_TYPES,
    )
from lp.app.interfaces.launchpad import ILaunchpadCelebrities
from lp.code.enums import (
    BranchSubscriptionDiffSize,
    BranchSubscriptionNotificationLevel,
    CodeReviewNotificationLevel,
    GitObjectType,
    )
from lp.code.errors import (
    CannotDeleteGitRepository,
    GitRepositoryCreatorNotMemberOfOwnerTeam,
    GitRepositoryCreatorNotOwner,
    GitRepositoryExists,
    GitTargetError,
    )
from lp.code.interfaces.defaultgit import ICanHasDefaultGitRepository
from lp.code.interfaces.gitjob import IGitRefScanJobSource
from lp.code.interfaces.gitlookup import IGitLookup
from lp.code.interfaces.gitnamespace import (
    IGitNamespacePolicy,
    IGitNamespaceSet,
    )
from lp.code.interfaces.gitrepository import (
    IGitRepository,
    IGitRepositorySet,
    )
from lp.code.interfaces.revision import IRevisionSet
from lp.code.model.branchmergeproposal import BranchMergeProposal
from lp.code.model.codereviewcomment import CodeReviewComment
from lp.code.model.gitjob import (
    GitJob,
    GitJobType,
    ReclaimGitRepositorySpaceJob,
    )
from lp.code.model.gitrepository import (
    ClearPrerequisiteRepository,
    DeletionCallable,
    DeletionOperation,
    GitRepository,
    )
from lp.code.xmlrpc.git import GitAPI
from lp.registry.enums import (
    BranchSharingPolicy,
    PersonVisibility,
    TeamMembershipPolicy,
    )
from lp.registry.interfaces.accesspolicy import (
    IAccessArtifactSource,
    IAccessPolicyArtifactSource,
    IAccessPolicySource,
    )
from lp.registry.interfaces.persondistributionsourcepackage import (
    IPersonDistributionSourcePackageFactory,
    )
from lp.registry.interfaces.personproduct import IPersonProductFactory
from lp.registry.tests.test_accesspolicy import get_policies_for_artifact
from lp.services.config import config
from lp.services.database.constants import UTC_NOW
from lp.services.job.runner import JobRunner
from lp.services.mail import stub
from lp.services.webapp.authorization import check_permission
from lp.services.webapp.interfaces import OAuthPermission
from lp.testing import (
    admin_logged_in,
    ANONYMOUS,
    api_url,
    celebrity_logged_in,
    login_person,
    person_logged_in,
    TestCaseWithFactory,
    verifyObject,
    )
from lp.testing.dbuser import dbuser
from lp.testing.fakemethod import FakeMethod
from lp.testing.layers import (
    DatabaseFunctionalLayer,
    LaunchpadFunctionalLayer,
    LaunchpadZopelessLayer,
    )
from lp.testing.pages import webservice_for_person


class TestGitRepository(TestCaseWithFactory):
    """Test basic properties about Launchpad database Git repositories."""

    layer = DatabaseFunctionalLayer

    def test_implements_IGitRepository(self):
        repository = self.factory.makeGitRepository()
        verifyObject(IGitRepository, repository)

    def test_unique_name_project(self):
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        self.assertEqual(
            "~%s/%s/+git/%s" % (
                repository.owner.name, project.name, repository.name),
            repository.unique_name)

    def test_unique_name_package(self):
        dsp = self.factory.makeDistributionSourcePackage()
        repository = self.factory.makeGitRepository(target=dsp)
        self.assertEqual(
            "~%s/%s/+source/%s/+git/%s" % (
                repository.owner.name, dsp.distribution.name,
                dsp.sourcepackagename.name, repository.name),
            repository.unique_name)

    def test_unique_name_personal(self):
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner, target=owner)
        self.assertEqual(
            "~%s/+git/%s" % (owner.name, repository.name),
            repository.unique_name)

    def test_target_project(self):
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        self.assertEqual(project, repository.target)

    def test_target_package(self):
        dsp = self.factory.makeDistributionSourcePackage()
        repository = self.factory.makeGitRepository(target=dsp)
        self.assertEqual(dsp, repository.target)

    def test_target_personal(self):
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner, target=owner)
        self.assertEqual(owner, repository.target)


class TestGitIdentityMixin(TestCaseWithFactory):
    """Test the defaults and identities provided by GitIdentityMixin."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestGitIdentityMixin, self).setUp()
        self.repository_set = getUtility(IGitRepositorySet)

    def assertGitIdentity(self, repository, identity_path):
        """Assert that the Git identity of 'repository' is 'identity_path'.

        Actually, it'll be lp:<identity_path>.
        """
        self.assertEqual(
            identity_path, repository.shortened_path, "shortened path")
        self.assertEqual(
            "lp:%s" % identity_path, repository.git_identity, "git identity")

    def test_git_identity_default(self):
        # By default, the Git identity is the repository's unique name.
        repository = self.factory.makeGitRepository()
        self.assertGitIdentity(repository, repository.unique_name)

    def test_git_identity_default_for_project(self):
        # If a repository is the default for a project, then its Git
        # identity is the project name.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(
            owner=project.owner, target=project)
        with person_logged_in(project.owner):
            self.repository_set.setDefaultRepository(project, repository)
        self.assertGitIdentity(repository, project.name)

    def test_git_identity_private_default_for_project(self):
        # Private repositories also have a short lp: URL.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(
            target=project, information_type=InformationType.USERDATA)
        with admin_logged_in():
            self.repository_set.setDefaultRepository(project, repository)
            self.assertGitIdentity(repository, project.name)

    def test_git_identity_default_for_package(self):
        # If a repository is the default for a package, then its Git
        # identity uses the path to that package.
        dsp = self.factory.makeDistributionSourcePackage()
        repository = self.factory.makeGitRepository(target=dsp)
        with admin_logged_in():
            self.repository_set.setDefaultRepository(dsp, repository)
        self.assertGitIdentity(
            repository,
            "%s/+source/%s" % (
                dsp.distribution.name, dsp.sourcepackagename.name))

    def test_git_identity_owner_default_for_project(self):
        # If a repository is a person's default for a project, then its Git
        # identity is a combination of the person and project names.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        with person_logged_in(repository.owner) as user:
            self.repository_set.setDefaultRepositoryForOwner(
                repository.owner, project, repository, user)
        self.assertGitIdentity(
            repository, "~%s/%s" % (repository.owner.name, project.name))

    def test_git_identity_owner_default_for_package(self):
        # If a repository is a person's default for a package, then its Git
        # identity is a combination of the person name and the package path.
        dsp = self.factory.makeDistributionSourcePackage()
        repository = self.factory.makeGitRepository(target=dsp)
        with person_logged_in(repository.owner) as user:
            self.repository_set.setDefaultRepositoryForOwner(
                repository.owner, dsp, repository, user)
        self.assertGitIdentity(
            repository,
            "~%s/%s/+source/%s" % (
                repository.owner.name, dsp.distribution.name,
                dsp.sourcepackagename.name))

    def test_identities_no_defaults(self):
        # If there are no defaults, the only repository identity is the
        # unique name.
        repository = self.factory.makeGitRepository()
        self.assertEqual(
            [(repository.unique_name, repository)],
            repository.getRepositoryIdentities())

    def test_default_for_project(self):
        # If a repository is the default for a project, then that is the
        # preferred identity.  Target defaults are preferred over
        # owner-target defaults.
        eric = self.factory.makePerson(name="eric")
        fooix = self.factory.makeProduct(name="fooix", owner=eric)
        repository = self.factory.makeGitRepository(
            owner=eric, target=fooix, name=u"fooix-repo")
        with person_logged_in(fooix.owner) as user:
            self.repository_set.setDefaultRepositoryForOwner(
                repository.owner, fooix, repository, user)
            self.repository_set.setDefaultRepository(fooix, repository)
        eric_fooix = getUtility(IPersonProductFactory).create(eric, fooix)
        self.assertEqual(
            [ICanHasDefaultGitRepository(target)
             for target in (fooix, eric_fooix)],
            repository.getRepositoryDefaults())
        self.assertEqual(
            [("fooix", fooix), ("~eric/fooix", eric_fooix),
             ("~eric/fooix/+git/fooix-repo", repository)],
            repository.getRepositoryIdentities())

    def test_default_for_package(self):
        # If a repository is the default for a package, then that is the
        # preferred identity.  Target defaults are preferred over
        # owner-target defaults.
        mint = self.factory.makeDistribution(name="mint")
        eric = self.factory.makePerson(name="eric")
        mint_choc = self.factory.makeDistributionSourcePackage(
            distribution=mint, sourcepackagename="choc")
        repository = self.factory.makeGitRepository(
            owner=eric, target=mint_choc, name=u"choc-repo")
        dsp = repository.target
        with admin_logged_in():
            self.repository_set.setDefaultRepositoryForOwner(
                repository.owner, dsp, repository, repository.owner)
            self.repository_set.setDefaultRepository(dsp, repository)
        eric_dsp = getUtility(IPersonDistributionSourcePackageFactory).create(
            eric, dsp)
        self.assertEqual(
            [ICanHasDefaultGitRepository(target)
             for target in (dsp, eric_dsp)],
            repository.getRepositoryDefaults())
        self.assertEqual(
            [("mint/+source/choc", dsp),
             ("~eric/mint/+source/choc", eric_dsp),
             ("~eric/mint/+source/choc/+git/choc-repo", repository)],
            repository.getRepositoryIdentities())


class TestGitRepositoryDeletion(TestCaseWithFactory):
    """Test the different cases that make a repository deletable or not."""

    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestGitRepositoryDeletion, self).setUp()
        self.user = self.factory.makePerson()
        self.project = self.factory.makeProduct(owner=self.user)
        self.repository = self.factory.makeGitRepository(
            name=u"to-delete", owner=self.user, target=self.project)
        [self.ref] = self.factory.makeGitRefs(repository=self.repository)
        # The owner of the repository is subscribed to the repository when
        # it is created.  The tests here assume no initial connections, so
        # unsubscribe the repository owner here.
        self.repository.unsubscribe(
            self.repository.owner, self.repository.owner)
        # Make sure that the tests all flush the database changes.
        self.addCleanup(Store.of(self.repository).flush)
        login_person(self.user)

    def test_deletable(self):
        # A newly created repository can be deleted without any problems.
        self.assertTrue(
            self.repository.canBeDeleted(),
            "A newly created repository should be able to be deleted.")
        repository_id = self.repository.id
        self.repository.destroySelf()
        self.assertIsNone(
            getUtility(IGitLookup).get(repository_id),
            "The repository has not been deleted.")

    def test_subscription_does_not_disable_deletion(self):
        # A repository that has a subscription can be deleted.
        self.repository.subscribe(
            self.user, BranchSubscriptionNotificationLevel.NOEMAIL, None,
            CodeReviewNotificationLevel.NOEMAIL, self.user)
        self.assertTrue(self.repository.canBeDeleted())
        repository_id = self.repository.id
        self.repository.destroySelf()
        self.assertIsNone(
            getUtility(IGitLookup).get(repository_id),
            "The repository has not been deleted.")

    def test_private_subscription_does_not_disable_deletion(self):
        # A private repository that has a subscription can be deleted.
        self.repository.transitionToInformationType(
            InformationType.USERDATA, self.repository.owner,
            verify_policy=False)
        self.repository.subscribe(
            self.user, BranchSubscriptionNotificationLevel.NOEMAIL, None,
            CodeReviewNotificationLevel.NOEMAIL, self.user)
        self.assertTrue(self.repository.canBeDeleted())
        repository_id = self.repository.id
        self.repository.destroySelf()
        self.assertIsNone(
            getUtility(IGitLookup).get(repository_id),
            "The repository has not been deleted.")

    def test_landing_target_disables_deletion(self):
        # A repository with a landing target cannot be deleted.
        [merge_target] = self.factory.makeGitRefs(
            name=u"landing-target", owner=self.user, target=self.project)
        self.ref.addLandingTarget(self.user, merge_target)
        self.assertFalse(
            self.repository.canBeDeleted(),
            "A repository with a landing target is not deletable.")
        self.assertRaises(
            CannotDeleteGitRepository, self.repository.destroySelf)

    def test_landing_candidate_disables_deletion(self):
        # A repository with a landing candidate cannot be deleted.
        [merge_source] = self.factory.makeGitRefs(
            name=u"landing-candidate", owner=self.user, target=self.project)
        merge_source.addLandingTarget(self.user, self.ref)
        self.assertFalse(
            self.repository.canBeDeleted(),
             "A repository with a landing candidate is not deletable.")
        self.assertRaises(
            CannotDeleteGitRepository, self.repository.destroySelf)

    def test_prerequisite_repository_disables_deletion(self):
        # A repository that is a prerequisite repository cannot be deleted.
        [merge_source] = self.factory.makeGitRefs(
            name=u"landing-candidate", owner=self.user, target=self.project)
        [merge_target] = self.factory.makeGitRefs(
            name=u"landing-target", owner=self.user, target=self.project)
        merge_source.addLandingTarget(self.user, merge_target, self.ref)
        self.assertFalse(
            self.repository.canBeDeleted(),
            "A repository with a prerequisite target is not deletable.")
        self.assertRaises(
            CannotDeleteGitRepository, self.repository.destroySelf)

    def test_related_GitJobs_deleted(self):
        # A repository with an associated job will delete those jobs.
        repository = self.factory.makeGitRepository()
        GitAPI(None, None).notify(repository.getInternalPath())
        store = Store.of(repository)
        repository.destroySelf()
        # Need to commit the transaction to fire off the constraint checks.
        transaction.commit()
        jobs = store.find(GitJob, GitJob.job_type == GitJobType.REF_SCAN)
        self.assertEqual([], list(jobs))

    def test_creates_job_to_reclaim_space(self):
        # When a repository is deleted from the database, a job is created
        # to remove the repository from disk as well.
        repository = self.factory.makeGitRepository()
        repository_path = repository.getInternalPath()
        store = Store.of(repository)
        repository.destroySelf()
        jobs = store.find(
            GitJob,
            GitJob.job_type == GitJobType.RECLAIM_REPOSITORY_SPACE)
        self.assertEqual(
            [repository_path],
            [ReclaimGitRepositorySpaceJob(job).repository_path
             for job in jobs])

    def test_destroySelf_with_inline_comments_draft(self):
        # Draft inline comments related to a deleted repository (source or
        # target MP repository) also get removed.
        merge_proposal = self.factory.makeBranchMergeProposalForGit(
            registrant=self.user, target_ref=self.ref)
        preview_diff = self.factory.makePreviewDiff(
            merge_proposal=merge_proposal)
        transaction.commit()
        merge_proposal.saveDraftInlineComment(
            previewdiff_id=preview_diff.id,
            person=self.user,
            comments={"1": "Should vanish."})
        self.repository.destroySelf(break_references=True)

    def test_destroySelf_with_inline_comments_published(self):
        # Published inline comments related to a deleted repository (source
        # or target MP repository) also get removed.
        merge_proposal = self.factory.makeBranchMergeProposalForGit(
            registrant=self.user, target_ref=self.ref)
        preview_diff = self.factory.makePreviewDiff(
            merge_proposal=merge_proposal)
        transaction.commit()
        merge_proposal.createComment(
            owner=self.user,
            subject="Delete me!",
            previewdiff_id=preview_diff.id,
            inline_comments={"1": "Must disappear."},
        )
        self.repository.destroySelf(break_references=True)


class TestGitRepositoryDeletionConsequences(TestCaseWithFactory):
    """Test determination and application of repository deletion
    consequences."""

    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestGitRepositoryDeletionConsequences, self).setUp(
            user="test@canonical.com")
        self.repository = self.factory.makeGitRepository()
        [self.ref] = self.factory.makeGitRefs(repository=self.repository)
        # The owner of the repository is subscribed to the repository when
        # it is created.  The tests here assume no initial connections, so
        # unsubscribe the repository owner here.
        self.repository.unsubscribe(
            self.repository.owner, self.repository.owner)

    def test_plain_repository(self):
        # A fresh repository has no deletion requirements.
        self.assertEqual({}, self.repository.getDeletionRequirements())

    def makeMergeProposals(self):
        # Produce a merge proposal for testing purposes.
        [merge_target] = self.factory.makeGitRefs(target=self.ref.target)
        [merge_prerequisite] = self.factory.makeGitRefs(target=self.ref.target)
        # Remove the implicit subscriptions.
        merge_target.repository.unsubscribe(
            merge_target.owner, merge_target.owner)
        merge_prerequisite.repository.unsubscribe(
            merge_prerequisite.owner, merge_prerequisite.owner)
        merge_proposal1 = self.ref.addLandingTarget(
            self.ref.owner, merge_target, merge_prerequisite)
        # Disable this merge proposal, to allow creating a new identical one.
        lp_admins = getUtility(ILaunchpadCelebrities).admin
        merge_proposal1.rejectBranch(lp_admins, "null:")
        merge_proposal2 = self.ref.addLandingTarget(
            self.ref.owner, merge_target, merge_prerequisite)
        return merge_proposal1, merge_proposal2

    def test_repository_with_merge_proposal(self):
        # Ensure that deletion requirements with a merge proposal are right.
        #
        # Each repository related to the merge proposal is tested to ensure
        # it produces a unique, correct result.
        merge_proposal1, merge_proposal2 = self.makeMergeProposals()
        self.assertEqual(
            {
                merge_proposal1:
                ("delete",
                 _("This repository is the source repository of this merge "
                   "proposal.")),
                merge_proposal2:
                ("delete",
                 _("This repository is the source repository of this merge "
                   "proposal.")),
                },
            self.repository.getDeletionRequirements())
        target = merge_proposal1.target_git_repository
        self.assertEqual(
            {
                merge_proposal1:
                ("delete",
                 _("This repository is the target repository of this merge "
                   "proposal.")),
                merge_proposal2:
                ("delete",
                 _("This repository is the target repository of this merge "
                   "proposal.")),
                },
            target.getDeletionRequirements())
        prerequisite = merge_proposal1.prerequisite_git_repository
        self.assertEqual(
            {
                merge_proposal1:
                ("alter",
                 _("This repository is the prerequisite repository of this "
                   "merge proposal.")),
                merge_proposal2:
                ("alter",
                 _("This repository is the prerequisite repository of this "
                   "merge proposal.")),
                },
            prerequisite.getDeletionRequirements())

    def test_delete_merge_proposal_source(self):
        # Merge proposal source repositories can be deleted with
        # break_references.
        merge_proposal1, merge_proposal2 = self.makeMergeProposals()
        merge_proposal1_id = merge_proposal1.id
        BranchMergeProposal.get(merge_proposal1_id)
        self.repository.destroySelf(break_references=True)
        self.assertRaises(
            SQLObjectNotFound, BranchMergeProposal.get, merge_proposal1_id)

    def test_delete_merge_proposal_target(self):
        # Merge proposal target repositories can be deleted with
        # break_references.
        merge_proposal1, merge_proposal2 = self.makeMergeProposals()
        merge_proposal1_id = merge_proposal1.id
        BranchMergeProposal.get(merge_proposal1_id)
        merge_proposal1.target_git_repository.destroySelf(
            break_references=True)
        self.assertRaises(SQLObjectNotFound,
            BranchMergeProposal.get, merge_proposal1_id)

    def test_delete_merge_proposal_prerequisite(self):
        # Merge proposal prerequisite repositories can be deleted with
        # break_references.
        merge_proposal1, merge_proposal2 = self.makeMergeProposals()
        merge_proposal1.prerequisite_git_repository.destroySelf(
            break_references=True)
        self.assertIsNone(merge_proposal1.prerequisite_git_repository)

    def test_delete_source_CodeReviewComment(self):
        # Deletion of source repositories that have CodeReviewComments works.
        comment = self.factory.makeCodeReviewComment(git=True)
        comment_id = comment.id
        repository = comment.branch_merge_proposal.source_git_repository
        repository.destroySelf(break_references=True)
        self.assertRaises(
            SQLObjectNotFound, CodeReviewComment.get, comment_id)

    def test_delete_target_CodeReviewComment(self):
        # Deletion of target repositories that have CodeReviewComments works.
        comment = self.factory.makeCodeReviewComment(git=True)
        comment_id = comment.id
        repository = comment.branch_merge_proposal.target_git_repository
        repository.destroySelf(break_references=True)
        self.assertRaises(
            SQLObjectNotFound, CodeReviewComment.get, comment_id)

    def test_sourceBranchWithCodeReviewVoteReference(self):
        # break_references handles CodeReviewVoteReference source repository.
        merge_proposal = self.factory.makeBranchMergeProposalForGit()
        merge_proposal.nominateReviewer(
            self.factory.makePerson(), self.factory.makePerson())
        merge_proposal.source_git_repository.destroySelf(break_references=True)

    def test_targetBranchWithCodeReviewVoteReference(self):
        # break_references handles CodeReviewVoteReference target repository.
        merge_proposal = self.factory.makeBranchMergeProposalForGit()
        merge_proposal.nominateReviewer(
            self.factory.makePerson(), self.factory.makePerson())
        merge_proposal.target_git_repository.destroySelf(break_references=True)

    def test_ClearPrerequisiteRepository(self):
        # ClearPrerequisiteRepository.__call__ must clear the prerequisite
        # repository.
        merge_proposal = removeSecurityProxy(self.makeMergeProposals()[0])
        with person_logged_in(
                merge_proposal.prerequisite_git_repository.owner):
            ClearPrerequisiteRepository(merge_proposal)()
        self.assertIsNone(merge_proposal.prerequisite_git_repository)

    def test_DeletionOperation(self):
        # DeletionOperation.__call__ is not implemented.
        self.assertRaises(NotImplementedError, DeletionOperation("a", "b"))

    def test_DeletionCallable(self):
        # DeletionCallable must invoke the callable.
        merge_proposal = self.factory.makeBranchMergeProposalForGit()
        merge_proposal_id = merge_proposal.id
        DeletionCallable(
            merge_proposal, "blah", merge_proposal.deleteProposal)()
        self.assertRaises(
            SQLObjectNotFound, BranchMergeProposal.get, merge_proposal_id)


class TestGitRepositoryModifications(TestCaseWithFactory):
    """Tests for Git repository modification notifications."""

    layer = DatabaseFunctionalLayer

    def test_date_last_modified_initial_value(self):
        # The initial value of date_last_modified is date_created.
        repository = self.factory.makeGitRepository()
        self.assertEqual(
            repository.date_created, repository.date_last_modified)

    def test_modifiedevent_sets_date_last_modified(self):
        # When a GitRepository receives an object modified event, the last
        # modified date is set to UTC_NOW.
        repository = self.factory.makeGitRepository(
            date_created=datetime(2015, 02, 04, 17, 42, 0, tzinfo=pytz.UTC))
        notify(ObjectModifiedEvent(
            removeSecurityProxy(repository), repository,
            [IGitRepository["name"]], user=repository.owner))
        self.assertSqlAttributeEqualsDate(
            repository, "date_last_modified", UTC_NOW)

    def test_create_ref_sets_date_last_modified(self):
        repository = self.factory.makeGitRepository(
            date_created=datetime(2015, 06, 01, tzinfo=pytz.UTC))
        [ref] = self.factory.makeGitRefs(repository=repository)
        new_refs_info = {
            ref.path: {
                u"sha1": u"0000000000000000000000000000000000000000",
                u"type": ref.object_type,
                },
            }
        repository.createOrUpdateRefs(new_refs_info)
        self.assertSqlAttributeEqualsDate(
            repository, "date_last_modified", UTC_NOW)

    def test_update_ref_sets_date_last_modified(self):
        repository = self.factory.makeGitRepository(
            date_created=datetime(2015, 06, 01, tzinfo=pytz.UTC))
        [ref] = self.factory.makeGitRefs(repository=repository)
        new_refs_info = {
            u"refs/heads/new": {
                u"sha1": ref.commit_sha1,
                u"type": ref.object_type,
                },
            }
        repository.createOrUpdateRefs(new_refs_info)
        self.assertSqlAttributeEqualsDate(
            repository, "date_last_modified", UTC_NOW)

    def test_remove_ref_sets_date_last_modified(self):
        repository = self.factory.makeGitRepository(
            date_created=datetime(2015, 06, 01, tzinfo=pytz.UTC))
        [ref] = self.factory.makeGitRefs(repository=repository)
        repository.removeRefs(set([ref.path]))
        self.assertSqlAttributeEqualsDate(
            repository, "date_last_modified", UTC_NOW)

    def test_sends_notifications(self):
        # Attribute modifications send mail to subscribers.
        self.assertEqual(0, len(stub.test_emails))
        repository = self.factory.makeGitRepository(name=u"foo")
        repository_before_modification = Snapshot(
            repository, providing=providedBy(repository))
        with person_logged_in(repository.owner):
            repository.subscribe(
                repository.owner,
                BranchSubscriptionNotificationLevel.ATTRIBUTEONLY,
                BranchSubscriptionDiffSize.NODIFF,
                CodeReviewNotificationLevel.NOEMAIL,
                repository.owner)
            repository.setName(u"bar", repository.owner)
            notify(ObjectModifiedEvent(
                repository, repository_before_modification, ["name"],
                user=repository.owner))
        transaction.commit()
        self.assertEqual(1, len(stub.test_emails))
        message = email.message_from_string(stub.test_emails[0][2])
        body = message.get_payload(decode=True)
        self.assertIn("Name: foo => bar\n", body)
        self.assertIn(
            "Git identity: lp:~{person}/{project}/+git/foo => "
            "lp:~{person}/{project}/+git/bar\n".format(
                person=repository.owner.name, project=repository.target.name),
            body)

    # XXX cjwatson 2015-02-04: This will need to be expanded once Launchpad
    # actually notices any interesting kind of repository modifications.


class TestGitRepositoryURLs(TestCaseWithFactory):
    """Tests for Git repository URLs."""

    layer = DatabaseFunctionalLayer

    def test_codebrowse_url(self):
        # The basic codebrowse URL for a repository is an 'https' URL.
        repository = self.factory.makeGitRepository()
        expected_url = urlutils.join(
            config.codehosting.git_browse_root, repository.unique_name)
        self.assertEqual(expected_url, repository.getCodebrowseUrl())

    def test_anon_url_for_public(self):
        # Public repositories have an anonymous URL, visible to anyone.
        repository = self.factory.makeGitRepository()
        expected_url = urlutils.join(
            config.codehosting.git_anon_root, repository.shortened_path)
        self.assertEqual(expected_url, repository.anon_url)

    def test_anon_url_not_for_private(self):
        # Private repositories do not have an anonymous URL.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        with person_logged_in(owner):
            self.assertIsNone(repository.anon_url)

    def test_ssh_url_for_public(self):
        # Public repositories have an SSH URL.
        repository = self.factory.makeGitRepository()
        expected_url = urlutils.join(
            config.codehosting.git_ssh_root, repository.shortened_path)
        self.assertEqual(expected_url, repository.ssh_url)

    def test_ssh_url_for_private(self):
        # Private repositories have an SSH URL.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        with person_logged_in(owner):
            expected_url = urlutils.join(
                config.codehosting.git_ssh_root, repository.shortened_path)
            self.assertEqual(expected_url, repository.ssh_url)


class TestGitRepositoryNamespace(TestCaseWithFactory):
    """Test `IGitRepository.namespace`."""

    layer = DatabaseFunctionalLayer

    def test_namespace_personal(self):
        # The namespace attribute of a personal repository points to the
        # namespace that corresponds to ~owner.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner, target=owner)
        namespace = getUtility(IGitNamespaceSet).get(person=owner)
        self.assertEqual(namespace, repository.namespace)

    def test_namespace_project(self):
        # The namespace attribute of a project repository points to the
        # namespace that corresponds to ~owner/project.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        namespace = getUtility(IGitNamespaceSet).get(
            person=repository.owner, project=project)
        self.assertEqual(namespace, repository.namespace)

    def test_namespace_package(self):
        # The namespace attribute of a package repository points to the
        # namespace that corresponds to
        # ~owner/distribution/+source/sourcepackagename.
        dsp = self.factory.makeDistributionSourcePackage()
        repository = self.factory.makeGitRepository(target=dsp)
        namespace = getUtility(IGitNamespaceSet).get(
            person=repository.owner, distribution=dsp.distribution,
            sourcepackagename=dsp.sourcepackagename)
        self.assertEqual(namespace, repository.namespace)


class TestGitRepositoryPendingWrites(TestCaseWithFactory):
    """Are there changes to this repository not reflected in the database?"""

    layer = LaunchpadFunctionalLayer

    def test_new_repository_no_writes(self):
        # New repositories have no pending writes.
        repository = self.factory.makeGitRepository()
        self.assertFalse(repository.pending_writes)

    def test_notify(self):
        # If the hosting service has just sent us a change notification,
        # then there are pending writes, but running the ref-scanning job
        # clears that flag.
        git_api = GitAPI(None, None)
        repository = self.factory.makeGitRepository()
        self.assertIsNone(git_api.notify(repository.getInternalPath()))
        self.assertTrue(repository.pending_writes)
        [job] = list(getUtility(IGitRefScanJobSource).iterReady())
        with dbuser("branchscanner"):
            JobRunner([job]).runAll()
        self.assertFalse(repository.pending_writes)


class TestGitRepositoryPrivacy(TestCaseWithFactory):
    """Tests for Git repository privacy."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        # Use an admin user as we aren't checking edit permissions here.
        super(TestGitRepositoryPrivacy, self).setUp("admin@canonical.com")

    def test_personal_repositories_for_private_teams_are_private(self):
        team = self.factory.makeTeam(
            membership_policy=TeamMembershipPolicy.MODERATED,
            visibility=PersonVisibility.PRIVATE)
        repository = self.factory.makeGitRepository(owner=team, target=team)
        self.assertTrue(repository.private)
        self.assertEqual(
            InformationType.PROPRIETARY, repository.information_type)

    def test__reconcileAccess_for_project_repository(self):
        # _reconcileAccess uses a project policy for a project repository.
        repository = self.factory.makeGitRepository(
            information_type=InformationType.USERDATA)
        [artifact] = getUtility(IAccessArtifactSource).ensure([repository])
        getUtility(IAccessPolicyArtifactSource).deleteByArtifact([artifact])
        removeSecurityProxy(repository)._reconcileAccess()
        self.assertContentEqual(
            getUtility(IAccessPolicySource).find(
                [(repository.target, InformationType.USERDATA)]),
            get_policies_for_artifact(repository))

    def test__reconcileAccess_for_package_repository(self):
        # Git repository privacy isn't yet supported for distributions, so
        # no AccessPolicyArtifact is created for a package repository.
        repository = self.factory.makeGitRepository(
            target=self.factory.makeDistributionSourcePackage(),
            information_type=InformationType.USERDATA)
        removeSecurityProxy(repository)._reconcileAccess()
        self.assertEqual([], get_policies_for_artifact(repository))

    def test__reconcileAccess_for_personal_repository(self):
        # _reconcileAccess uses a person policy for a personal repository.
        team_owner = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(
            owner=team_owner, target=team_owner,
            information_type=InformationType.USERDATA)
        removeSecurityProxy(repository)._reconcileAccess()
        self.assertContentEqual(
            getUtility(IAccessPolicySource).findByTeam([team_owner]),
            get_policies_for_artifact(repository))


class TestGitRepositoryRefs(TestCaseWithFactory):
    """Tests for ref handling."""

    layer = DatabaseFunctionalLayer

    def test__convertRefInfo(self):
        # _convertRefInfo converts a valid info dictionary.
        sha1 = unicode(hashlib.sha1("").hexdigest())
        info = {"object": {"sha1": sha1, "type": u"commit"}}
        expected_info = {"sha1": sha1, "type": GitObjectType.COMMIT}
        self.assertEqual(expected_info, GitRepository._convertRefInfo(info))

    def test__convertRefInfo_requires_object(self):
        self.assertRaisesWithContent(
            ValueError, 'ref info does not contain "object" key',
            GitRepository._convertRefInfo, {})

    def test__convertRefInfo_requires_object_sha1(self):
        self.assertRaisesWithContent(
            ValueError, 'ref info object does not contain "sha1" key',
            GitRepository._convertRefInfo, {"object": {}})

    def test__convertRefInfo_requires_object_type(self):
        info = {
            "object": {"sha1": u"0000000000000000000000000000000000000000"},
            }
        self.assertRaisesWithContent(
            ValueError, 'ref info object does not contain "type" key',
            GitRepository._convertRefInfo, info)

    def test__convertRefInfo_bad_sha1(self):
        info = {"object": {"sha1": "x", "type": "commit"}}
        self.assertRaisesWithContent(
            ValueError, 'ref info sha1 is not a 40-character string',
            GitRepository._convertRefInfo, info)

    def test__convertRefInfo_bad_type(self):
        info = {
            "object": {
                "sha1": u"0000000000000000000000000000000000000000",
                "type": u"nonsense",
                },
            }
        self.assertRaisesWithContent(
            ValueError, 'ref info type is not a recognised object type',
            GitRepository._convertRefInfo, info)

    def assertRefsMatch(self, refs, repository, paths):
        matchers = [
            MatchesStructure.byEquality(
                repository=repository,
                path=path,
                commit_sha1=unicode(hashlib.sha1(path).hexdigest()),
                object_type=GitObjectType.COMMIT)
            for path in paths]
        self.assertThat(refs, MatchesSetwise(*matchers))

    def test_create(self):
        repository = self.factory.makeGitRepository()
        self.assertEqual([], list(repository.refs))
        paths = (u"refs/heads/master", u"refs/tags/1.0")
        self.factory.makeGitRefs(repository=repository, paths=paths)
        self.assertRefsMatch(repository.refs, repository, paths)
        master_ref = repository.getRefByPath(u"refs/heads/master")
        new_refs_info = {
            u"refs/tags/1.1": {
                u"sha1": master_ref.commit_sha1,
                u"type": master_ref.object_type,
                },
            }
        repository.createOrUpdateRefs(new_refs_info)
        self.assertRefsMatch(
            [ref for ref in repository.refs if ref.path != u"refs/tags/1.1"],
            repository, paths)
        self.assertThat(
            repository.getRefByPath(u"refs/tags/1.1"),
            MatchesStructure.byEquality(
                repository=repository,
                path=u"refs/tags/1.1",
                commit_sha1=master_ref.commit_sha1,
                object_type=master_ref.object_type,
                ))

    def test_remove(self):
        repository = self.factory.makeGitRepository()
        paths = (u"refs/heads/master", u"refs/heads/branch", u"refs/tags/1.0")
        self.factory.makeGitRefs(repository=repository, paths=paths)
        self.assertRefsMatch(repository.refs, repository, paths)
        repository.removeRefs([u"refs/heads/branch", u"refs/tags/1.0"])
        self.assertRefsMatch(
            repository.refs, repository, [u"refs/heads/master"])

    def test_update(self):
        repository = self.factory.makeGitRepository()
        paths = (u"refs/heads/master", u"refs/tags/1.0")
        self.factory.makeGitRefs(repository=repository, paths=paths)
        self.assertRefsMatch(repository.refs, repository, paths)
        new_info = {
            u"sha1": u"0000000000000000000000000000000000000000",
            u"type": GitObjectType.BLOB,
            }
        repository.createOrUpdateRefs({u"refs/tags/1.0": new_info})
        self.assertRefsMatch(
            [ref for ref in repository.refs if ref.path != u"refs/tags/1.0"],
            repository, [u"refs/heads/master"])
        self.assertThat(
            repository.getRefByPath(u"refs/tags/1.0"),
            MatchesStructure.byEquality(
                repository=repository,
                path=u"refs/tags/1.0",
                commit_sha1=u"0000000000000000000000000000000000000000",
                object_type=GitObjectType.BLOB,
                ))

    def test_getRefByPath_without_leading_refs_heads(self):
        [ref] = self.factory.makeGitRefs(paths=[u"refs/heads/master"])
        self.assertEqual(
            ref, ref.repository.getRefByPath(u"refs/heads/master"))
        self.assertEqual(ref, ref.repository.getRefByPath(u"master"))
        self.assertIsNone(ref.repository.getRefByPath(u"other"))

    def test_planRefChanges(self):
        # planRefChanges copes with planning changes to refs in a repository
        # where some refs have been created, some deleted, and some changed.
        repository = self.factory.makeGitRepository()
        paths = (u"refs/heads/master", u"refs/heads/foo", u"refs/heads/bar")
        self.factory.makeGitRefs(repository=repository, paths=paths)
        self.assertRefsMatch(repository.refs, repository, paths)
        master_sha1 = repository.getRefByPath(u"refs/heads/master").commit_sha1
        foo_sha1 = repository.getRefByPath(u"refs/heads/foo").commit_sha1
        hosting_client = FakeMethod()
        hosting_client.getRefs = FakeMethod(result={
            u"refs/heads/master": {
                u"object": {
                    u"sha1": u"1111111111111111111111111111111111111111",
                    u"type": u"commit",
                    },
                },
            u"refs/heads/foo": {
                u"object": {
                    u"sha1": foo_sha1,
                    u"type": u"commit",
                    },
                },
            u"refs/tags/1.0": {
                u"object": {
                    u"sha1": master_sha1,
                    u"type": u"commit",
                    },
                },
            })
        refs_to_upsert, refs_to_remove = repository.planRefChanges(
            hosting_client, "dummy")

        expected_upsert = {
            u"refs/heads/master": {
                u"sha1": u"1111111111111111111111111111111111111111",
                u"type": GitObjectType.COMMIT,
                },
            u"refs/heads/foo": {
                u"sha1": unicode(hashlib.sha1(u"refs/heads/foo").hexdigest()),
                u"type": GitObjectType.COMMIT,
                },
            u"refs/tags/1.0": {
                u"sha1": unicode(
                    hashlib.sha1(u"refs/heads/master").hexdigest()),
                u"type": GitObjectType.COMMIT,
                },
            }
        self.assertEqual(expected_upsert, refs_to_upsert)
        self.assertEqual(set([u"refs/heads/bar"]), refs_to_remove)

    def test_planRefChanges_skips_non_commits(self):
        # planRefChanges does not attempt to update refs that point to
        # non-commits.
        repository = self.factory.makeGitRepository()
        blob_sha1 = unicode(hashlib.sha1(u"refs/heads/blob").hexdigest())
        refs_info = {
            u"refs/heads/blob": {
                u"sha1": blob_sha1,
                u"type": GitObjectType.BLOB,
                },
            }
        repository.createOrUpdateRefs(refs_info)
        hosting_client = FakeMethod()
        hosting_client.getRefs = FakeMethod(result={
            u"refs/heads/blob": {
                u"object": {
                    u"sha1": blob_sha1,
                    u"type": u"blob",
                    },
                },
            })
        self.assertEqual(
            ({}, set()), repository.planRefChanges(hosting_client, "dummy"))

    def test_fetchRefCommits(self):
        # fetchRefCommits fetches detailed tip commit metadata for the
        # requested refs.
        master_sha1 = unicode(hashlib.sha1(u"refs/heads/master").hexdigest())
        foo_sha1 = unicode(hashlib.sha1(u"refs/heads/foo").hexdigest())
        author = self.factory.makePerson()
        with person_logged_in(author):
            author_email = author.preferredemail.email
        epoch = datetime.fromtimestamp(0, tz=pytz.UTC)
        author_date = datetime(2015, 1, 1, tzinfo=pytz.UTC)
        committer_date = datetime(2015, 1, 2, tzinfo=pytz.UTC)
        hosting_client = FakeMethod()
        hosting_client.getCommits = FakeMethod(result=[
            {
                u"sha1": master_sha1,
                u"message": u"tip of master",
                u"author": {
                    u"name": author.displayname,
                    u"email": author_email,
                    u"time": int((author_date - epoch).total_seconds()),
                    },
                u"committer": {
                    u"name": u"New Person",
                    u"email": u"new-person@example.org",
                    u"time": int((committer_date - epoch).total_seconds()),
                    },
                u"parents": [],
                u"tree": unicode(hashlib.sha1("").hexdigest()),
                }])
        refs = {
            u"refs/heads/master": {
                u"sha1": master_sha1,
                u"type": GitObjectType.COMMIT,
                },
            u"refs/heads/foo": {
                u"sha1": foo_sha1,
                u"type": GitObjectType.COMMIT,
                },
            }
        GitRepository.fetchRefCommits(hosting_client, "dummy", refs)

        expected_oids = [master_sha1, foo_sha1]
        [(_, observed_oids)] = hosting_client.getCommits.extract_args()
        self.assertContentEqual(expected_oids, observed_oids)
        expected_author_addr = u"%s <%s>" % (author.displayname, author_email)
        [expected_author] = getUtility(IRevisionSet).acquireRevisionAuthors(
            [expected_author_addr]).values()
        expected_committer_addr = u"New Person <new-person@example.org>"
        [expected_committer] = getUtility(IRevisionSet).acquireRevisionAuthors(
            [expected_committer_addr]).values()
        expected_refs = {
            u"refs/heads/master": {
                u"sha1": master_sha1,
                u"type": GitObjectType.COMMIT,
                u"author": expected_author.id,
                u"author_addr": expected_author_addr,
                u"author_date": author_date,
                u"committer": expected_committer.id,
                u"committer_addr": expected_committer_addr,
                u"committer_date": committer_date,
                u"commit_message": u"tip of master",
                },
            u"refs/heads/foo": {
                u"sha1": foo_sha1,
                u"type": GitObjectType.COMMIT,
                },
            }
        self.assertEqual(expected_refs, refs)

    def test_synchroniseRefs(self):
        # synchroniseRefs copes with synchronising a repository where some
        # refs have been created, some deleted, and some changed.
        repository = self.factory.makeGitRepository()
        paths = (u"refs/heads/master", u"refs/heads/foo", u"refs/heads/bar")
        self.factory.makeGitRefs(repository=repository, paths=paths)
        self.assertRefsMatch(repository.refs, repository, paths)
        refs_to_upsert = {
            u"refs/heads/master": {
                u"sha1": u"1111111111111111111111111111111111111111",
                u"type": GitObjectType.COMMIT,
                },
            u"refs/heads/foo": {
                u"sha1": repository.getRefByPath(
                    u"refs/heads/foo").commit_sha1,
                u"type": GitObjectType.COMMIT,
                },
            u"refs/tags/1.0": {
                u"sha1": repository.getRefByPath(
                    u"refs/heads/master").commit_sha1,
                u"type": GitObjectType.COMMIT,
                },
            }
        refs_to_remove = set([u"refs/heads/bar"])
        repository.synchroniseRefs(refs_to_upsert, refs_to_remove)
        expected_sha1s = [
            (u"refs/heads/master",
             u"1111111111111111111111111111111111111111"),
            (u"refs/heads/foo",
             unicode(hashlib.sha1(u"refs/heads/foo").hexdigest())),
            (u"refs/tags/1.0",
             unicode(hashlib.sha1(u"refs/heads/master").hexdigest())),
            ]
        matchers = [
            MatchesStructure.byEquality(
                repository=repository,
                path=path,
                commit_sha1=sha1,
                object_type=GitObjectType.COMMIT,
                ) for path, sha1 in expected_sha1s]
        self.assertThat(repository.refs, MatchesSetwise(*matchers))


class TestGitRepositoryGetAllowedInformationTypes(TestCaseWithFactory):
    """Test `IGitRepository.getAllowedInformationTypes`."""

    layer = DatabaseFunctionalLayer

    def test_normal_user_sees_namespace_types(self):
        # An unprivileged user sees the types allowed by the namespace.
        repository = self.factory.makeGitRepository()
        policy = IGitNamespacePolicy(repository.namespace)
        self.assertContentEqual(
            policy.getAllowedInformationTypes(),
            repository.getAllowedInformationTypes(repository.owner))
        self.assertNotIn(
            InformationType.PROPRIETARY,
            repository.getAllowedInformationTypes(repository.owner))
        self.assertNotIn(
            InformationType.EMBARGOED,
            repository.getAllowedInformationTypes(repository.owner))

    def test_admin_sees_namespace_types(self):
        # An admin sees all the types, since they occasionally need to
        # override the namespace rules.  This is hopefully temporary, and
        # can go away once the new sharing rules (granting non-commercial
        # projects limited use of private repositories) are deployed.
        repository = self.factory.makeGitRepository()
        admin = self.factory.makeAdministrator()
        self.assertContentEqual(
            PUBLIC_INFORMATION_TYPES + PRIVATE_INFORMATION_TYPES,
            repository.getAllowedInformationTypes(admin))
        self.assertIn(
            InformationType.PROPRIETARY,
            repository.getAllowedInformationTypes(admin))


class TestGitRepositoryModerate(TestCaseWithFactory):
    """Test that project owners and commercial admins can moderate Git
    repositories."""

    layer = DatabaseFunctionalLayer

    def test_moderate_permission(self):
        # Test the ModerateGitRepository security checker.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        with person_logged_in(project.owner):
            self.assertTrue(check_permission("launchpad.Moderate", repository))
        with celebrity_logged_in("commercial_admin"):
            self.assertTrue(check_permission("launchpad.Moderate", repository))
        with person_logged_in(self.factory.makePerson()):
            self.assertFalse(
                check_permission("launchpad.Moderate", repository))

    def test_methods_smoketest(self):
        # Users with launchpad.Moderate can call transitionToInformationType.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        with person_logged_in(project.owner):
            project.setBranchSharingPolicy(BranchSharingPolicy.PUBLIC)
            repository.transitionToInformationType(
                InformationType.PRIVATESECURITY, project.owner)
            self.assertEqual(
                InformationType.PRIVATESECURITY, repository.information_type)

    def test_attribute_smoketest(self):
        # Users with launchpad.Moderate can set attributes.
        project = self.factory.makeProduct()
        repository = self.factory.makeGitRepository(target=project)
        with person_logged_in(project.owner):
            repository.description = u"something"
            repository.reviewer = project.owner
        self.assertEqual(u"something", repository.description)
        self.assertEqual(project.owner, repository.reviewer)


class TestGitRepositoryIsPersonTrustedReviewer(TestCaseWithFactory):
    """Test the `IGitRepository.isPersonTrustedReviewer` method."""

    layer = DatabaseFunctionalLayer

    def assertTrustedReviewer(self, repository, person):
        """Assert that `person` is a trusted reviewer for the `repository`."""
        self.assertTrue(repository.isPersonTrustedReviewer(person))

    def assertNotTrustedReviewer(self, repository, person):
        """Assert that `person` is not a trusted reviewer for the
        `repository`.
        """
        self.assertFalse(repository.isPersonTrustedReviewer(person))

    def test_none_is_not_trusted(self):
        # If None is passed in as the person, the method returns false.
        repository = self.factory.makeGitRepository()
        self.assertNotTrustedReviewer(repository, None)

    def test_repository_owner_is_trusted(self):
        # The repository owner is a trusted reviewer.
        repository = self.factory.makeGitRepository()
        self.assertTrustedReviewer(repository, repository.owner)

    def test_non_repository_owner_is_not_trusted(self):
        # Someone other than the repository owner is not a trusted reviewer.
        repository = self.factory.makeGitRepository()
        reviewer = self.factory.makePerson()
        self.assertNotTrustedReviewer(repository, reviewer)

    def test_lp_admins_always_trusted(self):
        # Launchpad admins are special, and as such, are trusted.
        repository = self.factory.makeGitRepository()
        admins = getUtility(ILaunchpadCelebrities).admin
        # Grab a random admin, the teamowner is good enough here.
        self.assertTrustedReviewer(repository, admins.teamowner)

    def test_member_of_team_owned_repository(self):
        # If the repository is owned by a team, any team member is a trusted
        # reviewer.
        team = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(owner=team)
        self.assertTrustedReviewer(repository, team.teamowner)

    def test_review_team_member_is_trusted(self):
        # If the reviewer is a member of the review team, but not the owner
        # they are still trusted.
        team = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(reviewer=team)
        self.assertTrustedReviewer(repository, team.teamowner)

    def test_repository_owner_not_review_team_member_is_trusted(self):
        # If the owner of the repository is not in the review team,
        #they are still trusted.
        team = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(reviewer=team)
        self.assertFalse(repository.owner.inTeam(team))
        self.assertTrustedReviewer(repository, repository.owner)

    def test_community_reviewer(self):
        # If the reviewer is not a member of the owner, or the review team,
        # they are not trusted reviewers.
        team = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(reviewer=team)
        reviewer = self.factory.makePerson()
        self.assertNotTrustedReviewer(repository, reviewer)


class TestGitRepositorySetName(TestCaseWithFactory):
    """Test `IGitRepository.setName`."""

    layer = DatabaseFunctionalLayer

    def test_not_owner(self):
        # A non-owner non-admin user cannot rename a repository.
        repository = self.factory.makeGitRepository()
        with person_logged_in(self.factory.makePerson()):
            self.assertRaises(Unauthorized, getattr, repository, "setName")

    def test_name_clash(self):
        # Name clashes are refused.
        repository = self.factory.makeGitRepository(name=u"foo")
        self.factory.makeGitRepository(
            owner=repository.owner, target=repository.target, name=u"bar")
        with person_logged_in(repository.owner):
            self.assertRaises(
                GitRepositoryExists, repository.setName,
                u"bar", repository.owner)

    def test_rename(self):
        # A non-clashing rename request works.
        repository = self.factory.makeGitRepository(name=u"foo")
        with person_logged_in(repository.owner):
            repository.setName(u"bar", repository.owner)
        self.assertEqual(u"bar", repository.name)


class TestGitRepositorySetOwner(TestCaseWithFactory):
    """Test `IGitRepository.setOwner`."""

    layer = DatabaseFunctionalLayer

    def test_owner_sets_team(self):
        # The owner of the repository can set the owner of the repository to
        # be a team they are a member of.
        repository = self.factory.makeGitRepository()
        team = self.factory.makeTeam(owner=repository.owner)
        with person_logged_in(repository.owner):
            repository.setOwner(team, repository.owner)
        self.assertEqual(team, repository.owner)

    def test_owner_cannot_set_nonmember_team(self):
        # The owner of the repository cannot set the owner to be a team they
        # are not a member of.
        repository = self.factory.makeGitRepository()
        team = self.factory.makeTeam()
        with person_logged_in(repository.owner):
            self.assertRaises(
                GitRepositoryCreatorNotMemberOfOwnerTeam,
                repository.setOwner, team, repository.owner)

    def test_owner_cannot_set_other_user(self):
        # The owner of the repository cannot set the new owner to be another
        # person.
        repository = self.factory.makeGitRepository()
        person = self.factory.makePerson()
        with person_logged_in(repository.owner):
            self.assertRaises(
                GitRepositoryCreatorNotOwner,
                repository.setOwner, person, repository.owner)

    def test_admin_can_set_any_team_or_person(self):
        # A Launchpad admin can set the repository to be owned by any team
        # or person.
        repository = self.factory.makeGitRepository()
        team = self.factory.makeTeam()
        # To get a random administrator, choose the admin team owner.
        admin = getUtility(ILaunchpadCelebrities).admin.teamowner
        with person_logged_in(admin):
            repository.setOwner(team, admin)
            self.assertEqual(team, repository.owner)
            person = self.factory.makePerson()
            repository.setOwner(person, admin)
            self.assertEqual(person, repository.owner)

    def test_private_personal_forbidden_for_public_teams(self):
        # Only private teams can have private personal repositories.
        person = self.factory.makePerson()
        private_team = self.factory.makeTeam(
            owner=person, membership_policy=TeamMembershipPolicy.MODERATED,
            visibility=PersonVisibility.PRIVATE)
        public_team = self.factory.makeTeam(owner=person)
        with person_logged_in(person):
            repository = self.factory.makeGitRepository(
                owner=private_team, target=private_team,
                information_type=InformationType.USERDATA)
            self.assertRaises(
                GitTargetError, repository.setOwner, public_team, person)

    def test_private_personal_allowed_for_private_teams(self):
        # Only private teams can have private personal repositories.
        person = self.factory.makePerson()
        private_team_1 = self.factory.makeTeam(
            owner=person, membership_policy=TeamMembershipPolicy.MODERATED,
            visibility=PersonVisibility.PRIVATE)
        private_team_2 = self.factory.makeTeam(
            owner=person, membership_policy=TeamMembershipPolicy.MODERATED,
            visibility=PersonVisibility.PRIVATE)
        with person_logged_in(person):
            repository = self.factory.makeGitRepository(
                owner=private_team_1, target=private_team_1,
                information_type=InformationType.USERDATA)
            repository.setOwner(private_team_2, person)
            self.assertEqual(private_team_2, repository.owner)
            self.assertEqual(private_team_2, repository.target)

    def test_reconciles_access(self):
        # setOwner calls _reconcileAccess to make the sharing schema correct
        # when changing the owner of a private personal repository.
        person = self.factory.makePerson()
        team = self.factory.makeTeam(
            owner=person, visibility=PersonVisibility.PRIVATE)
        with person_logged_in(person):
            repository = self.factory.makeGitRepository(
                owner=person, target=person,
                information_type=InformationType.USERDATA)
            repository.setOwner(team, person)
        self.assertEqual(
            team, get_policies_for_artifact(repository)[0].person)


class TestGitRepositorySetTarget(TestCaseWithFactory):
    """Test `IGitRepository.setTarget`."""

    layer = DatabaseFunctionalLayer

    def test_personal_to_other_personal(self):
        # A personal repository can be moved to a different owner.
        person = self.factory.makePerson()
        team = self.factory.makeTeam(owner=person)
        repository = self.factory.makeGitRepository(
            owner=person, target=person)
        with person_logged_in(person):
            repository.setTarget(target=team, user=repository.owner)
        self.assertEqual(team, repository.owner)
        self.assertEqual(team, repository.target)

    def test_personal_to_project(self):
        # A personal repository can be moved to a project.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner, target=owner)
        project = self.factory.makeProduct()
        with person_logged_in(owner):
            repository.setTarget(target=project, user=owner)
        self.assertEqual(project, repository.target)

    def test_personal_to_package(self):
        # A personal repository can be moved to a package.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner, target=owner)
        dsp = self.factory.makeDistributionSourcePackage()
        with person_logged_in(owner):
            repository.setTarget(target=dsp, user=owner)
        self.assertEqual(dsp, repository.target)

    def test_project_to_other_project(self):
        # Move a repository from one project to another.
        repository = self.factory.makeGitRepository()
        project = self.factory.makeProduct()
        with person_logged_in(repository.owner):
            repository.setTarget(target=project, user=repository.owner)
        self.assertEqual(project, repository.target)

    def test_project_to_package(self):
        # Move a repository from a project to a package.
        repository = self.factory.makeGitRepository()
        dsp = self.factory.makeDistributionSourcePackage()
        with person_logged_in(repository.owner):
            repository.setTarget(target=dsp, user=repository.owner)
        self.assertEqual(dsp, repository.target)

    def test_project_to_personal(self):
        # Move a repository from a project to a personal namespace.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=owner)
        with person_logged_in(owner):
            repository.setTarget(target=owner, user=owner)
        self.assertEqual(owner, repository.target)

    def test_package_to_other_package(self):
        # Move a repository from one package to another.
        repository = self.factory.makeGitRepository(
            target=self.factory.makeDistributionSourcePackage())
        dsp = self.factory.makeDistributionSourcePackage()
        with person_logged_in(repository.owner):
            repository.setTarget(target=dsp, user=repository.owner)
        self.assertEqual(dsp, repository.target)

    def test_package_to_project(self):
        # Move a repository from a package to a project.
        repository = self.factory.makeGitRepository(
            target=self.factory.makeDistributionSourcePackage())
        project = self.factory.makeProduct()
        with person_logged_in(repository.owner):
            repository.setTarget(target=project, user=repository.owner)
        self.assertEqual(project, repository.target)

    def test_package_to_personal(self):
        # Move a repository from a package to a personal namespace.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(
            owner=owner, target=self.factory.makeDistributionSourcePackage())
        with person_logged_in(owner):
            repository.setTarget(target=owner, user=owner)
        self.assertEqual(owner, repository.target)

    def test_private_personal_forbidden_for_public_teams(self):
        # Only private teams can have private personal repositories.
        owner = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        with admin_logged_in():
            self.assertRaises(
                GitTargetError, repository.setTarget, target=owner, user=owner)

    def test_private_personal_allowed_for_private_teams(self):
        # Only private teams can have private personal repositories.
        owner = self.factory.makeTeam(visibility=PersonVisibility.PRIVATE)
        with person_logged_in(owner):
            repository = self.factory.makeGitRepository(
                owner=owner, information_type=InformationType.USERDATA)
            repository.setTarget(target=owner, user=owner)
            self.assertEqual(owner, repository.target)

    def test_reconciles_access(self):
        # setTarget calls _reconcileAccess to make the sharing schema
        # match the new target.
        repository = self.factory.makeGitRepository(
            information_type=InformationType.USERDATA)
        new_project = self.factory.makeProduct()
        with admin_logged_in():
            repository.setTarget(target=new_project, user=repository.owner)
        self.assertEqual(
            new_project, get_policies_for_artifact(repository)[0].pillar)

    def test_reconciles_access_personal(self):
        # setTarget calls _reconcileAccess to make the sharing schema
        # correct for a private personal repository.
        owner = self.factory.makeTeam(visibility=PersonVisibility.PRIVATE)
        with person_logged_in(owner):
            repository = self.factory.makeGitRepository(
                owner=owner,
                information_type=InformationType.USERDATA)
            repository.setTarget(target=owner, user=owner)
        self.assertEqual(
            owner, get_policies_for_artifact(repository)[0].person)

    def test_public_to_proprietary_only_project(self):
        # A repository cannot be moved to a target where the sharing policy
        # does not allow it.
        owner = self.factory.makePerson()
        commercial_project = self.factory.makeProduct(
            owner=owner, branch_sharing_policy=BranchSharingPolicy.PROPRIETARY)
        repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.PUBLIC)
        with admin_logged_in():
            self.assertRaises(
                GitTargetError, repository.setTarget,
                target=commercial_project, user=owner)


class TestGitRepositorySet(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestGitRepositorySet, self).setUp()
        self.repository_set = getUtility(IGitRepositorySet)

    def test_provides_IGitRepositorySet(self):
        # GitRepositorySet instances provide IGitRepositorySet.
        verifyObject(IGitRepositorySet, self.repository_set)

    def test_getByPath(self):
        # getByPath returns a repository matching the path that it's given.
        a = self.factory.makeGitRepository()
        self.factory.makeGitRepository()
        repository = self.repository_set.getByPath(a.owner, a.shortened_path)
        self.assertEqual(a, repository)

    def test_getByPath_not_found(self):
        # If a repository cannot be found for a path, then getByPath returns
        # None.
        person = self.factory.makePerson()
        self.assertIsNone(self.repository_set.getByPath(person, "nonexistent"))

    def test_getByPath_inaccessible(self):
        # If the given user cannot view the matched repository, then
        # getByPath returns None.
        owner = self.factory.makePerson()
        repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        with person_logged_in(owner):
            path = repository.shortened_path
        self.assertEqual(
            repository, self.repository_set.getByPath(owner, path))
        self.assertIsNone(
            self.repository_set.getByPath(self.factory.makePerson(), path))

    def test_getRepositories(self):
        # getRepositories returns a collection of repositories for the given
        # target.
        project = self.factory.makeProduct()
        repositories = [
            self.factory.makeGitRepository(target=project) for _ in range(5)]
        self.assertContentEqual(
            repositories, self.repository_set.getRepositories(None, project))

    def test_getRepositories_inaccessible(self):
        # getRepositories only returns repositories that the given user can
        # see.
        person = self.factory.makePerson()
        project = self.factory.makeProduct()
        public_repositories = [
            self.factory.makeGitRepository(owner=person, target=project)
            for _ in range(3)]
        other_person = self.factory.makePerson()
        private_repository = self.factory.makeGitRepository(
            owner=other_person, target=project,
            information_type=InformationType.USERDATA)
        self.assertContentEqual(
            public_repositories,
            self.repository_set.getRepositories(None, project))
        self.assertContentEqual(
            public_repositories,
            self.repository_set.getRepositories(person, project))
        self.assertContentEqual(
            public_repositories + [private_repository],
            self.repository_set.getRepositories(other_person, project))

    def test_getRepositoryVisibilityInfo_empty_repository_names(self):
        # If repository_names is empty, getRepositoryVisibilityInfo returns
        # an empty visible_repositories list.
        person = self.factory.makePerson(name="fred")
        info = self.repository_set.getRepositoryVisibilityInfo(
            person, person, repository_names=[])
        self.assertEqual("Fred", info["person_name"])
        self.assertEqual([], info["visible_repositories"])

    def test_getRepositoryVisibilityInfo(self):
        person = self.factory.makePerson(name="fred")
        owner = self.factory.makePerson()
        visible_repository = self.factory.makeGitRepository()
        invisible_repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        invisible_name = removeSecurityProxy(invisible_repository).unique_name
        repositories = [visible_repository.unique_name, invisible_name]

        with person_logged_in(owner):
            info = self.repository_set.getRepositoryVisibilityInfo(
                owner, person, repository_names=repositories)
        self.assertEqual("Fred", info["person_name"])
        self.assertEqual(
            [visible_repository.unique_name], info["visible_repositories"])

    def test_getRepositoryVisibilityInfo_unauthorised_user(self):
        # If the user making the API request cannot see one of the
        # repositories, that repository is not included in the results.
        person = self.factory.makePerson(name="fred")
        owner = self.factory.makePerson()
        visible_repository = self.factory.makeGitRepository()
        invisible_repository = self.factory.makeGitRepository(
            owner=owner, information_type=InformationType.USERDATA)
        invisible_name = removeSecurityProxy(invisible_repository).unique_name
        repositories = [visible_repository.unique_name, invisible_name]

        someone = self.factory.makePerson()
        with person_logged_in(someone):
            info = self.repository_set.getRepositoryVisibilityInfo(
                someone, person, repository_names=repositories)
        self.assertEqual("Fred", info["person_name"])
        self.assertEqual(
            [visible_repository.unique_name], info["visible_repositories"])

    def test_getRepositoryVisibilityInfo_anonymous(self):
        # Anonymous users are not allowed to see any repository visibility
        # information, even if the repository they are querying about is
        # public.
        person = self.factory.makePerson(name="fred")
        owner = self.factory.makePerson()
        visible_repository = self.factory.makeGitRepository(owner=owner)
        repositories = [visible_repository.unique_name]

        with person_logged_in(owner):
            info = self.repository_set.getRepositoryVisibilityInfo(
                None, person, repository_names=repositories)
        self.assertEqual({}, info)

    def test_getRepositoryVisibilityInfo_invalid_repository_name(self):
        # If an invalid repository name is specified, it is not included.
        person = self.factory.makePerson(name="fred")
        owner = self.factory.makePerson()
        visible_repository = self.factory.makeGitRepository(owner=owner)
        repositories = [
            visible_repository.unique_name,
            "invalid_repository_name"]

        with person_logged_in(owner):
            info = self.repository_set.getRepositoryVisibilityInfo(
                owner, person, repository_names=repositories)
        self.assertEqual("Fred", info["person_name"])
        self.assertEqual(
            [visible_repository.unique_name], info["visible_repositories"])

    def test_setDefaultRepository_refuses_person(self):
        # setDefaultRepository refuses if the target is a person.
        person = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=person)
        with person_logged_in(person):
            self.assertRaises(
                GitTargetError, self.repository_set.setDefaultRepository,
                person, repository)

    def test_setDefaultRepositoryForOwner_refuses_person(self):
        # setDefaultRepositoryForOwner refuses if the target is a person.
        person = self.factory.makePerson()
        repository = self.factory.makeGitRepository(owner=person)
        with person_logged_in(person) as user:
            self.assertRaises(
                GitTargetError,
                self.repository_set.setDefaultRepositoryForOwner,
                person, person, repository, user)


class TestGitRepositorySetDefaultsMixin:

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestGitRepositorySetDefaultsMixin, self).setUp()
        self.repository_set = getUtility(IGitRepositorySet)
        self.get_method = self.repository_set.getDefaultRepository
        self.set_method = (lambda target, repository, user:
            self.repository_set.setDefaultRepository(target, repository))

    def makeGitRepository(self, target):
        return self.factory.makeGitRepository(target=target)

    def test_default_repository_round_trip(self):
        # A target's default Git repository set using setDefaultRepository*
        # can be retrieved using getDefaultRepository*.
        target = self.makeTarget()
        repository = self.makeGitRepository(target)
        self.assertIsNone(self.get_method(target))
        with person_logged_in(self.getPersonForLogin(target)) as user:
            self.set_method(target, repository, user)
        self.assertEqual(repository, self.get_method(target))

    def test_set_default_repository_None(self):
        # setDefaultRepository*(target, None) clears the default.
        target = self.makeTarget()
        repository = self.makeGitRepository(target)
        with person_logged_in(self.getPersonForLogin(target)) as user:
            self.set_method(target, repository, user)
            self.set_method(target, None, user)
        self.assertIsNone(self.get_method(target))

    def test_set_default_repository_different_target(self):
        # setDefaultRepository* refuses if the repository is attached to a
        # different target.
        target = self.makeTarget()
        other_target = self.makeTarget(template=target)
        repository = self.makeGitRepository(other_target)
        with person_logged_in(self.getPersonForLogin(target)) as user:
            self.assertRaises(
                GitTargetError, self.set_method, target, repository, user)


class TestGitRepositorySetDefaultsProject(
    TestGitRepositorySetDefaultsMixin, TestCaseWithFactory):

    def makeTarget(self, template=None):
        return self.factory.makeProduct()

    @staticmethod
    def getPersonForLogin(target):
        return target.owner


class TestGitRepositorySetDefaultsPackage(
    TestGitRepositorySetDefaultsMixin, TestCaseWithFactory):

    def makeTarget(self, template=None):
        kwargs = {}
        if template is not None:
            kwargs["distribution"] = template.distribution
        return self.factory.makeDistributionSourcePackage(**kwargs)

    @staticmethod
    def getPersonForLogin(target):
        return target.distribution.owner


class TestGitRepositorySetDefaultsOwnerMixin(
    TestGitRepositorySetDefaultsMixin):

    def setUp(self):
        super(TestGitRepositorySetDefaultsOwnerMixin, self).setUp()
        self.person = self.factory.makePerson()
        self.get_method = partial(
            self.repository_set.getDefaultRepositoryForOwner, self.person)
        self.set_method = partial(
            self.repository_set.setDefaultRepositoryForOwner, self.person)

    def makeGitRepository(self, target):
        return self.factory.makeGitRepository(owner=self.person, target=target)

    def getPersonForLogin(self, target):
        return self.person

    def test_set_default_repository_for_owner_team_member(self):
        # A member of the owner team can use setDefaultRepositoryForOwner.
        target = self.makeTarget()
        team = self.factory.makeTeam(members=[self.person])
        repository = self.factory.makeGitRepository(owner=team, target=target)
        self.assertIsNone(
            self.repository_set.getDefaultRepositoryForOwner(team, target))
        with person_logged_in(self.person) as user:
            self.repository_set.setDefaultRepositoryForOwner(
                team, target, repository, user)
        self.assertEqual(
            repository,
            self.repository_set.getDefaultRepositoryForOwner(team, target))

    def test_set_default_repository_for_owner_not_team_member(self):
        # A non-member of the owner team cannot use
        # setDefaultRepositoryForOwner.
        target = self.makeTarget()
        team = self.factory.makeTeam()
        repository = self.factory.makeGitRepository(owner=team, target=target)
        self.assertIsNone(
            self.repository_set.getDefaultRepositoryForOwner(team, target))
        with person_logged_in(self.person) as user:
            self.assertRaises(
                Unauthorized, self.repository_set.setDefaultRepositoryForOwner,
                team, target, repository, user)


class TestGitRepositorySetDefaultsOwnerProject(
    TestGitRepositorySetDefaultsOwnerMixin,
    TestGitRepositorySetDefaultsProject):
    pass


class TestGitRepositorySetDefaultsOwnerPackage(
    TestGitRepositorySetDefaultsOwnerMixin,
    TestGitRepositorySetDefaultsPackage):
    pass


class TestGitRepositoryWebservice(TestCaseWithFactory):
    """Tests for the webservice."""

    layer = DatabaseFunctionalLayer

    def test_getRepositories_project(self):
        project_db = self.factory.makeProduct()
        repository_db = self.factory.makeGitRepository(target=project_db)
        webservice = webservice_for_person(
            repository_db.owner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            owner_url = api_url(repository_db.owner)
            project_url = api_url(project_db)
        response = webservice.named_get(
            "/+git", "getRepositories", user=owner_url, target=project_url)
        self.assertEqual(200, response.status)
        self.assertEqual(
            [webservice.getAbsoluteUrl(repository_url)],
            [entry["self_link"] for entry in response.jsonBody()["entries"]])

    def test_getRepositories_package(self):
        dsp_db = self.factory.makeDistributionSourcePackage()
        repository_db = self.factory.makeGitRepository(target=dsp_db)
        webservice = webservice_for_person(
            repository_db.owner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            owner_url = api_url(repository_db.owner)
            dsp_url = api_url(dsp_db)
        response = webservice.named_get(
            "/+git", "getRepositories", user=owner_url, target=dsp_url)
        self.assertEqual(200, response.status)
        self.assertEqual(
            [webservice.getAbsoluteUrl(repository_url)],
            [entry["self_link"] for entry in response.jsonBody()["entries"]])

    def test_getRepositories_personal(self):
        owner_db = self.factory.makePerson()
        repository_db = self.factory.makeGitRepository(
            owner=owner_db, target=owner_db)
        webservice = webservice_for_person(
            owner_db, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            owner_url = api_url(owner_db)
        response = webservice.named_get(
            "/+git", "getRepositories", user=owner_url, target=owner_url)
        self.assertEqual(200, response.status)
        self.assertEqual(
            [webservice.getAbsoluteUrl(repository_url)],
            [entry["self_link"] for entry in response.jsonBody()["entries"]])

    def test_set_information_type(self):
        # The repository owner can change the information type.
        repository_db = self.factory.makeGitRepository()
        webservice = webservice_for_person(
            repository_db.owner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"information_type": "Public Security"}))
        self.assertEqual(209, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(
                InformationType.PUBLICSECURITY, repository_db.information_type)

    def test_set_information_type_other_person(self):
        # An unrelated user cannot change the information type.
        repository_db = self.factory.makeGitRepository()
        webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"information_type": "Public Security"}))
        self.assertEqual(401, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(
                InformationType.PUBLIC, repository_db.information_type)

    def test_set_target(self):
        # The repository owner can move the repository to another target;
        # this redirects to the new location.
        repository_db = self.factory.makeGitRepository()
        new_project_db = self.factory.makeProduct()
        webservice = webservice_for_person(
            repository_db.owner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            new_project_url = api_url(new_project_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"target_link": new_project_url}))
        self.assertEqual(301, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(
                webservice.getAbsoluteUrl(api_url(repository_db)),
                response.getHeader("Location"))
            self.assertEqual(new_project_db, repository_db.target)

    def test_set_target_other_person(self):
        # An unrelated person cannot change the target.
        project_db = self.factory.makeProduct()
        repository_db = self.factory.makeGitRepository(target=project_db)
        new_project_db = self.factory.makeProduct()
        webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            new_project_url = api_url(new_project_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"target_link": new_project_url}))
        self.assertEqual(401, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(project_db, repository_db.target)

    def test_set_owner(self):
        # The repository owner can reassign the repository to a team they're
        # a member of; this redirects to the new location.
        repository_db = self.factory.makeGitRepository()
        new_owner_db = self.factory.makeTeam(members=[repository_db.owner])
        webservice = webservice_for_person(
            repository_db.owner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            new_owner_url = api_url(new_owner_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"owner_link": new_owner_url}))
        self.assertEqual(301, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(
                webservice.getAbsoluteUrl(api_url(repository_db)),
                response.getHeader("Location"))
            self.assertEqual(new_owner_db, repository_db.owner)

    def test_set_owner_other_person(self):
        # An unrelated person cannot change the owner.
        owner_db = self.factory.makePerson()
        repository_db = self.factory.makeGitRepository(owner=owner_db)
        new_owner_db = self.factory.makeTeam()
        webservice = webservice_for_person(
            new_owner_db.teamowner, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            new_owner_url = api_url(new_owner_db)
        response = webservice.patch(
            repository_url, "application/json",
            json.dumps({"owner_link": new_owner_url}))
        self.assertEqual(401, response.status)
        with person_logged_in(ANONYMOUS):
            self.assertEqual(owner_db, repository_db.owner)

    def test_subscribe(self):
        # A user can subscribe to a repository.
        repository_db = self.factory.makeGitRepository()
        subscriber_db = self.factory.makePerson()
        webservice = webservice_for_person(
            subscriber_db, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        with person_logged_in(ANONYMOUS):
            repository_url = api_url(repository_db)
            subscriber_url = api_url(subscriber_db)
        response = webservice.named_post(
            repository_url, "subscribe", person=subscriber_url,
            notification_level=u"Branch attribute notifications only",
            max_diff_lines=u"Don't send diffs", code_review_level=u"No email")
        self.assertEqual(200, response.status)
        with person_logged_in(ANONYMOUS):
            subscription_db = repository_db.getSubscription(subscriber_db)
            self.assertIsNotNone(subscription_db)
            self.assertThat(
                response.jsonBody()["self_link"],
                EndsWith(api_url(subscription_db)))

    def _makeSubscription(self, repository, subscriber):
        with person_logged_in(subscriber):
            return repository.subscribe(
                person=subscriber,
                notification_level=(
                    BranchSubscriptionNotificationLevel.ATTRIBUTEONLY),
                max_diff_lines=BranchSubscriptionDiffSize.NODIFF,
                code_review_level=CodeReviewNotificationLevel.NOEMAIL,
                subscribed_by=subscriber)

    def test_getSubscription(self):
        # It is possible to get a single subscription via the webservice.
        repository_db = self.factory.makeGitRepository()
        subscriber_db = self.factory.makePerson()
        subscription_db = self._makeSubscription(repository_db, subscriber_db)
        with person_logged_in(subscriber_db):
            repository_url = api_url(repository_db)
            subscriber_url = api_url(subscriber_db)
            subscription_url = api_url(subscription_db)
        webservice = webservice_for_person(
            subscriber_db, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        response = webservice.named_get(
            repository_url, "getSubscription", person=subscriber_url)
        self.assertEqual(200, response.status)
        self.assertThat(
            response.jsonBody()["self_link"], EndsWith(subscription_url))

    def test_edit_subscription(self):
        # An existing subscription can be edited via the webservice, by
        # subscribing the same person again with different details.
        repository_db = self.factory.makeGitRepository()
        subscriber_db = self.factory.makePerson()
        self._makeSubscription(repository_db, subscriber_db)
        with person_logged_in(subscriber_db):
            repository_url = api_url(repository_db)
            subscriber_url = api_url(subscriber_db)
        webservice = webservice_for_person(
            subscriber_db, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        response = webservice.named_post(
            repository_url, "subscribe", person=subscriber_url,
            notification_level=u"No email",
            max_diff_lines=u"Send entire diff",
            code_review_level=u"Status changes only")
        self.assertEqual(200, response.status)
        with person_logged_in(subscriber_db):
            self.assertThat(
                repository_db.getSubscription(subscriber_db),
                MatchesStructure.byEquality(
                    person=subscriber_db,
                    notification_level=(
                        BranchSubscriptionNotificationLevel.NOEMAIL),
                    max_diff_lines=BranchSubscriptionDiffSize.WHOLEDIFF,
                    review_level=CodeReviewNotificationLevel.STATUS,
                    ))
        repository = webservice.get(repository_url).jsonBody()
        subscribers = webservice.get(
            repository["subscribers_collection_link"]).jsonBody()
        self.assertEqual(2, len(subscribers["entries"]))
        with person_logged_in(subscriber_db):
            self.assertContentEqual(
                [repository_db.owner.name, subscriber_db.name],
                [subscriber["name"] for subscriber in subscribers["entries"]])

    def test_unsubscribe(self):
        # It is possible to unsubscribe via the webservice.
        repository_db = self.factory.makeGitRepository()
        subscriber_db = self.factory.makePerson()
        self._makeSubscription(repository_db, subscriber_db)
        with person_logged_in(subscriber_db):
            repository_url = api_url(repository_db)
            subscriber_url = api_url(subscriber_db)
        webservice = webservice_for_person(
            subscriber_db, permission=OAuthPermission.WRITE_PUBLIC)
        webservice.default_api_version = "devel"
        response = webservice.named_post(
            repository_url, "unsubscribe", person=subscriber_url)
        self.assertEqual(200, response.status)
        with person_logged_in(subscriber_db):
            self.assertNotIn(subscriber_db, repository_db.subscribers)
