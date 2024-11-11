# Copyright 2014-2020 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test live filesystem build behaviour."""

import os.path
from datetime import datetime, timezone

from testtools.matchers import MatchesListwise
from testtools.twistedsupport import AsynchronousDeferredRunTest
from twisted.internet import defer
from zope.component import getUtility
from zope.security.proxy import Proxy

from lp.archivepublisher.interfaces.archivegpgsigningkey import (
    IArchiveGPGSigningKey,
)
from lp.buildmaster.enums import BuildBaseImageType, BuildStatus
from lp.buildmaster.interfaces.builder import CannotBuild
from lp.buildmaster.interfaces.buildfarmjobbehaviour import (
    IBuildFarmJobBehaviour,
)
from lp.buildmaster.interfaces.processor import IProcessorSet
from lp.buildmaster.tests.mock_workers import MockBuilder, OkWorker
from lp.buildmaster.tests.test_buildfarmjobbehaviour import (
    TestGetUploadMethodsMixin,
    TestHandleStatusMixin,
    TestVerifySuccessfulBuildMixin,
)
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.registry.interfaces.series import SeriesStatus
from lp.services.features.testing import FeatureFixture
from lp.services.log.logger import BufferLogger, DevNullLogger
from lp.services.webapp import canonical_url
from lp.soyuz.adapters.archivedependencies import get_sources_list_for_building
from lp.soyuz.enums import PackagePublishingStatus
from lp.soyuz.interfaces.archive import ArchiveDisabled
from lp.soyuz.interfaces.livefs import (
    LIVEFS_FEATURE_FLAG,
    LiveFSBuildArchiveOwnerMismatch,
)
from lp.soyuz.model.livefsbuildbehaviour import LiveFSBuildBehaviour
from lp.soyuz.tests.soyuz import Base64KeyMatches
from lp.testing import TestCaseWithFactory
from lp.testing.gpgkeys import gpgkeysdir
from lp.testing.keyserver import InProcessKeyServerFixture
from lp.testing.layers import ZopelessDatabaseLayer


class TestLiveFSBuildBehaviourBase(TestCaseWithFactory):
    layer = ZopelessDatabaseLayer

    def setUp(self):
        super().setUp()
        self.useFixture(FeatureFixture({LIVEFS_FEATURE_FLAG: "on"}))

    def makeJob(
        self,
        archive=None,
        pocket=PackagePublishingPocket.RELEASE,
        with_builder=False,
        **kwargs,
    ):
        """Create a sample `ILiveFSBuildBehaviour`."""
        if archive is None:
            distribution = self.factory.makeDistribution(name="distro")
        else:
            distribution = archive.distribution
        distroseries = self.factory.makeDistroSeries(
            distribution=distribution, name="unstable"
        )
        processor = getUtility(IProcessorSet).getByName("386")
        distroarchseries = self.factory.makeDistroArchSeries(
            distroseries=distroseries,
            architecturetag="i386",
            processor=processor,
        )
        build = self.factory.makeLiveFSBuild(
            archive=archive,
            distroarchseries=distroarchseries,
            pocket=pocket,
            name="test-livefs",
            **kwargs,
        )
        job = IBuildFarmJobBehaviour(build)
        if with_builder:
            builder = MockBuilder()
            builder.processor = processor
            job.setBuilder(builder, None)
        return job


