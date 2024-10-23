# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test RecipeBuildBehaviour."""

import os.path
import shutil
import tempfile

import transaction
from testtools.matchers import MatchesListwise
from testtools.twistedsupport import AsynchronousDeferredRunTest
from twisted.internet import defer
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.archivepublisher.interfaces.archivegpgsigningkey import (
    IArchiveGPGSigningKey,
)
from lp.buildmaster.enums import BuildStatus
from lp.buildmaster.interactor import BuilderInteractor
from lp.buildmaster.interfaces.buildfarmjobbehaviour import (
    IBuildFarmJobBehaviour,
)
from lp.buildmaster.interfaces.processor import IProcessorSet
from lp.buildmaster.tests.mock_workers import (
    MockBuilder,
    OkWorker,
    WaitingWorker,
)
from lp.buildmaster.tests.test_buildfarmjobbehaviour import (
    TestGetUploadMethodsMixin,
    TestHandleStatusMixin,
    TestVerifySuccessfulBuildMixin,
)
from lp.code.model.recipebuilder import RecipeBuildBehaviour
from lp.code.model.sourcepackagerecipebuild import SourcePackageRecipeBuild
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.registry.interfaces.series import SeriesStatus
from lp.services.config import config
from lp.services.log.logger import BufferLogger
from lp.services.webapp import canonical_url
from lp.soyuz.adapters.archivedependencies import get_sources_list_for_building
from lp.soyuz.enums import ArchivePurpose, PackagePublishingStatus
from lp.soyuz.tests.soyuz import Base64KeyMatches
from lp.soyuz.tests.test_publishing import SoyuzTestPublisher
from lp.testing import TestCaseWithFactory, person_logged_in
from lp.testing.fakemethod import FakeMethod
from lp.testing.gpgkeys import gpgkeysdir
from lp.testing.keyserver import InProcessKeyServerFixture
from lp.testing.layers import LaunchpadZopelessLayer, ZopelessDatabaseLayer
from lp.testing.mail_helpers import pop_notifications


class TestRecipeBuilderBase(TestCaseWithFactory):
    layer = ZopelessDatabaseLayer

    def makeJob(
        self,
        recipe_registrant=None,
        recipe_owner=None,
        archive=None,
        git=False,
        with_builder=False,
    ):
        """Create a sample `ISourcePackageRecipeBuild`."""
        spn = self.factory.makeSourcePackageName("apackage")
        if archive is None:
            distro = self.factory.makeDistribution(name="distro")
        else:
            distro = archive.distribution
        distroseries = self.factory.makeDistroSeries(
            name="mydistro", distribution=distro
        )
        processor = getUtility(IProcessorSet).getByName("386")
        distroseries.nominatedarchindep = distroseries.newArch(
            "i386", processor, True, self.factory.makePerson()
        )
        for component_name in ("main", "universe"):
            self.factory.makeComponentSelection(distroseries, component_name)
        sourcepackage = self.factory.makeSourcePackage(spn, distroseries)
        if recipe_registrant is None:
            recipe_registrant = self.factory.makePerson(
                email="requester@ubuntu.com",
                name="joe",
                displayname="Joe User",
            )
        if recipe_owner is None:
            recipe_owner = recipe_registrant
        if git:
            [somebranch] = self.factory.makeGitRefs(
                owner=recipe_owner,
                name="pkg",
                target=self.factory.makeProduct("someapp"),
                paths=["refs/heads/packaging"],
            )
        else:
            somebranch = self.factory.makeBranch(
                owner=recipe_owner,
                name="pkg",
                product=self.factory.makeProduct("someapp"),
            )
        recipe = self.factory.makeSourcePackageRecipe(
            recipe_registrant,
            recipe_owner,
            distroseries,
            "recept",
            "Recipe description",
            branches=[somebranch],
        )
        spb = self.factory.makeSourcePackageRecipeBuild(
            sourcepackage=sourcepackage,
            archive=archive,
            recipe=recipe,
            requester=recipe_owner,
            distroseries=distroseries,
        )
        job = IBuildFarmJobBehaviour(spb)
        if with_builder:
            builder = MockBuilder()
            builder.processor = processor
            job.setBuilder(builder, None)
        return job


