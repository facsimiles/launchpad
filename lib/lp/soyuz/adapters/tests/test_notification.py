# -*- coding: utf-8 -*-
# NOTE: The first line above must stay first; do not move the copyright
# notice to the top.  See http://www.python.org/dev/peps/pep-0263/.
#
# Copyright 2011 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from email.utils import formataddr
from storm.store import Store
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from canonical.launchpad.webapp.publisher import canonical_url
from canonical.testing.layers import (
    LaunchpadZopelessLayer,
    ZopelessDatabaseLayer,
    )
from lp.archivepublisher.utils import get_ppa_reference
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.services.mail.sendmail import format_address_for_person
from lp.services.log.logger import BufferLogger
from lp.soyuz.adapters.notification import (
    assemble_body,
    calculate_subject,
    get_recipients,
    fetch_information,
    is_auto_sync_upload,
    reject_changes_file,
    person_to_email,
    notify,
    )
from lp.soyuz.interfaces.component import IComponentSet
from lp.soyuz.model.component import ComponentSelection
from lp.soyuz.enums import (
    ArchivePurpose,
    PackageUploadCustomFormat,
    )
from lp.soyuz.model.distroseriessourcepackagerelease import (
    DistroSeriesSourcePackageRelease,
    )
from lp.testing import (
    person_logged_in,
    TestCaseWithFactory,
    )
from lp.testing.mail_helpers import pop_notifications


class TestNotificationRequiringLibrarian(TestCaseWithFactory):

    layer = LaunchpadZopelessLayer

    def test_notify_from_unicode_names(self):
        # People with unicode in their names should appear correctly in the
        # email and not get smashed to ASCII or otherwise transliterated.
        RANDOM_UNICODE = u"Loïc"
        creator = self.factory.makePerson(displayname=RANDOM_UNICODE)
        spr = self.factory.makeSourcePackageRelease(creator=creator)
        self.factory.makeSourcePackageReleaseFile(sourcepackagerelease=spr)
        archive = self.factory.makeArchive(purpose=ArchivePurpose.PRIMARY)
        pocket = PackagePublishingPocket.RELEASE
        distroseries = self.factory.makeDistroSeries()
        distroseries.changeslist = "blah@example.com"
        blamer = self.factory.makePerson()
        notify(
            blamer, spr, [], [], archive, distroseries, pocket,
            action='accepted')
        notifications = pop_notifications()
        self.assertEqual(2, len(notifications))
        msg = notifications[1].get_payload(0)
        body = msg.get_payload(decode=True)
        self.assertIn("Loïc", body)

    def test_calculate_subject_customfile(self):
        lfa = self.factory.makeLibraryFileAlias()
        package_upload = self.factory.makePackageUpload()
        customfile = package_upload.addCustom(
            lfa, PackageUploadCustomFormat.DEBIAN_INSTALLER)
        archive = self.factory.makeArchive()
        pocket = self.factory.getAnyPocket()
        distroseries = self.factory.makeDistroSeries()
        expected_subject = '[PPA %s] [%s/%s] %s - (Accepted)' % (
            get_ppa_reference(archive), distroseries.distribution.name,
            distroseries.getSuite(pocket), lfa.filename)
        subject = calculate_subject(
            None, [], [customfile], archive, distroseries, pocket,
            'accepted')
        self.assertEqual(expected_subject, subject)

    def _setup_notification(self, from_person=None, distroseries=None,
                            spr=None):
        if spr is None:
            spr = self.factory.makeSourcePackageRelease()
        self.factory.makeSourcePackageReleaseFile(sourcepackagerelease=spr)
        archive = self.factory.makeArchive(purpose=ArchivePurpose.PRIMARY)
        pocket = PackagePublishingPocket.RELEASE
        if distroseries is None:
            distroseries = self.factory.makeDistroSeries()
        distroseries.changeslist = "blah@example.com"
        blamer = self.factory.makePerson()
        if from_person is None:
            from_person = self.factory.makePerson()
        notify(
            blamer, spr, [], [], archive, distroseries, pocket,
            action='accepted', announce_from_person=from_person)

    def test_notify_from_person_override(self):
        # notify() takes an optional from_person to override the calculated
        # From: address in announcement emails.
        from_person = self.factory.makePerson()
        self._setup_notification(from_person=from_person)
        notifications = pop_notifications()
        self.assertEqual(2, len(notifications))
        # The first notification is to the blamer,
        # the second is the announce list, which is the one that gets the
        # overridden From:
        self.assertEqual(
            from_person.preferredemail.email, notifications[1]["From"])

    def test_notify_bcc_to_derivatives_list(self):
        # notify() will BCC the announcement email to the address defined in
        # Distribution.package_derivatives_email if it's defined.
        email = "{package_name}_thing@foo.com"
        distroseries = self.factory.makeDistroSeries()
        with person_logged_in(distroseries.distribution.owner):
            distroseries.distribution.package_derivatives_email = email
        spr = self.factory.makeSourcePackageRelease()
        self._setup_notification(distroseries=distroseries, spr=spr)

        notifications = pop_notifications()
        self.assertEqual(2, len(notifications))
        bcc_address = notifications[1]["Bcc"]
        expected_email = email.format(package_name=spr.sourcepackagename.name)
        self.assertIn(expected_email, bcc_address)