class TestLiveFSBuildBehaviour(TestLiveFSBuildBehaviourBase):
    def test_provides_interface(self):
        # LiveFSBuildBehaviour provides IBuildFarmJobBehaviour.
        job = LiveFSBuildBehaviour(None)
        self.assertProvides(job, IBuildFarmJobBehaviour)

    def test_adapts_ILiveFSBuild(self):
        # IBuildFarmJobBehaviour adapts an ILiveFSBuild.
        build = self.factory.makeLiveFSBuild()
        job = IBuildFarmJobBehaviour(build)
        self.assertProvides(job, IBuildFarmJobBehaviour)

    def test_verifyBuildRequest_valid(self):
        # verifyBuildRequest doesn't raise any exceptions when called with a
        # valid builder set.
        job = self.makeJob()
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        builder = MockBuilder()
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        job.verifyBuildRequest(logger)
        self.assertEqual("", logger.getLogBuffer())

    def test_verifyBuildRequest_virtual_mismatch(self):
        # verifyBuildRequest raises on an attempt to build a virtualized
        # build on a non-virtual builder.
        job = self.makeJob()
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        builder = MockBuilder(virtualized=False)
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        e = self.assertRaises(AssertionError, job.verifyBuildRequest, logger)
        self.assertEqual(
            "Attempt to build virtual item on a non-virtual builder.", str(e)
        )

    def test_verifyBuildRequest_archive_disabled(self):
        archive = self.factory.makeArchive(
            enabled=False, displayname="Disabled Archive"
        )
        job = self.makeJob(archive=archive)
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        builder = MockBuilder()
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        e = self.assertRaises(ArchiveDisabled, job.verifyBuildRequest, logger)
        self.assertEqual("Disabled Archive is disabled.", str(e))

    def test_verifyBuildRequest_archive_private_owners_match(self):
        archive = self.factory.makeArchive(private=True)
        job = self.makeJob(
            archive=archive, registrant=archive.owner, owner=archive.owner
        )
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        builder = MockBuilder()
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        job.verifyBuildRequest(logger)
        self.assertEqual("", logger.getLogBuffer())

    def test_verifyBuildRequest_archive_private_owners_mismatch(self):
        archive = self.factory.makeArchive(private=True)
        job = self.makeJob(archive=archive)
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        builder = MockBuilder()
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        e = self.assertRaises(
            LiveFSBuildArchiveOwnerMismatch, job.verifyBuildRequest, logger
        )
        self.assertEqual(
            "Live filesystem builds against private archives are only allowed "
            "if the live filesystem owner and the archive owner are equal.",
            str(e),
        )

    def test_verifyBuildRequest_no_chroot(self):
        # verifyBuildRequest raises when the DAS has no chroot.
        job = self.makeJob()
        builder = MockBuilder()
        job.setBuilder(builder, OkWorker())
        logger = BufferLogger()
        e = self.assertRaises(CannotBuild, job.verifyBuildRequest, logger)
        self.assertIn("Missing chroot", str(e))