class TestRecipeBuilder(TestRecipeBuilderBase):
    def test_providesInterface(self):
        # RecipeBuildBehaviour provides IBuildFarmJobBehaviour.
        recipe_builder = RecipeBuildBehaviour(None)
        self.assertProvides(recipe_builder, IBuildFarmJobBehaviour)

    def test_adapts_ISourcePackageRecipeBuild(self):
        # IBuildFarmJobBehaviour adapts a ISourcePackageRecipeBuild
        build = self.factory.makeSourcePackageRecipeBuild()
        job = IBuildFarmJobBehaviour(build)
        self.assertProvides(job, IBuildFarmJobBehaviour)

    def test_verifyBuildRequest_valid(self):
        # VerifyBuildRequest won't raise any exceptions when called with a
        # valid builder set.
        job = self.makeJob()
        builder = MockBuilder("bob-de-bouwer")
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        job.verifyBuildRequest(logger)
        self.assertEqual("", logger.getLogBuffer())

    def test_verifyBuildRequest_non_virtual(self):
        # verifyBuildRequest will raise if a non-virtual builder is proposed.
        job = self.makeJob()
        builder = MockBuilder("non-virtual builder")
        builder.virtualized = False
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        e = self.assertRaises(AssertionError, job.verifyBuildRequest, logger)
        self.assertEqual(
            "Attempt to build virtual item on a non-virtual builder.", str(e)
        )

    def test_verifyBuildRequest_bad_pocket(self):
        # verifyBuildRequest will raise if a bad pocket is proposed.
        build = self.factory.makeSourcePackageRecipeBuild(
            pocket=PackagePublishingPocket.SECURITY
        )
        job = IBuildFarmJobBehaviour(build)
        job.setBuilder(MockBuilder("bob-de-bouwer"), OkWorker())
        e = self.assertRaises(
            AssertionError, job.verifyBuildRequest, BufferLogger()
        )
        self.assertIn("invalid pocket due to the series status of", str(e))

    def test_getByID(self):
        job = self.makeJob()
        transaction.commit()
        self.assertEqual(
            job.build, SourcePackageRecipeBuild.getByID(job.build.id)
        )


