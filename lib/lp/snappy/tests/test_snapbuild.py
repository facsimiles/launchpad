# Copyright 2015-2018 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test snap package build features."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type

from datetime import (
    datetime,
    timedelta,
    )
from urllib2 import (
    HTTPError,
    urlopen,
    )

from pymacaroons import Macaroon
import pytz
from testtools.matchers import (
    Equals,
    MatchesDict,
    MatchesStructure,
    )
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.app.errors import NotFoundError
from lp.app.interfaces.launchpad import ILaunchpadCelebrities
from lp.buildmaster.enums import BuildStatus
from lp.buildmaster.interfaces.buildqueue import IBuildQueue
from lp.buildmaster.interfaces.packagebuild import IPackageBuild
from lp.buildmaster.interfaces.processor import IProcessorSet
from lp.registry.enums import PersonVisibility
from lp.services.config import config
from lp.services.features.testing import FeatureFixture
from lp.services.job.interfaces.job import JobStatus
from lp.services.librarian.browser import ProxiedLibraryFileAlias
from lp.services.propertycache import clear_property_cache
from lp.services.webapp.interfaces import OAuthPermission
from lp.services.webapp.publisher import canonical_url
from lp.snappy.interfaces.snap import SNAP_TESTING_FLAGS
from lp.snappy.interfaces.snapbuild import (
    CannotScheduleStoreUpload,
    ISnapBuild,
    ISnapBuildSet,
    SnapBuildStoreUploadStatus,
    )
from lp.snappy.interfaces.snapbuildjob import ISnapStoreUploadJobSource
from lp.soyuz.enums import ArchivePurpose
from lp.testing import (
    ANONYMOUS,
    api_url,
    login,
    logout,
    person_logged_in,
    StormStatementRecorder,
    TestCaseWithFactory,
    )
from lp.testing.dbuser import dbuser
from lp.testing.layers import (
    LaunchpadFunctionalLayer,
    LaunchpadZopelessLayer,
    )
from lp.testing.mail_helpers import pop_notifications
from lp.testing.matchers import HasQueryCount
from lp.testing.pages import webservice_for_person


expected_body = """\
 * Snap Package: snap-1
 * Archive: distro
 * Distroseries: distro unstable
 * Architecture: i386
 * Pocket: UPDATES
 * State: Failed to build
 * Duration: 10 minutes
 * Build Log: %s
 * Upload Log: %s
 * Builder: http://launchpad.dev/builders/bob
"""