class TestAsyncLiveFSBuildBehaviour(TestLiveFSBuildBehaviourBase):
    run_tests_with = AsynchronousDeferredRunTest.make_factory(timeout=30)

    @defer.inlineCallbacks
    def test_extraBuildArgs(self):
        # extraBuildArgs returns a reasonable set of additional arguments.
        job = self.makeJob(
            date_created=datetime(2014, 4, 25, 10, 38, 0, tzinfo=timezone.utc),
            metadata={"project": "distro", "subproject": "special"},
            with_builder=True,
        )
        (
            expected_archives,
            expected_trusted_keys,
        ) = yield get_sources_list_for_building(
            job, job.build.distro_arch_series, None
        )
        extra_args = yield job.extraBuildArgs()
        self.assertEqual(
            {
                "archive_private": False,
                "archives": expected_archives,
                "arch_tag": "i386",
                "build_url": canonical_url(job.build),
                "builder_constraints": [],
                "datestamp": "20140425-103800",
                "fast_cleanup": True,
                "launchpad_instance": "devel",
                "launchpad_server_url": "launchpad.test",
                "pocket": "release",
                "project": "distro",
                "subproject": "special",
                "series": "unstable",
                "trusted_keys": expected_trusted_keys,
            },
            extra_args,
        )

    @defer.inlineCallbacks
    def test_extraBuildArgs_proposed(self):
        # extraBuildArgs returns appropriate arguments if asked to build a
        # job for -proposed.
        job = self.makeJob(
            pocket=PackagePublishingPocket.PROPOSED,
            metadata={"project": "distro"},
            with_builder=True,
        )
        args = yield job.extraBuildArgs()
        self.assertEqual("unstable", args["series"])
        self.assertEqual("proposed", args["pocket"])

    @defer.inlineCallbacks
    def test_extraBuildArgs_no_security_proxy(self):
        # extraBuildArgs returns an object without security wrapping, even
        # if values in the metadata are (say) lists and hence get proxied by
        # Zope.
        job = self.makeJob(
            metadata={"lb_args": ["--option=value"]}, with_builder=True
        )
        args = yield job.extraBuildArgs()
        self.assertEqual(["--option=value"], args["lb_args"])
        self.assertIsNot(Proxy, type(args["lb_args"]))

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
        self.factory.makeBinaryPackagePublishingHistory(
            distroarchseries=job.build.distro_arch_series,
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
    def test_extraBuildArgs_metadata_cannot_override_base(self):
        # Items in the user-provided metadata cannot override the base
        # arguments.
        job = self.makeJob(
            metadata={"project": "distro", "arch_tag": "nonsense"},
            with_builder=True,
        )
        args = yield job.extraBuildArgs()
        self.assertEqual("distro", args["project"])
        self.assertEqual("i386", args["arch_tag"])

    @defer.inlineCallbacks
    def test_composeBuildRequest(self):
        job = self.makeJob(with_builder=True)
        lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(lfa)
        build_request = yield job.composeBuildRequest(None)
        args = yield job.extraBuildArgs()
        self.assertEqual(
            (
                "livefs",
                job.build.distro_arch_series,
                job.build.pocket,
                {},
                args,
            ),
            build_request,
        )

    @defer.inlineCallbacks
    def test_dispatchBuildToWorker_prefers_lxd(self):
        job = self.makeJob()
        builder = MockBuilder()
        builder.processor = job.build.processor
        worker = OkWorker()
        job.setBuilder(builder, worker)
        chroot_lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(
            chroot_lfa, image_type=BuildBaseImageType.CHROOT
        )
        lxd_lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(
            lxd_lfa, image_type=BuildBaseImageType.LXD
        )
        yield job.dispatchBuildToWorker(DevNullLogger())
        self.assertEqual(
            ("ensurepresent", lxd_lfa.http_url, "", ""), worker.call_log[0]
        )

    @defer.inlineCallbacks
    def test_dispatchBuildToWorker_falls_back_to_chroot(self):
        job = self.makeJob()
        builder = MockBuilder()
        builder.processor = job.build.processor
        worker = OkWorker()
        job.setBuilder(builder, worker)
        chroot_lfa = self.factory.makeLibraryFileAlias(db_only=True)
        job.build.distro_arch_series.addOrUpdateChroot(
            chroot_lfa, image_type=BuildBaseImageType.CHROOT
        )
        yield job.dispatchBuildToWorker(DevNullLogger())
        self.assertEqual(
            ("ensurepresent", chroot_lfa.http_url, "", ""), worker.call_log[0]
        )


class MakeLiveFSBuildMixin:
    """Provide the common makeBuild method returning a queued build."""

    def makeBuild(self):
        self.useFixture(FeatureFixture({LIVEFS_FEATURE_FLAG: "on"}))
        build = self.factory.makeLiveFSBuild(status=BuildStatus.BUILDING)
        build.queueBuild()
        return build

    def makeUnmodifiableBuild(self):
        self.useFixture(FeatureFixture({LIVEFS_FEATURE_FLAG: "on"}))
        build = self.factory.makeLiveFSBuild(status=BuildStatus.BUILDING)
        build.distro_series.status = SeriesStatus.OBSOLETE
        build.queueBuild()
        return build


class TestGetUploadMethodsForLiveFSBuild(
    MakeLiveFSBuildMixin, TestGetUploadMethodsMixin, TestCaseWithFactory
):
    """IPackageBuild.getUpload-related methods work with LiveFS builds."""


class TestVerifySuccessfulBuildForLiveFSBuild(
    MakeLiveFSBuildMixin, TestVerifySuccessfulBuildMixin, TestCaseWithFactory
):
    """IBuildFarmJobBehaviour.verifySuccessfulBuild works."""


class TestHandleStatusForLiveFSBuild(
    MakeLiveFSBuildMixin, TestHandleStatusMixin, TestCaseWithFactory
):
    """IPackageBuild.handleStatus works with LiveFS builds."""