class TestAsyncRecipeBuilder(TestRecipeBuilderBase):
    run_tests_with = AsynchronousDeferredRunTest.make_factory(timeout=30)

    def _setBuilderConfig(self):
        """Setup a temporary builder config."""
        self.pushConfig(
            "builddmaster",
            bzr_builder_sources_list="deb http://foo %(series)s main",
        )

    @defer.inlineCallbacks
    def test_extraBuildArgs(self):
        # extraBuildArgs will return a sane set of additional arguments.
        self._setBuilderConfig()
        job = self.makeJob(with_builder=True)
        distroarchseries = job.build.distroseries.architectures[0]
        (
            expected_archives,
            expected_trusted_keys,
        ) = yield get_sources_list_for_building(job, distroarchseries, None)
        expected_archives.insert(
            0, "deb http://foo %s main" % job.build.distroseries.name
        )
        args = yield job.extraBuildArgs()
        self.assertEqual(
            {
                "arch_tag": "i386",
                "archive_private": False,
                "archive_purpose": "PPA",
                "archives": expected_archives,
                "author_email": "requester@ubuntu.com",
                "author_name": "Joe User",
                "build_url": canonical_url(job.build),
                "builder_constraints": [],
                "fast_cleanup": True,
                "launchpad_instance": "devel",
                "launchpad_server_url": "launchpad.test",
                "ogrecomponent": "universe",
                "recipe_text": "# bzr-builder format 0.3 "
                "deb-version {debupstream}-0~{revno}\n"
                "lp://dev/~joe/someapp/pkg\n",
                "series": job.build.distroseries.name,
                "suite": "mydistro",
                "trusted_keys": expected_trusted_keys,
            },
            args,
        )

    @defer.inlineCallbacks
    def test_extraBuildArgs_private_archive(self):
        # If the build archive is private, the archive_private flag is
        # True. This tells launchpad-buildd to redact credentials from
        # build logs.
        self._setBuilderConfig()
        archive = self.factory.makeArchive(private=True)
        job = self.makeJob(archive=archive, with_builder=True)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(True, extra_args["archive_private"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_team_owner_no_email(self):
        # If the owner of the recipe is a team without a preferred email, the
        # registrant is used.
        self._setBuilderConfig()
        recipe_registrant = self.factory.makePerson(
            name="eric",
            displayname="Eric the Viking",
            email="eric@vikings.r.us",
        )
        recipe_owner = self.factory.makeTeam(
            name="vikings", members=[recipe_registrant]
        )

        job = self.makeJob(recipe_registrant, recipe_owner, with_builder=True)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(
            "Launchpad Package Builder", extra_args["author_name"]
        )
        self.assertEqual("noreply@launchpad.net", extra_args["author_email"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_team_owner_with_email(self):
        # If the owner of the recipe is a team that has an email set, we use
        # that.
        self._setBuilderConfig()
        recipe_registrant = self.factory.makePerson()
        recipe_owner = self.factory.makeTeam(
            name="vikings",
            email="everyone@vikings.r.us",
            members=[recipe_registrant],
        )

        job = self.makeJob(recipe_registrant, recipe_owner, with_builder=True)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual("Vikings", extra_args["author_name"])
        self.assertEqual("everyone@vikings.r.us", extra_args["author_email"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_owner_deactivated(self):
        # If the owner is deactivated, they have no preferred email.
        self._setBuilderConfig()
        owner = self.factory.makePerson()
        with person_logged_in(owner):
            owner.deactivate(comment="deactivating")
        job = self.makeJob(owner, with_builder=True)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(
            "Launchpad Package Builder", extra_args["author_name"]
        )
        self.assertEqual("noreply@launchpad.net", extra_args["author_email"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_withBadConfigForBzrBuilderPPA(self):
        # Ensure extraBuildArgs doesn't blow up with a badly formatted
        # bzr_builder_sources_list in the config.
        self.pushConfig(
            "builddmaster",
            bzr_builder_sources_list="deb http://foo %(series) main",
        )
        # (note the missing 's' in %(series)
        job = self.makeJob(with_builder=True)
        distroarchseries = job.build.distroseries.architectures[0]
        (
            expected_archives,
            expected_trusted_keys,
        ) = yield get_sources_list_for_building(job, distroarchseries, None)
        logger = BufferLogger()
        extra_args = yield job.extraBuildArgs(logger)
        self.assertEqual(
            {
                "arch_tag": "i386",
                "archive_private": False,
                "archive_purpose": "PPA",
                "archives": expected_archives,
                "author_email": "requester@ubuntu.com",
                "author_name": "Joe User",
                "build_url": canonical_url(job.build),
                "builder_constraints": [],
                "fast_cleanup": True,
                "launchpad_instance": "devel",
                "launchpad_server_url": "launchpad.test",
                "ogrecomponent": "universe",
                "recipe_text": "# bzr-builder format 0.3 "
                "deb-version {debupstream}-0~{revno}\n"
                "lp://dev/~joe/someapp/pkg\n",
                "series": job.build.distroseries.name,
                "suite": "mydistro",
                "trusted_keys": expected_trusted_keys,
            },
            extra_args,
        )
        self.assertIn(
            "Exception processing build tools sources.list entry:",
            logger.getLogBuffer(),
        )

    @defer.inlineCallbacks
    def test_extraBuildArgs_withNoBzrBuilderConfigSet(self):
        # Ensure extraBuildArgs doesn't blow up when
        # bzr_builder_sources_list isn't set.
        job = self.makeJob(with_builder=True)
        distroarchseries = job.build.distroseries.architectures[0]
        args = yield job.extraBuildArgs()
        (
            expected_archives,
            expected_trusted_keys,
        ) = yield get_sources_list_for_building(job, distroarchseries, None)
        self.assertEqual(args["archives"], expected_archives)
        self.assertEqual(args["trusted_keys"], expected_trusted_keys)

    @defer.inlineCallbacks
    def test_extraBuildArgs_git(self):
        job = self.makeJob(git=True, with_builder=True)
        distroarchseries = job.build.distroseries.architectures[0]
        (
            expected_archives,
            expected_trusted_keys,
        ) = yield get_sources_list_for_building(job, distroarchseries, None)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(
            {
                "arch_tag": "i386",
                "archive_private": False,
                "archive_purpose": "PPA",
                "archives": expected_archives,
                "author_email": "requester@ubuntu.com",
                "author_name": "Joe User",
                "build_url": canonical_url(job.build),
                "builder_constraints": [],
                "fast_cleanup": True,
                "git": True,
                "launchpad_instance": "devel",
                "launchpad_server_url": "launchpad.test",
                "ogrecomponent": "universe",
                "recipe_text": "# git-build-recipe format 0.4 deb-version "
                "{debupstream}-0~{revtime}\n"
                "lp:~joe/someapp/+git/pkg packaging\n",
                "series": job.build.distroseries.name,
                "suite": "mydistro",
                "trusted_keys": expected_trusted_keys,
            },
            extra_args,
        )

    @defer.inlineCallbacks
    def test_extraBuildArgs_archives(self):
        # The build uses the release pocket in its target PPA, and the
        # release, security, and updates pockets in the primary archive.
        archive = self.factory.makeArchive()
        job = self.makeJob(archive=archive, with_builder=True)
        self.factory.makeBinaryPackagePublishingHistory(
            archive=archive,
            distroarchseries=job.build.distroseries.architectures[0],
            pocket=PackagePublishingPocket.RELEASE,
            status=PackagePublishingStatus.PUBLISHED,
        )
        primary = job.build.distribution.main_archive
        expected_archives = [
            "deb %s %s main"
            % (archive.archive_url, job.build.distroseries.name),
            "deb %s %s main universe"
            % (primary.archive_url, job.build.distroseries.name),
            "deb %s %s-security main universe"
            % (primary.archive_url, job.build.distroseries.name),
            "deb %s %s-updates main universe"
            % (primary.archive_url, job.build.distroseries.name),
        ]
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(expected_archives, extra_args["archives"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_archive_trusted_keys(self):
        # If the archive has a signing key, extraBuildArgs sends it.
        yield self.useFixture(InProcessKeyServerFixture()).start()
        archive = self.factory.makeArchive()
        key_path = os.path.join(gpgkeysdir, "ppa-sample@canonical.com.sec")
        yield IArchiveGPGSigningKey(archive).setSigningKey(
            key_path, async_keyserver=True
        )
        job = self.makeJob(archive=archive, with_builder=True)
        distroarchseries = job.build.distroseries.architectures[0]
        self.factory.makeBinaryPackagePublishingHistory(
            distroarchseries=distroarchseries,
            pocket=job.build.pocket,
            archive=archive,
            status=PackagePublishingStatus.PUBLISHED,
        )
        args = yield job.extraBuildArgs()
        self.assertThat(
            args["trusted_keys"],
            MatchesListwise(
                [
                    Base64KeyMatches(
                        "0D57E99656BEFB0897606EE9A022DD1F5001B46D"
                    ),
                ]
            ),
        )

    @defer.inlineCallbacks
    def test_composeBuildRequest(self):
        job = self.makeJob(with_builder=True)
        test_publisher = SoyuzTestPublisher()
        test_publisher.addFakeChroots(job.build.distroseries, db_only=True)
        das = job.build.distroseries.nominatedarchindep
        build_request = yield job.composeBuildRequest(None)
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(
            ("sourcepackagerecipe", das, job.build.pocket, {}, extra_args),
            build_request,
        )


class TestBuildNotifications(TestCaseWithFactory):
    layer = LaunchpadZopelessLayer
    run_tests_with = AsynchronousDeferredRunTest.make_factory(timeout=30)

    def prepareBehaviour(self, fake_successful_upload=False):
        self.queue_record = (
            self.factory.makeSourcePackageRecipeBuild().queueBuild()
        )
        build = self.queue_record.specific_build
        if fake_successful_upload:
            removeSecurityProxy(build).verifySuccessfulUpload = FakeMethod(
                result=True
            )
            # We overwrite the buildmaster root to use a temp directory.
            tempdir = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, tempdir)
            self.upload_root = tempdir
            tmp_builddmaster_root = (
                """
            [builddmaster]
            root: %s
            """
                % self.upload_root
            )
            config.push("tmp_builddmaster_root", tmp_builddmaster_root)
            self.addCleanup(config.pop, "tmp_builddmaster_root")
        self.queue_record.builder = self.factory.makeBuilder()
        worker = WaitingWorker("BuildStatus.OK")
        return BuilderInteractor.getBuildBehaviour(
            self.queue_record, self.queue_record.builder, worker
        )

    def assertDeferredNotifyCount(self, status, behaviour, expected_count):
        d = behaviour.handleStatus(
            self.queue_record,
            {
                "builder_status": "BuilderStatus.WAITING",
                "build_status": "BuildStatus.%s" % status,
                "filemap": {},
            },
        )

        def cb(result):
            self.assertEqual(expected_count, len(pop_notifications()))

        d.addCallback(cb)
        return d

    def test_handleStatus_PACKAGEFAIL(self):
        """Failing to build the package immediately sends a notification."""
        return self.assertDeferredNotifyCount(
            "PACKAGEFAIL", self.prepareBehaviour(), 1
        )

    def test_handleStatus_OK(self):
        """Building the source package does _not_ immediately send mail.

        (The archive uploader mail send one later.
        """
        return self.assertDeferredNotifyCount("OK", self.prepareBehaviour(), 0)

    def test_handleStatus_OK_successful_upload(self):
        return self.assertDeferredNotifyCount(
            "OK", self.prepareBehaviour(True), 0
        )


class MakeSPRecipeBuildMixin:
    """Provide the common makeBuild method returning a queued build."""

    def makeBuild(self):
        build = self.factory.makeSourcePackageRecipeBuild(
            status=BuildStatus.BUILDING
        )
        build.queueBuild()
        return build

    def makeUnmodifiableBuild(self):
        archive = self.factory.makeArchive(purpose=ArchivePurpose.PRIMARY)
        build = self.factory.makeSourcePackageRecipeBuild(
            archive=archive, status=BuildStatus.BUILDING
        )
        build.distro_series.status = SeriesStatus.CURRENT
        build.queueBuild()
        return build


class TestGetUploadMethodsForSPRecipeBuild(
    MakeSPRecipeBuildMixin, TestGetUploadMethodsMixin, TestCaseWithFactory
):
    """IPackageBuild.getUpload-related methods work with SPRecipe builds."""


class TestVerifySuccessfulBuildForSPRBuild(
    MakeSPRecipeBuildMixin, TestVerifySuccessfulBuildMixin, TestCaseWithFactory
):
    """IBuildFarmJobBehaviour.verifySuccessfulBuild works."""


class TestHandleStatusForSPRBuild(
    MakeSPRecipeBuildMixin, TestHandleStatusMixin, TestCaseWithFactory
):
    """IPackageBuild.handleStatus works with SPRecipe builds."""