class TestNotification(TestCaseWithFactory):

    layer = ZopelessDatabaseLayer

    def test_fetch_information_changes(self):
        changes = {
            'Date': '2001-01-01',
            'Changed-By': 'Foo Bar <foo.bar@canonical.com>',
            'Maintainer': 'Foo Bar <foo.bar@canonical.com>',
            'Changes': ' * Foo!',
            }
        info = fetch_information(
            None, None, changes)
        self.assertEqual('2001-01-01', info['date'])
        self.assertEqual(' * Foo!', info['changesfile'])
        fields = [
            info['changedby'],
            info['maintainer'],
            info['changedby_displayname'],
            info['maintainer_displayname'],
            ]
        for field in fields:
            self.assertEqual('Foo Bar <foo.bar@canonical.com>', field)

    def test_fetch_information_spr(self):
        creator = self.factory.makePerson(displayname=u"foø")
        maintainer = self.factory.makePerson(displayname=u"bær")
        spr = self.factory.makeSourcePackageRelease(
            creator=creator, maintainer=maintainer)
        info = fetch_information(spr, None, None)
        self.assertEqual(info['date'], spr.dateuploaded)
        self.assertEqual(info['changesfile'], spr.changelog_entry)
        self.assertEqual(
            info['changedby'], format_address_for_person(spr.creator))
        self.assertEqual(
            info['maintainer'], format_address_for_person(spr.maintainer))
        self.assertEqual(
            u"foø <%s>" % spr.creator.preferredemail.email,
            info['changedby_displayname'])
        self.assertEqual(
            u"bær <%s>" % spr.maintainer.preferredemail.email,
            info['maintainer_displayname'])

    def test_fetch_information_bprs(self):
        bpr = self.factory.makeBinaryPackageRelease()
        info = fetch_information(None, [bpr], None)
        spr = bpr.build.source_package_release
        self.assertEqual(info['date'], spr.dateuploaded)
        self.assertEqual(info['changesfile'], spr.changelog_entry)
        self.assertEqual(
            info['changedby'], format_address_for_person(spr.creator))
        self.assertEqual(
            info['maintainer'], format_address_for_person(spr.maintainer))
        self.assertEqual(
            info['changedby_displayname'],
            formataddr((spr.creator.displayname,
                        spr.creator.preferredemail.email)))
        self.assertEqual(
            info['maintainer_displayname'],
            formataddr((spr.maintainer.displayname,
                        spr.maintainer.preferredemail.email)))

    def test_calculate_subject_spr(self):
        spr = self.factory.makeSourcePackageRelease()
        archive = self.factory.makeArchive()
        pocket = self.factory.getAnyPocket()
        distroseries = self.factory.makeDistroSeries()
        expected_subject = '[PPA %s] [%s/%s] %s %s (Accepted)' % (
            get_ppa_reference(archive), distroseries.distribution.name,
            distroseries.getSuite(pocket), spr.name, spr.version)
        subject = calculate_subject(
            spr, [], [], archive, distroseries, pocket, 'accepted')
        self.assertEqual(expected_subject, subject)

    def test_calculate_subject_bprs(self):
        bpr = self.factory.makeBinaryPackageRelease()
        archive = self.factory.makeArchive()
        pocket = self.factory.getAnyPocket()
        distroseries = self.factory.makeDistroSeries()
        expected_subject = '[PPA %s] [%s/%s] %s %s (Accepted)' % (
            get_ppa_reference(archive), distroseries.distribution.name,
            distroseries.getSuite(pocket),
            bpr.build.source_package_release.name, bpr.version)
        subject = calculate_subject(
            None, [bpr], [], archive, distroseries, pocket, 'accepted')
        self.assertEqual(expected_subject, subject)

    def test_notify_bpr(self):
        # If we notify about an accepted bpr with no source, it is from a
        # build, and no notification is sent.
        bpr = self.factory.makeBinaryPackageRelease()
        archive = self.factory.makeArchive()
        pocket = self.factory.getAnyPocket()
        distroseries = self.factory.makeDistroSeries()
        person = self.factory.makePerson()
        notify(
            person, None, [bpr], [], archive, distroseries, pocket,
            action='accepted')
        notifications = pop_notifications()
        self.assertEqual(0, len(notifications))

    def test_notify_bpr_rejected(self):
        # If we notify about a rejected bpr with no source, a notification is
        # sent.
        bpr = self.factory.makeBinaryPackageRelease()
        removeSecurityProxy(
            bpr.build.source_package_release).changelog_entry = '* Foo!'
        archive = self.factory.makeArchive()
        pocket = self.factory.getAnyPocket()
        distroseries = self.factory.makeDistroSeries()
        person = self.factory.makePerson()
        notify(
            person, None, [bpr], [], archive, distroseries, pocket,
            action='rejected')
        [notification] = pop_notifications()
        body = notification.as_string()
        self.assertEqual(person_to_email(person), notification['To'])
        self.assertIn('Rejected by archive administrator.\n\n* Foo!\n', body)

    def test_reject_changes_file_no_email(self):
        # If we are rejecting a mail, and the person to notify has no
        # preferred email, we should return early.
        archive = self.factory.makeArchive()
        distroseries = self.factory.makeDistroSeries()
        uploader = self.factory.makePerson()
        removeSecurityProxy(uploader).preferredemail = None
        email = '%s <foo@example.com>' % uploader.displayname
        changes = {'Changed-By': email, 'Maintainer': email}
        logger = BufferLogger()
        reject_changes_file(
            uploader, '/tmp/changes', changes, archive, distroseries, '',
            logger=logger)
        self.assertIn(
            'No recipients have a preferred email.', logger.getLogBuffer())

    def test_reject_with_no_changes(self):
        # If we don't have any files and no changes content, nothing happens.
        archive = self.factory.makeArchive()
        distroseries = self.factory.makeDistroSeries()
        pocket = self.factory.getAnyPocket()
        notify(None, None, (), (), archive, distroseries, pocket)
        notifications = pop_notifications()
        self.assertEqual(0, len(notifications))

    def _run_recipients_test(self, changes, blamer, maintainer, changer):
        distribution = self.factory.makeDistribution()
        archive = self.factory.makeArchive(
            distribution=distribution, purpose=ArchivePurpose.PRIMARY)
        distroseries = self.factory.makeDistroSeries(
            distribution=distribution)
        # Now set the uploaders.
        component = getUtility(IComponentSet).ensure('main')
        if component not in distroseries.components:
            store = Store.of(distroseries)
            store.add(
                ComponentSelection(
                    distroseries=distroseries, component=component))
        archive.newComponentUploader(maintainer, component)
        archive.newComponentUploader(changer, component)
        return get_recipients(
            blamer, archive, distroseries, logger=None, changes=changes)

    def test_get_recipients_good_emails(self):
        # Test get_recipients with good email addresses..
        blamer = self.factory.makePerson()
        maintainer = self.factory.makePerson(
            'maintainer@canonical.com', displayname='Maintainer')
        changer = self.factory.makePerson(
            'changer@canonical.com', displayname='Changer')
        changes = {
            'Date': '2001-01-01',
            'Changed-By': 'Changer <changer@canonical.com>',
            'Maintainer': 'Maintainer <maintainer@canonical.com>',
            'Changes': ' * Foo!',
            }
        recipients = self._run_recipients_test(
            changes, blamer, maintainer, changer)
        expected = [format_address_for_person(p)
                    for p in (blamer, maintainer, changer)]
        self.assertEqual(expected, recipients)

    def test_get_recipients_bad_maintainer_email(self):
        blamer = self.factory.makePerson()
        maintainer = self.factory.makePerson(
            'maintainer@canonical.com', displayname='Maintainer')
        changer = self.factory.makePerson(
            'changer@canonical.com', displayname='Changer')
        changes = {
            'Date': '2001-01-01',
            'Changed-By': 'Changer <changer@canonical.com>',
            'Maintainer': 'Maintainer <maintainer at canonical.com>',
            'Changes': ' * Foo!',
            }
        recipients = self._run_recipients_test(
            changes, blamer, maintainer, changer)
        expected = [format_address_for_person(p)
                    for p in (blamer, changer)]
        self.assertEqual(expected, recipients)

    def test_get_recipients_bad_changedby_email(self):
        # Test get_recipients with invalid changedby email address.
        blamer = self.factory.makePerson()
        maintainer = self.factory.makePerson(
            'maintainer@canonical.com', displayname='Maintainer')
        changer = self.factory.makePerson(
            'changer@canonical.com', displayname='Changer')
        changes = {
            'Date': '2001-01-01',
            'Changed-By': 'Changer <changer at canonical.com>',
            'Maintainer': 'Maintainer <maintainer@canonical.com>',
            'Changes': ' * Foo!',
            }
        recipients = self._run_recipients_test(
            changes, blamer, maintainer, changer)
        expected = [format_address_for_person(p)
                    for p in (blamer, maintainer)]
        self.assertEqual(expected, recipients)

    def test_assemble_body_handles_no_preferred_email_for_changer(self):
        # If changer has no preferred email address,
        # assemble_body should still work.
        spr = self.factory.makeSourcePackageRelease()
        blamer = self.factory.makePerson()
        archive = self.factory.makeArchive()
        series = self.factory.makeDistroSeries()

        spr.creator.setPreferredEmail(None)

        body = assemble_body(blamer, spr, [], archive, series, "",
                             None, "unapproved")
        self.assertIn("Waiting for approval", body)

    def test_assemble_body_inserts_package_url_for_distro_upload(self):
        # The email body should contain the canonical url to the package
        # page in the target distroseries.
        spr = self.factory.makeSourcePackageRelease()
        blamer = self.factory.makePerson()
        archive = self.factory.makeArchive(purpose=ArchivePurpose.PRIMARY)
        series = self.factory.makeDistroSeries()

        body = assemble_body(blamer, spr, [], archive, series, "",
                             None, "unapproved")
        dsspr = DistroSeriesSourcePackageRelease(series, spr)
        url = canonical_url(dsspr)
        self.assertIn(url, body)

    def test__is_auto_sync_upload__no_preferred_email_for_changer(self):
        # If changer has no preferred email address,
        # is_auto_sync_upload should still work.
        result = is_auto_sync_upload(
            spr=None, bprs=None, pocket=None, changed_by_email=None)
        self.assertFalse(result)
