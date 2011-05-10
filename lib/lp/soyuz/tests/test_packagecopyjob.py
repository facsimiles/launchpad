# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for sync package jobs."""

from testtools.content import text_content
import transaction
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from canonical.testing import LaunchpadZopelessLayer
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.soyuz.interfaces.archive import CannotCopy
from lp.soyuz.interfaces.packagecopyjob import (
    IPackageCopyJob,
    IPlainPackageCopyJobSource,
    )
from lp.soyuz.interfaces.publishing import PackagePublishingStatus
from lp.soyuz.tests.test_publishing import SoyuzTestPublisher
from lp.testing import (
    run_script,
    TestCaseWithFactory,
    )


class PlainPackageCopyJobTests(TestCaseWithFactory):
    """Test case for PlainPackageCopyJob."""

    layer = LaunchpadZopelessLayer

    def test_create(self):
        # A PackageCopyJob can be created and stores its arguments.
        distroseries = self.factory.makeDistroSeries()
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[("foo", "1.0-1"), ("bar", "2.4")],
            source_archive=archive1, target_archive=archive2,
            target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        self.assertProvides(job, IPackageCopyJob)
        self.assertEquals(archive1.id, job.source_archive_id)
        self.assertEquals(archive1, job.source_archive)
        self.assertEquals(archive2.id, job.target_archive_id)
        self.assertEquals(archive2, job.target_archive)
        self.assertEquals(distroseries, job.target_distroseries)
        self.assertEquals(PackagePublishingPocket.RELEASE, job.target_pocket)
        self.assertContentEqual(
            job.source_packages,
            [("foo", "1.0-1", None), ("bar", "2.4", None)])
        self.assertEquals(False, job.include_binaries)

    def test_getActiveJobs(self):
        # getActiveJobs() can retrieve all active jobs for an archive.
        distroseries = self.factory.makeDistroSeries()
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[("foo", "1.0-1")], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        self.assertContentEqual([job], source.getActiveJobs(archive2))

    def test_run_unknown_package(self):
        # A job properly records failure.
        distroseries = self.factory.makeDistroSeries()
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[("foo", "1.0-1")], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        self.assertRaises(CannotCopy, job.run)

    def test_target_ppa_non_release_pocket(self):
        # When copying to a PPA archive the target must be the release pocket.
        distroseries = self.factory.makeDistroSeries()
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.UPDATES,
            include_binaries=False)
        self.assertRaises(CannotCopy, job.run)

    def test_run(self):
        # A proper test run synchronizes packages.
        publisher = SoyuzTestPublisher()
        publisher.prepareBreezyAutotest()
        distroseries = publisher.breezy_autotest

        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)

        source_package = publisher.getPubSource(
            distroseries=distroseries, sourcename="libc",
            version="2.8-1", status=PackagePublishingStatus.PUBLISHED,
            archive=archive1)

        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[("libc", "2.8-1")], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        self.assertContentEqual(
            job.source_packages, [("libc", "2.8-1", source_package)])

        # Make sure everything hits the database, switching db users
        # aborts.
        transaction.commit()
        # XXX: GavinPanella 2011-04-20 bug=770297: The sync_packages database
        # user should be renamed to copy_packages.
        self.layer.switchDbUser('sync_packages')
        job.run()

        published_sources = archive2.getPublishedSources()
        spr = published_sources.one().sourcepackagerelease
        self.assertEquals("libc", spr.name)
        self.assertEquals("2.8-1", spr.version)

    def test_getOopsVars(self):
        distroseries = self.factory.makeDistroSeries()
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        source = getUtility(IPlainPackageCopyJobSource)
        job = source.create(
            source_packages=[("foo", "1.0-1")], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        oops_vars = job.getOopsVars()
        naked_job = removeSecurityProxy(job)
        self.assertIn(
            ('source_archive_id', archive1.id), oops_vars)
        self.assertIn(
            ('target_archive_id', archive2.id), oops_vars)
        self.assertIn(
            ('target_distroseries_id', distroseries.id), oops_vars)
        self.assertIn(
            ('package_copy_job_id', naked_job.context.id), oops_vars)
        self.assertIn(
            ('package_copy_job_type', naked_job.context.job_type.title),
            oops_vars)

    def test_smoke(self):
        publisher = SoyuzTestPublisher()
        publisher.prepareBreezyAutotest()
        distroseries = publisher.breezy_autotest
        archive1 = self.factory.makeArchive(distroseries.distribution)
        archive2 = self.factory.makeArchive(distroseries.distribution)
        publisher.getPubSource(
            distroseries=distroseries, sourcename="libc",
            version="2.8-1", status=PackagePublishingStatus.PUBLISHED,
            archive=archive1)
        getUtility(IPlainPackageCopyJobSource).create(
            source_packages=[("libc", "2.8-1")], source_archive=archive1,
            target_archive=archive2, target_distroseries=distroseries,
            target_pocket=PackagePublishingPocket.RELEASE,
            include_binaries=False)
        transaction.commit()

        out, err, exit_code = run_script(
            "LP_DEBUG_SQL=1 cronscripts/process-job-source.py -vv %s" % (
                IPlainPackageCopyJobSource.getName()))

        self.addDetail("stdout", text_content(out))
        self.addDetail("stderr", text_content(err))

        self.assertEqual(0, exit_code)
        copied_source_package = archive2.getPublishedSources(
            name="libc", version="2.8-1", exact_match=True).first()
        self.assertIsNot(copied_source_package, None)