class TestSnapBuild(TestCaseWithFactory):

    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestSnapBuild, self).setUp()
        self.useFixture(FeatureFixture(SNAP_TESTING_FLAGS))
        self.pushConfig(
            "snappy", store_url="http://sca.example/",
            store_upload_url="http://updown.example/")
        self.build = self.factory.makeSnapBuild()

    def test_implements_interfaces(self):
        # SnapBuild implements IPackageBuild and ISnapBuild.
        self.assertProvides(self.build, IPackageBuild)
        self.assertProvides(self.build, ISnapBuild)

    def test_queueBuild(self):
        # SnapBuild can create the queue entry for itself.
        bq = self.build.queueBuild()
        self.assertProvides(bq, IBuildQueue)
        self.assertEqual(
            self.build.build_farm_job, removeSecurityProxy(bq)._build_farm_job)
        self.assertEqual(self.build, bq.specific_build)
        self.assertEqual(self.build.virtualized, bq.virtualized)
        self.assertIsNotNone(bq.processor)
        self.assertEqual(bq, self.build.buildqueue_record)

    def test_current_component_primary(self):
        # SnapBuilds for primary archives always build in multiverse for the
        # time being.
        self.assertEqual(ArchivePurpose.PRIMARY, self.build.archive.purpose)
        self.assertEqual("multiverse", self.build.current_component.name)

    def test_current_component_ppa(self):
        # PPAs only have indices for main, so SnapBuilds for PPAs always
        # build in main.
        build = self.factory.makeSnapBuild(archive=self.factory.makeArchive())
        self.assertEqual("main", build.current_component.name)

    def test_is_private(self):
        # A SnapBuild is private iff its Snap and archive are.
        self.assertFalse(self.build.is_private)
        private_team = self.factory.makeTeam(
            visibility=PersonVisibility.PRIVATE)
        with person_logged_in(private_team.teamowner):
            build = self.factory.makeSnapBuild(
                requester=private_team.teamowner, owner=private_team,
                private=True)
            self.assertTrue(build.is_private)
        private_archive = self.factory.makeArchive(private=True)
        with person_logged_in(private_archive.owner):
            build = self.factory.makeSnapBuild(archive=private_archive)
            self.assertTrue(build.is_private)

    def test_can_be_cancelled(self):
        # For all states that can be cancelled, can_be_cancelled returns True.
        ok_cases = [
            BuildStatus.BUILDING,
            BuildStatus.NEEDSBUILD,
            ]
        for status in BuildStatus:
            if status in ok_cases:
                self.assertTrue(self.build.can_be_cancelled)
            else:
                self.assertFalse(self.build.can_be_cancelled)

    def test_cancel_not_in_progress(self):
        # The cancel() method for a pending build leaves it in the CANCELLED
        # state.
        self.build.queueBuild()
        self.build.cancel()
        self.assertEqual(BuildStatus.CANCELLED, self.build.status)
        self.assertIsNone(self.build.buildqueue_record)

    def test_cancel_in_progress(self):
        # The cancel() method for a building build leaves it in the
        # CANCELLING state.
        bq = self.build.queueBuild()
        bq.markAsBuilding(self.factory.makeBuilder())
        self.build.cancel()
        self.assertEqual(BuildStatus.CANCELLING, self.build.status)
        self.assertEqual(bq, self.build.buildqueue_record)

    def test_estimateDuration(self):
        # Without previous builds, the default time estimate is 30m.
        self.assertEqual(1800, self.build.estimateDuration().seconds)

    def test_estimateDuration_with_history(self):
        # Previous successful builds of the same snap package are used for
        # estimates.
        self.factory.makeSnapBuild(
            requester=self.build.requester, snap=self.build.snap,
            distroarchseries=self.build.distro_arch_series,
            status=BuildStatus.FULLYBUILT, duration=timedelta(seconds=335))
        for i in range(3):
            self.factory.makeSnapBuild(
                requester=self.build.requester, snap=self.build.snap,
                distroarchseries=self.build.distro_arch_series,
                status=BuildStatus.FAILEDTOBUILD,
                duration=timedelta(seconds=20))
        self.assertEqual(335, self.build.estimateDuration().seconds)

    def test_build_cookie(self):
        build = self.factory.makeSnapBuild()
        self.assertEqual('SNAPBUILD-%d' % build.id, build.build_cookie)

    def test_getFileByName_logs(self):
        # getFileByName returns the logs when requested by name.
        self.build.setLog(
            self.factory.makeLibraryFileAlias(filename="buildlog.txt.gz"))
        self.assertEqual(
            self.build.log, self.build.getFileByName("buildlog.txt.gz"))
        self.assertRaises(NotFoundError, self.build.getFileByName, "foo")
        self.build.storeUploadLog("uploaded")
        self.assertEqual(
            self.build.upload_log,
            self.build.getFileByName(self.build.upload_log.filename))

    def test_getFileByName_uploaded_files(self):
        # getFileByName returns uploaded files when requested by name.
        filenames = ("ubuntu.squashfs", "ubuntu.manifest")
        lfas = []
        for filename in filenames:
            lfa = self.factory.makeLibraryFileAlias(filename=filename)
            lfas.append(lfa)
            self.build.addFile(lfa)
        self.assertContentEqual(
            lfas, [row[1] for row in self.build.getFiles()])
        for filename, lfa in zip(filenames, lfas):
            self.assertEqual(lfa, self.build.getFileByName(filename))
        self.assertRaises(NotFoundError, self.build.getFileByName, "missing")

    def test_verifySuccessfulUpload(self):
        self.assertFalse(self.build.verifySuccessfulUpload())
        self.factory.makeSnapFile(snapbuild=self.build)
        self.assertTrue(self.build.verifySuccessfulUpload())

    def test_updateStatus_stores_revision_id(self):
        # If the builder reports a revision_id, updateStatus saves it.
        self.assertIsNone(self.build.revision_id)
        self.build.updateStatus(BuildStatus.BUILDING, slave_status={})
        self.assertIsNone(self.build.revision_id)
        self.build.updateStatus(
            BuildStatus.BUILDING, slave_status={"revision_id": "dummy"})
        self.assertEqual("dummy", self.build.revision_id)

    def test_updateStatus_triggers_webhooks(self):
        # Updating the status of a SnapBuild triggers webhooks on the
        # corresponding Snap.
        hook = self.factory.makeWebhook(
            target=self.build.snap, event_types=["snap:build:0.1"])
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        expected_payload = {
            "snap_build": Equals(
                canonical_url(self.build, force_local_path=True)),
            "action": Equals("status-changed"),
            "snap": Equals(
                canonical_url(self.build.snap, force_local_path=True)),
            "status": Equals("Successfully built"),
            "store_upload_status": Equals("Unscheduled"),
            }
        delivery = hook.deliveries.one()
        self.assertThat(
            delivery, MatchesStructure(
                event_type=Equals("snap:build:0.1"),
                payload=MatchesDict(expected_payload)))
        with dbuser(config.IWebhookDeliveryJobSource.dbuser):
            self.assertEqual(
                "<WebhookDeliveryJob for webhook %d on %r>" % (
                    hook.id, hook.target),
                repr(delivery))

    def test_updateStatus_no_change_does_not_trigger_webhooks(self):
        # An updateStatus call that changes details such as the revision_id
        # but that doesn't change the build's status attribute does not
        # trigger webhooks.
        hook = self.factory.makeWebhook(
            target=self.build.snap, event_types=["snap:build:0.1"])
        builder = self.factory.makeBuilder()
        self.build.updateStatus(BuildStatus.BUILDING)
        self.assertEqual(1, hook.deliveries.count())
        self.build.updateStatus(
            BuildStatus.BUILDING, builder=builder,
            slave_status={"revision_id": "1"})
        self.assertEqual(1, hook.deliveries.count())
        self.build.updateStatus(BuildStatus.UPLOADING)
        self.assertEqual(2, hook.deliveries.count())

    def test_updateStatus_failure_does_not_trigger_store_uploads(self):
        # A failed SnapBuild does not trigger store uploads.
        self.build.snap.store_series = self.factory.makeSnappySeries()
        self.build.snap.store_name = self.factory.getUniqueUnicode()
        self.build.snap.store_upload = True
        self.build.snap.store_secrets = {"root": Macaroon().serialize()}
        with dbuser(config.builddmaster.dbuser):
            self.build.updateStatus(BuildStatus.FAILEDTOBUILD)
        self.assertContentEqual([], self.build.store_upload_jobs)

    def test_updateStatus_fullybuilt_triggers_store_uploads(self):
        # A completed SnapBuild triggers store uploads.
        self.build.snap.store_series = self.factory.makeSnappySeries()
        self.build.snap.store_name = self.factory.getUniqueUnicode()
        self.build.snap.store_upload = True
        self.build.snap.store_secrets = {"root": Macaroon().serialize()}
        with dbuser(config.builddmaster.dbuser):
            self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.assertEqual(1, len(list(self.build.store_upload_jobs)))

    def test_notify_fullybuilt(self):
        # notify does not send mail when a SnapBuild completes normally.
        person = self.factory.makePerson(name="person")
        build = self.factory.makeSnapBuild(
            requester=person, status=BuildStatus.FULLYBUILT)
        build.notify()
        self.assertEqual(0, len(pop_notifications()))

    def test_notify_packagefail(self):
        # notify sends mail when a SnapBuild fails.
        person = self.factory.makePerson(name="person")
        distribution = self.factory.makeDistribution(name="distro")
        distroseries = self.factory.makeDistroSeries(
            distribution=distribution, name="unstable")
        processor = getUtility(IProcessorSet).getByName("386")
        distroarchseries = self.factory.makeDistroArchSeries(
            distroseries=distroseries, architecturetag="i386",
            processor=processor)
        build = self.factory.makeSnapBuild(
            name="snap-1", requester=person, owner=person,
            distroarchseries=distroarchseries,
            date_created=datetime(2014, 4, 25, 10, 38, 0, tzinfo=pytz.UTC),
            status=BuildStatus.FAILEDTOBUILD,
            builder=self.factory.makeBuilder(name="bob"),
            duration=timedelta(minutes=10))
        build.setLog(self.factory.makeLibraryFileAlias())
        build.notify()
        [notification] = pop_notifications()
        self.assertEqual(
            config.canonical.noreply_from_address, notification["From"])
        self.assertEqual(
            "Person <%s>" % person.preferredemail.email, notification["To"])
        subject = notification["Subject"].replace("\n ", " ")
        self.assertEqual(
            "[Snap build #%d] i386 build of snap-1 snap package in distro "
            "unstable-updates" % build.id, subject)
        self.assertEqual(
            "Requester", notification["X-Launchpad-Message-Rationale"])
        self.assertEqual(person.name, notification["X-Launchpad-Message-For"])
        self.assertEqual(
            "snap-build-status",
            notification["X-Launchpad-Notification-Type"])
        self.assertEqual(
            "FAILEDTOBUILD", notification["X-Launchpad-Build-State"])
        body, footer = notification.get_payload(decode=True).split("\n-- \n")
        self.assertEqual(expected_body % (build.log_url, ""), body)
        self.assertEqual(
            "http://launchpad.dev/~person/+snap/snap-1/+build/%d\n"
            "You are the requester of the build.\n" % build.id, footer)

    def addFakeBuildLog(self, build):
        build.setLog(self.factory.makeLibraryFileAlias("mybuildlog.txt"))

    def test_log_url(self):
        # The log URL for a snap package build will use the archive context.
        self.addFakeBuildLog(self.build)
        self.assertEqual(
            "http://launchpad.dev/~%s/+snap/%s/+build/%d/+files/"
            "mybuildlog.txt" % (
                self.build.snap.owner.name, self.build.snap.name,
                self.build.id),
            self.build.log_url)

    def test_eta(self):
        # SnapBuild.eta returns a non-None value when it should, or None
        # when there's no start time.
        self.build.queueBuild()
        self.assertIsNone(self.build.eta)
        self.factory.makeBuilder(processors=[self.build.processor])
        clear_property_cache(self.build)
        self.assertIsNotNone(self.build.eta)

    def test_eta_cached(self):
        # The expensive completion time estimate is cached.
        self.build.queueBuild()
        self.build.eta
        with StormStatementRecorder() as recorder:
            self.build.eta
        self.assertThat(recorder, HasQueryCount(Equals(0)))

    def test_estimate(self):
        # SnapBuild.estimate returns True until the job is completed.
        self.build.queueBuild()
        self.factory.makeBuilder(processors=[self.build.processor])
        self.build.updateStatus(BuildStatus.BUILDING)
        self.assertTrue(self.build.estimate)
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        clear_property_cache(self.build)
        self.assertFalse(self.build.estimate)

    def setUpStoreUpload(self):
        self.pushConfig(
            "snappy", store_url="http://sca.example/",
            store_upload_url="http://updown.example/")
        self.build.snap.store_series = self.factory.makeSnappySeries(
            usable_distro_series=[self.build.snap.distro_series])
        self.build.snap.store_name = self.factory.getUniqueUnicode()
        self.build.snap.store_secrets = {"root": Macaroon().serialize()}

    def test_store_upload_status_unscheduled(self):
        build = self.factory.makeSnapBuild(status=BuildStatus.FULLYBUILT)
        self.assertEqual(
            SnapBuildStoreUploadStatus.UNSCHEDULED, build.store_upload_status)

    def test_store_upload_status_pending(self):
        build = self.factory.makeSnapBuild(status=BuildStatus.FULLYBUILT)
        getUtility(ISnapStoreUploadJobSource).create(build)
        self.assertEqual(
            SnapBuildStoreUploadStatus.PENDING, build.store_upload_status)

    def test_store_upload_status_uploaded(self):
        build = self.factory.makeSnapBuild(status=BuildStatus.FULLYBUILT)
        job = getUtility(ISnapStoreUploadJobSource).create(build)
        naked_job = removeSecurityProxy(job)
        naked_job.job._status = JobStatus.COMPLETED
        self.assertEqual(
            SnapBuildStoreUploadStatus.UPLOADED, build.store_upload_status)

    def test_store_upload_status_failed_to_upload(self):
        build = self.factory.makeSnapBuild(status=BuildStatus.FULLYBUILT)
        job = getUtility(ISnapStoreUploadJobSource).create(build)
        naked_job = removeSecurityProxy(job)
        naked_job.job._status = JobStatus.FAILED
        self.assertEqual(
            SnapBuildStoreUploadStatus.FAILEDTOUPLOAD,
            build.store_upload_status)

    def test_store_upload_status_failed_to_release(self):
        build = self.factory.makeSnapBuild(status=BuildStatus.FULLYBUILT)
        job = getUtility(ISnapStoreUploadJobSource).create(build)
        naked_job = removeSecurityProxy(job)
        naked_job.job._status = JobStatus.FAILED
        naked_job.store_url = "http://sca.example/dev/click-apps/1/rev/1/"
        self.assertEqual(
            SnapBuildStoreUploadStatus.FAILEDTORELEASE,
            build.store_upload_status)

    def test_scheduleStoreUpload(self):
        # A build not previously uploaded to the store can be uploaded
        # manually.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.factory.makeSnapFile(
            snapbuild=self.build,
            libraryfile=self.factory.makeLibraryFileAlias(db_only=True))
        self.build.scheduleStoreUpload()
        [job] = getUtility(ISnapStoreUploadJobSource).iterReady()
        self.assertEqual(JobStatus.WAITING, job.job.status)
        self.assertEqual(self.build, job.snapbuild)

    def test_scheduleStoreUpload_not_configured(self):
        # A build that is not properly configured cannot be uploaded to the
        # store.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.build.snap.store_name = None
        self.assertRaisesWithContent(
            CannotScheduleStoreUpload,
            "Cannot upload this package to the store because it is not "
            "properly configured.",
            self.build.scheduleStoreUpload)
        self.assertEqual(
            [], list(getUtility(ISnapStoreUploadJobSource).iterReady()))

    def test_scheduleStoreUpload_no_files(self):
        # A build with no files cannot be uploaded to the store.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.assertRaisesWithContent(
            CannotScheduleStoreUpload,
            "Cannot upload this package because it has no files.",
            self.build.scheduleStoreUpload)
        self.assertEqual(
            [], list(getUtility(ISnapStoreUploadJobSource).iterReady()))

    def test_scheduleStoreUpload_already_in_progress(self):
        # A build with an upload already in progress will not have another
        # one created.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.factory.makeSnapFile(
            snapbuild=self.build,
            libraryfile=self.factory.makeLibraryFileAlias(db_only=True))
        old_job = getUtility(ISnapStoreUploadJobSource).create(self.build)
        self.assertRaisesWithContent(
            CannotScheduleStoreUpload,
            "An upload of this package is already in progress.",
            self.build.scheduleStoreUpload)
        self.assertEqual(
            [old_job], list(getUtility(ISnapStoreUploadJobSource).iterReady()))

    def test_scheduleStoreUpload_already_uploaded(self):
        # A build with an upload that has already completed will not have
        # another one created.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.factory.makeSnapFile(
            snapbuild=self.build,
            libraryfile=self.factory.makeLibraryFileAlias(db_only=True))
        old_job = getUtility(ISnapStoreUploadJobSource).create(self.build)
        removeSecurityProxy(old_job).job._status = JobStatus.COMPLETED
        self.assertRaisesWithContent(
            CannotScheduleStoreUpload,
            "Cannot upload this package because it has already been uploaded.",
            self.build.scheduleStoreUpload)
        self.assertEqual(
            [], list(getUtility(ISnapStoreUploadJobSource).iterReady()))

    def test_scheduleStoreUpload_triggers_webhooks(self):
        # Scheduling a store upload triggers webhooks on the corresponding
        # snap.
        self.setUpStoreUpload()
        self.build.updateStatus(BuildStatus.FULLYBUILT)
        self.factory.makeSnapFile(
            snapbuild=self.build,
            libraryfile=self.factory.makeLibraryFileAlias(db_only=True))
        hook = self.factory.makeWebhook(
            target=self.build.snap, event_types=["snap:build:0.1"])
        self.build.scheduleStoreUpload()
        expected_payload = {
            "snap_build": Equals(
                canonical_url(self.build, force_local_path=True)),
            "action": Equals("status-changed"),
            "snap": Equals(
                canonical_url(self.build.snap, force_local_path=True)),
            "status": Equals("Successfully built"),
            "store_upload_status": Equals("Pending"),
            }
        delivery = hook.deliveries.one()
        self.assertThat(
            delivery, MatchesStructure(
                event_type=Equals("snap:build:0.1"),
                payload=MatchesDict(expected_payload)))
        with dbuser(config.IWebhookDeliveryJobSource.dbuser):
            self.assertEqual(
                "<WebhookDeliveryJob for webhook %d on %r>" % (
                    hook.id, hook.target),
                repr(delivery))


class TestSnapBuildSet(TestCaseWithFactory):

    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestSnapBuildSet, self).setUp()
        self.useFixture(FeatureFixture(SNAP_TESTING_FLAGS))

    def test_getByBuildFarmJob_works(self):
        build = self.factory.makeSnapBuild()
        self.assertEqual(
            build,
            getUtility(ISnapBuildSet).getByBuildFarmJob(build.build_farm_job))

    def test_getByBuildFarmJob_returns_None_when_missing(self):
        bpb = self.factory.makeBinaryPackageBuild()
        self.assertIsNone(
            getUtility(ISnapBuildSet).getByBuildFarmJob(bpb.build_farm_job))

    def test_getByBuildFarmJobs_works(self):
        builds = [self.factory.makeSnapBuild() for i in range(10)]
        self.assertContentEqual(
            builds,
            getUtility(ISnapBuildSet).getByBuildFarmJobs(
                [build.build_farm_job for build in builds]))

    def test_getByBuildFarmJobs_works_empty(self):
        self.assertContentEqual(
            [], getUtility(ISnapBuildSet).getByBuildFarmJobs([]))


class TestSnapBuildWebservice(TestCaseWithFactory):

    layer = LaunchpadFunctionalLayer

    def setUp(self):
        super(TestSnapBuildWebservice, self).setUp()
        self.useFixture(FeatureFixture(SNAP_TESTING_FLAGS))
        self.person = self.factory.makePerson()
        self.webservice = webservice_for_person(
            self.person, permission=OAuthPermission.WRITE_PRIVATE)
        self.webservice.default_api_version = "devel"
        login(ANONYMOUS)

    def getURL(self, obj):
        return self.webservice.getAbsoluteUrl(api_url(obj))

    def test_properties(self):
        # The basic properties of a SnapBuild are sensible.
        db_build = self.factory.makeSnapBuild(
            requester=self.person,
            date_created=datetime(2014, 4, 25, 10, 38, 0, tzinfo=pytz.UTC))
        build_url = api_url(db_build)
        logout()
        build = self.webservice.get(build_url).jsonBody()
        with person_logged_in(self.person):
            self.assertEqual(self.getURL(self.person), build["requester_link"])
            self.assertEqual(self.getURL(db_build.snap), build["snap_link"])
            self.assertEqual(
                self.getURL(db_build.archive), build["archive_link"])
            self.assertEqual(
                self.getURL(db_build.distro_arch_series),
                build["distro_arch_series_link"])
            self.assertEqual(
                db_build.distro_arch_series.architecturetag, build["arch_tag"])
            self.assertEqual("Updates", build["pocket"])
            self.assertIsNone(build["channels"])
            self.assertIsNone(build["score"])
            self.assertFalse(build["can_be_rescored"])
            self.assertFalse(build["can_be_cancelled"])

    def test_public(self):
        # A SnapBuild with a public Snap and archive is itself public.
        db_build = self.factory.makeSnapBuild()
        build_url = api_url(db_build)
        unpriv_webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        unpriv_webservice.default_api_version = "devel"
        logout()
        self.assertEqual(200, self.webservice.get(build_url).status)
        self.assertEqual(200, unpriv_webservice.get(build_url).status)

    def test_private_snap(self):
        # A SnapBuild with a private Snap is private.
        db_team = self.factory.makeTeam(
            owner=self.person, visibility=PersonVisibility.PRIVATE)
        with person_logged_in(self.person):
            db_build = self.factory.makeSnapBuild(
                requester=self.person, owner=db_team, private=True)
            build_url = api_url(db_build)
        unpriv_webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        unpriv_webservice.default_api_version = "devel"
        logout()
        self.assertEqual(200, self.webservice.get(build_url).status)
        # 404 since we aren't allowed to know that the private team exists.
        self.assertEqual(404, unpriv_webservice.get(build_url).status)

    def test_private_archive(self):
        # A SnapBuild with a private archive is private.
        db_archive = self.factory.makeArchive(owner=self.person, private=True)
        with person_logged_in(self.person):
            db_build = self.factory.makeSnapBuild(archive=db_archive)
            build_url = api_url(db_build)
        unpriv_webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        unpriv_webservice.default_api_version = "devel"
        logout()
        self.assertEqual(200, self.webservice.get(build_url).status)
        self.assertEqual(401, unpriv_webservice.get(build_url).status)

    def test_cancel(self):
        # The owner of a build can cancel it.
        db_build = self.factory.makeSnapBuild(requester=self.person)
        db_build.queueBuild()
        build_url = api_url(db_build)
        unpriv_webservice = webservice_for_person(
            self.factory.makePerson(), permission=OAuthPermission.WRITE_PUBLIC)
        unpriv_webservice.default_api_version = "devel"
        logout()
        build = self.webservice.get(build_url).jsonBody()
        self.assertTrue(build["can_be_cancelled"])
        response = unpriv_webservice.named_post(build["self_link"], "cancel")
        self.assertEqual(401, response.status)
        response = self.webservice.named_post(build["self_link"], "cancel")
        self.assertEqual(200, response.status)
        build = self.webservice.get(build_url).jsonBody()
        self.assertFalse(build["can_be_cancelled"])
        with person_logged_in(self.person):
            self.assertEqual(BuildStatus.CANCELLED, db_build.status)

    def test_rescore(self):
        # Buildd administrators can rescore builds.
        db_build = self.factory.makeSnapBuild(requester=self.person)
        db_build.queueBuild()
        build_url = api_url(db_build)
        buildd_admin = self.factory.makePerson(
            member_of=[getUtility(ILaunchpadCelebrities).buildd_admin])
        buildd_admin_webservice = webservice_for_person(
            buildd_admin, permission=OAuthPermission.WRITE_PUBLIC)
        buildd_admin_webservice.default_api_version = "devel"
        logout()
        build = self.webservice.get(build_url).jsonBody()
        self.assertEqual(2510, build["score"])
        self.assertTrue(build["can_be_rescored"])
        response = self.webservice.named_post(
            build["self_link"], "rescore", score=5000)
        self.assertEqual(401, response.status)
        response = buildd_admin_webservice.named_post(
            build["self_link"], "rescore", score=5000)
        self.assertEqual(200, response.status)
        build = self.webservice.get(build_url).jsonBody()
        self.assertEqual(5000, build["score"])

    def assertCanOpenRedirectedUrl(self, browser, url):
        redirection = self.assertRaises(HTTPError, browser.open, url)
        self.assertEqual(303, redirection.code)
        urlopen(redirection.hdrs["Location"]).close()

    def test_logs(self):
        # API clients can fetch the build and upload logs.
        db_build = self.factory.makeSnapBuild(requester=self.person)
        db_build.setLog(self.factory.makeLibraryFileAlias("buildlog.txt.gz"))
        db_build.storeUploadLog("uploaded")
        build_url = api_url(db_build)
        logout()
        build = self.webservice.get(build_url).jsonBody()
        browser = self.getNonRedirectingBrowser(user=self.person)
        self.assertIsNotNone(build["build_log_url"])
        self.assertCanOpenRedirectedUrl(browser, build["build_log_url"])
        self.assertIsNotNone(build["upload_log_url"])
        self.assertCanOpenRedirectedUrl(browser, build["upload_log_url"])

    def test_getFileUrls(self):
        # API clients can fetch files attached to builds.
        db_build = self.factory.makeSnapBuild(requester=self.person)
        db_files = [
            self.factory.makeSnapFile(snapbuild=db_build) for i in range(2)]
        build_url = api_url(db_build)
        file_urls = [
            ProxiedLibraryFileAlias(file.libraryfile, db_build).http_url
            for file in db_files]
        logout()
        response = self.webservice.named_get(build_url, "getFileUrls")
        self.assertEqual(200, response.status)
        self.assertContentEqual(file_urls, response.jsonBody())
        browser = self.getNonRedirectingBrowser(user=self.person)
        for file_url in file_urls:
            self.assertCanOpenRedirectedUrl(browser, file_url)
