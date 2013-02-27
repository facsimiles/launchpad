# Copyright 2009-2013 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for ftparchive.py"""

__metaclass__ = type

import difflib
import os
import re
import shutil
from textwrap import dedent

from zope.component import getUtility

from lp.archivepublisher.config import getPubConfig
from lp.archivepublisher.diskpool import DiskPool
from lp.archivepublisher.model.ftparchive import (
    AptFTPArchiveFailure,
    FTPArchiveHandler,
    )
from lp.archivepublisher.publishing import Publisher
from lp.registry.interfaces.distribution import IDistributionSet
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.services.config import config
from lp.services.log.logger import (
    BufferLogger,
    DevNullLogger,
    )
from lp.soyuz.enums import (
    PackagePublishingPriority,
    PackagePublishingStatus,
    )
from lp.testing import TestCaseWithFactory
from lp.testing.dbuser import switch_dbuser
from lp.testing.layers import (
    LaunchpadZopelessLayer,
    ZopelessDatabaseLayer,
    )


def sanitize_apt_ftparchive_Sources_output(text):
    # XXX: maxb 2010-04-15 bug=563503: Filter Checksums-* stanzas out of
    # apt-ftparchive Sources file content, such that the output of lucid
    # apt-ftparchive is the same as on karmic.
    return re.subn(r'(?sm)^Checksums-.*?(?=^[^ ])', '', text)[0]


def skip_sha512(text):
    """Ignore SHA512 lines, which are present only in newer distroseries."""
    return re.sub('SHA512: [0-9a-f]*\n', '', text)


class SamplePublisher:
    """Publisher emulation test class."""

    def __init__(self, archive):
        self.archive = archive

    def isAllowed(self, distroseries, pocket):
        return True


class FakeSelectResult:
    """Receive a list and emulate a SelectResult object."""

    def __init__(self, result):
        self._result = result

    def __iter__(self):
        return iter(self._result)

    def count(self):
        return len(self._result)

    def __getslice__(self, i, j):
        return self._result[i:j]


class TestFTPArchive(TestCaseWithFactory):
    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestFTPArchive, self).setUp()
        switch_dbuser(config.archivepublisher.dbuser)

        self._distribution = getUtility(IDistributionSet)['ubuntutest']
        self._archive = self._distribution.main_archive
        self._config = getPubConfig(self._archive)
        self._config.setupArchiveDirs()
        self._sampledir = os.path.join(
            config.root, "lib", "lp", "archivepublisher", "tests",
            "apt-data")
        self._distsdir = self._config.distsroot
        self._confdir = self._config.miscroot
        self._pooldir = self._config.poolroot
        self._overdir = self._config.overrideroot
        self._listdir = self._config.overrideroot
        self._tempdir = self._config.temproot
        self._logger = BufferLogger()
        self._dp = DiskPool(self._pooldir, self._tempdir, self._logger)
        self._publisher = SamplePublisher(self._archive)

    def tearDown(self):
        super(TestFTPArchive, self).tearDown()
        shutil.rmtree(self._config.distroroot)

    def _verifyFile(self, filename, directory, output_filter=None):
        """Compare byte-to-byte the given file and the respective sample.

        It's a poor way of testing files generated by apt-ftparchive.
        """
        result_path = os.path.join(directory, filename)
        result_text = open(result_path).read()
        if output_filter is not None:
            result_text = output_filter(result_text)
        sample_path = os.path.join(self._sampledir, filename)
        sample_text = open(sample_path).read()
        # When the comparison between the sample text and the generated text
        # differ, just printing the strings will be less than optimal.  Use
        # difflib to get a line-by-line comparison that makes it much more
        # immediately obvious what the differences are.
        diff_lines = difflib.ndiff(
            sample_text.splitlines(), result_text.splitlines())
        self.assertEqual(sample_text, result_text, '\n'.join(diff_lines))

    def _verifyEmpty(self, path):
        """Assert that the given file is empty."""
        with open(path) as result_file:
            self.assertEqual("", result_file.read())

    def _addRepositoryFile(self, component, sourcename, leafname):
        """Create a repository file."""
        fullpath = self._dp.pathFor(component, sourcename, leafname)
        dirname = os.path.dirname(fullpath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        leaf = os.path.join(self._sampledir, leafname)
        leafcontent = file(leaf).read()
        file(fullpath, "w").write(leafcontent)

    def _setUpFTPArchiveHandler(self):
        return FTPArchiveHandler(
            self._logger, self._config, self._dp, self._distribution,
            self._publisher)

    def _publishDefaultOverrides(self, fa, component,
                                 phased_update_percentage=None):
        source_overrides = FakeSelectResult([('foo', component, 'misc')])
        binary_overrides = FakeSelectResult([(
            'foo', component, 'misc', 'i386', PackagePublishingPriority.EXTRA,
            phased_update_percentage)])
        fa.publishOverrides('hoary-test', source_overrides, binary_overrides)

    def _publishDefaultFileLists(self, fa, component):
        source_files = FakeSelectResult([('foo', 'foo_1.dsc', component)])
        binary_files = FakeSelectResult(
            [('foo', 'foo_1_i386.deb', component, 'binary-i386')])
        fa.publishFileLists('hoary-test', source_files, binary_files)

    def test_getSourcesForOverrides(self):
        # getSourcesForOverrides returns a list of tuples containing:
        # (sourcename, component, section)

        # Reconfigure FTPArchiveHandler to retrieve sampledata overrides.
        fa = self._setUpFTPArchiveHandler()
        ubuntu = getUtility(IDistributionSet).getByName('ubuntu')
        hoary = ubuntu.getSeries('hoary')
        fa.publisher.archive = hoary.main_archive

        published_sources = fa.getSourcesForOverrides(
            hoary, PackagePublishingPocket.RELEASE)

        # For the above query, we are depending on the sample data to
        # contain seven rows of SourcePackagePublishingHistory data.
        expectedSources = [
            ('linux-source-2.6.15', 'main', 'base'),
            ('libstdc++', 'main', 'base'),
            ('cnews', 'universe', 'base'),
            ('alsa-utils', 'main', 'base'),
            ('pmount', 'main', 'editors'),
            ('netapplet', 'main', 'web'),
            ('evolution', 'main', 'editors'),
            ]
        self.assertEqual(expectedSources, list(published_sources))

    def test_getBinariesForOverrides(self):
        # getBinariesForOverrides returns a list of tuples containing:
        # (sourcename, component, section, archtag, priority,
        # phased_update_percentage)

        # Reconfigure FTPArchiveHandler to retrieve sampledata overrides.
        fa = self._setUpFTPArchiveHandler()
        ubuntu = getUtility(IDistributionSet).getByName('ubuntu')
        hoary = ubuntu.getSeries('hoary')
        fa.publisher.archive = hoary.main_archive

        published_binaries = fa.getBinariesForOverrides(
            hoary, PackagePublishingPocket.RELEASE)
        expectedBinaries = [
            ('pmount', 'main', 'base', 'hppa',
             PackagePublishingPriority.EXTRA, None),
            ('pmount', 'universe', 'editors', 'i386',
             PackagePublishingPriority.IMPORTANT, None),
            ]
        self.assertEqual(expectedBinaries, list(published_binaries))

    def test_getBinariesForOverrides_with_no_architectures(self):
        # getBinariesForOverrides() copes with uninitiazed distroseries
        # (no architectures), returning an empty ResultSet.
        fa = self._setUpFTPArchiveHandler()

        breezy_autotest = self._distribution.getSeries('breezy-autotest')
        self.assertEqual([], list(breezy_autotest.architectures))

        published_binaries = fa.getBinariesForOverrides(
            breezy_autotest, PackagePublishingPocket.RELEASE)
        self.assertEqual([], list(published_binaries))

    def test_publishOverrides(self):
        # publishOverrides write the expected files on disk.
        fa = self._setUpFTPArchiveHandler()
        self._publishDefaultOverrides(fa, 'main')

        # Check that the overrides lists generated by LP exist and have the
        # expected contents.
        self._verifyFile("override.hoary-test.main", self._overdir)
        self._verifyFile("override.hoary-test.main.src", self._overdir)
        self._verifyFile("override.hoary-test.extra.main", self._overdir)

    def test_publishOverrides_more_extra_components(self):
        # more-extra.override.%s.main is used regardless of component.
        fa = self._setUpFTPArchiveHandler()

        sentinel = ("hello/i386", "Task", "minimal")
        extra_overrides = os.path.join(
            self._confdir, "more-extra.override.hoary-test.main")
        with open(extra_overrides, "w") as extra_override_file:
            print >>extra_override_file, "  ".join(sentinel)
        self._publishDefaultOverrides(fa, 'universe')

        result_path = os.path.join(
            self._overdir, "override.hoary-test.extra.universe")
        with open(result_path) as result_file:
            self.assertIn("\t".join(sentinel), result_file.read().splitlines())

    def test_publishOverrides_phase(self):
        # Publications with a non-None phased update percentage produce
        # Phased-Update-Percentage extra overrides.
        fa = self._setUpFTPArchiveHandler()
        self._publishDefaultOverrides(fa, 'main', phased_update_percentage=50)

        path = os.path.join(self._overdir, "override.hoary-test.extra.main")
        with open(path) as result_file:
            self.assertIn(
                "foo/i386\tPhased-Update-Percentage\t50",
                result_file.read().splitlines())

    def test_generateOverrides(self):
        # generateOverrides generates all the overrides from start to finish.
        self._distribution = getUtility(IDistributionSet).getByName('ubuntu')
        self._archive = self._distribution.main_archive
        self._publisher = SamplePublisher(self._archive)
        fa = self._setUpFTPArchiveHandler()
        pubs = self._archive.getAllPublishedBinaries(
            name="pmount", status=PackagePublishingStatus.PUBLISHED,
            distroarchseries=self._distribution.getSeries("hoary")["hppa"])
        for pub in pubs:
            pub.changeOverride(new_phased_update_percentage=30).setPublished()
        fa.generateOverrides(fullpublish=True)
        result_path = os.path.join(self._overdir, "override.hoary.main")
        with open(result_path) as result_file:
            self.assertEqual("pmount\textra\tbase\n", result_file.read())
        result_path = os.path.join(self._overdir, "override.hoary.main.src")
        with open(result_path) as result_file:
            self.assertIn("pmount\teditors\n", result_file.readlines())
        result_path = os.path.join(self._overdir, "override.hoary.extra.main")
        with open(result_path) as result_file:
            self.assertEqual(dedent("""\
                pmount\tOrigin\tUbuntu
                pmount\tBugs\thttps://bugs.launchpad.net/ubuntu/+filebug
                pmount/hppa\tPhased-Update-Percentage\t30
                """), result_file.read())

    def test_getSourceFiles(self):
        # getSourceFiles returns a list of tuples containing:
        # (sourcename, filename, component)

        # Reconfigure FTPArchiveHandler to retrieve sampledata records.
        fa = self._setUpFTPArchiveHandler()
        ubuntu = getUtility(IDistributionSet).getByName('ubuntu')
        hoary = ubuntu.getSeries('hoary')
        fa.distro = ubuntu
        fa.publisher.archive = hoary.main_archive

        sources_files = fa.getSourceFiles(
            hoary, PackagePublishingPocket.RELEASE)
        expected_files = [
            ('alsa-utils', 'alsa-utils_1.0.9a-4ubuntu1.dsc', 'main'),
            ('evolution', 'evolution-1.0.tar.gz', 'main'),
            ('netapplet', 'netapplet_1.0.0.orig.tar.gz', 'main'),
            ]
        self.assertEqual(expected_files, list(sources_files))

    def test_getBinaryFiles(self):
        # getBinaryFiles returns a list of tuples containing:
        # (sourcename, filename, component, architecture)

        # Reconfigure FTPArchiveHandler to retrieve sampledata records.
        fa = self._setUpFTPArchiveHandler()
        ubuntu = getUtility(IDistributionSet).getByName('ubuntu')
        hoary = ubuntu.getSeries('hoary')
        fa.distro = ubuntu
        fa.publisher.archive = hoary.main_archive

        binary_files = fa.getBinaryFiles(
            hoary, PackagePublishingPocket.RELEASE)
        expected_files = [
            ('pmount', 'pmount_1.9-1_all.deb', 'main', 'binary-hppa'),
            ]
        self.assertEqual(expected_files, list(binary_files))

    def test_publishFileLists(self):
        # publishFileLists writes the expected files on disk.
        fa = self._setUpFTPArchiveHandler()
        self._publishDefaultFileLists(fa, 'main')

        # Check that the file lists generated by LP exist and have the
        # expected contents.
        self._verifyFile("hoary-test_main_source", self._listdir)
        self._verifyFile("hoary-test_main_binary-i386", self._listdir)

    def test_generateConfig(self):
        # Generate apt-ftparchive configuration file and run it.

        # Setup FTPArchiveHandler with a real Publisher for Ubuntutest.
        publisher = Publisher(
            self._logger, self._config, self._dp, self._archive)
        fa = FTPArchiveHandler(self._logger, self._config, self._dp,
                               self._distribution, publisher)
        fa.createEmptyPocketRequests(fullpublish=True)

        # Calculate overrides and filelists.
        self._publishDefaultOverrides(fa, 'main')
        self._publishDefaultFileLists(fa, 'main')

        # Add mentioned files in the repository pool/.
        self._addRepositoryFile('main', 'foo', 'foo_1.dsc')
        self._addRepositoryFile('main', 'foo', 'foo_1_i386.deb')

        # When include_long_descriptions is set, apt.conf has
        # LongDescription "true" for that series.
        hoary_test = self._distribution.getSeries('hoary-test')
        self.assertTrue(hoary_test.include_long_descriptions)
        breezy_autotest = self._distribution.getSeries('breezy-autotest')
        breezy_autotest.include_long_descriptions = False

        # XXX cprov 2007-03-21: Relying on byte-to-byte configuration file
        # comparing is weak. We should improve this methodology to avoid
        # wasting time on test failures due to irrelevant format changes.
        apt_conf = fa.generateConfig(fullpublish=True)
        self._verifyFile("apt.conf", self._confdir)

        # XXX cprov 2007-03-21: This is an extra problem. Running a-f on
        # developer machines is wasteful. We need to find a away to split
        # those kind of tests and avoid to run it when performing 'make
        # check'. Although they should remain active in PQM to avoid possible
        # regressions.
        fa.runApt(apt_conf)
        self._verifyFile("Packages",
            os.path.join(self._distsdir, "hoary-test", "main", "binary-i386"),
            skip_sha512)
        self._verifyEmpty(
            os.path.join(
                self._distsdir, "hoary-test", "main", "debian-installer",
                "binary-i386", "Packages"))
        self._verifyFile("Sources",
            os.path.join(self._distsdir, "hoary-test", "main", "source"),
            sanitize_apt_ftparchive_Sources_output)

        # XXX cprov 2007-03-21: see above, byte-to-byte configuration
        # comparing is weak.
        # Test that a publisher run now will generate an empty apt
        # config and nothing else.
        apt_conf = fa.generateConfig()
        assert len(file(apt_conf).readlines()) == 24

        # XXX cprov 2007-03-21: see above, do not run a-f on dev machines.
        fa.runApt(apt_conf)

    def test_generateConfig_empty_and_careful(self):
        # Generate apt-ftparchive config for an specific empty suite.
        #
        # By passing 'careful_apt' option associated with 'allowed_suite'
        # we can publish only a specific group of the suites even if they
        # are still empty. It makes APT clients happier during development
        # cycle.
        #
        # This test should check:
        #
        #  * if apt.conf was generated correctly.
        #  * a-f runs based on this config without any errors
        #  * a-f *only* creates the wanted archive indexes.
        allowed_suites = set()
        allowed_suites.add(('hoary-test', PackagePublishingPocket.UPDATES))

        publisher = Publisher(
            self._logger, self._config, self._dp,
            allowed_suites=allowed_suites, archive=self._archive)

        fa = FTPArchiveHandler(self._logger, self._config, self._dp,
                               self._distribution, publisher)

        fa.createEmptyPocketRequests(fullpublish=True)

        # createEmptyPocketRequests creates empty override and file
        # listings.
        lists = (
            'hoary-test-updates_main_source',
            'hoary-test-updates_main_binary-i386',
            'hoary-test-updates_main_debian-installer_binary-i386',
            'override.hoary-test-updates.main',
            'override.hoary-test-updates.extra.main',
            'override.hoary-test-updates.main.src',
            )

        for listname in lists:
            path = os.path.join(self._config.overrideroot, listname)
            self._verifyEmpty(path)

        # XXX cprov 2007-03-21: see above, byte-to-byte configuration
        # comparing is weak.
        apt_conf = fa.generateConfig(fullpublish=True)
        self.assertTrue(os.path.exists(apt_conf))
        apt_conf_content = file(apt_conf).read()
        sample_content = file(
            os.path.join(
            self._sampledir, 'apt_conf_single_empty_suite_test')).read()
        self.assertEqual(apt_conf_content, sample_content)

        # XXX cprov 2007-03-21: see above, do not run a-f on dev machines.
        fa.runApt(apt_conf)
        self.assertTrue(os.path.exists(
            os.path.join(self._distsdir, "hoary-test-updates", "main",
                         "binary-i386", "Packages")))
        self.assertTrue(os.path.exists(
            os.path.join(self._distsdir, "hoary-test-updates", "main",
                         "debian-installer", "binary-i386", "Packages")))
        self.assertTrue(os.path.exists(
            os.path.join(self._distsdir, "hoary-test-updates", "main",
                         "source", "Sources")))

        self.assertFalse(os.path.exists(
            os.path.join(self._distsdir, "hoary-test", "main",
                         "binary-i386", "Packages")))
        self.assertFalse(os.path.exists(
            os.path.join(self._distsdir, "hoary-test", "main",
                         "debian-installer", "binary-i386", "Packages")))
        self.assertFalse(os.path.exists(
            os.path.join(self._distsdir, "hoary-test", "main",
                         "source", "Sources")))


class TestFTPArchiveRunApt(TestCaseWithFactory):
    """Test `FTPArchive`'s execution of apt-ftparchive."""

    layer = ZopelessDatabaseLayer

    def _makeMatchingDistroArchSeries(self):
        """Create two `DistroArchSeries` for the same distro and processor."""
        distro = self.factory.makeDistribution()
        processor = self.factory.makeProcessor()
        return (
            self.factory.makeDistroArchSeries(
                distroseries=self.factory.makeDistroSeries(distro),
                processorfamily=processor.family,
                architecturetag=processor.name)
            for counter in (1, 2))

    def test_getArchitectureTags_starts_out_empty(self):
        fa = FTPArchiveHandler(
            DevNullLogger(), None, None, self.factory.makeDistribution(),
            None)
        self.assertContentEqual([], fa._getArchitectureTags())

    def test_getArchitectureTags_includes_enabled_architectures(self):
        distroarchseries = self.factory.makeDistroArchSeries()
        fa = FTPArchiveHandler(
            DevNullLogger(), None, None,
            distroarchseries.distroseries.distribution, None)
        self.assertContentEqual(
            [distroarchseries.architecturetag], fa._getArchitectureTags())

    def test_getArchitectureTags_considers_all_series(self):
        distro = self.factory.makeDistribution()
        affluent_antilope = self.factory.makeDistroSeries(distribution=distro)
        bilious_baboon = self.factory.makeDistroSeries(distribution=distro)
        affluent_arch = self.factory.makeDistroArchSeries(
            distroseries=affluent_antilope)
        bilious_arch = self.factory.makeDistroArchSeries(
            distroseries=bilious_baboon)
        fa = FTPArchiveHandler(DevNullLogger(), None, None, distro, None)
        self.assertContentEqual(
            [affluent_arch.architecturetag, bilious_arch.architecturetag],
            fa._getArchitectureTags())

    def test_getArchitectureTags_ignores_disabled_architectures(self):
        distroarchseries = self.factory.makeDistroArchSeries()
        distroarchseries.enabled = False
        fa = FTPArchiveHandler(
            DevNullLogger(), None, None,
            distroarchseries.distroseries.distribution, None)
        self.assertContentEqual([], fa._getArchitectureTags())

    def test_getArchitectureTags_contains_no_duplicates(self):
        ominous_okapi, pilfering_puppy = self._makeMatchingDistroArchSeries()
        fa = FTPArchiveHandler(
            DevNullLogger(), None, None,
            ominous_okapi.distroseries.distribution, None)
        self.assertEqual(1, len(list(fa._getArchitectureTags())))
        self.assertContentEqual(
            [ominous_okapi.architecturetag], fa._getArchitectureTags())

    def test_getArchitectureTags_counts_any_architecture_enabled_once(self):
        manic_mantis, nervous_nit = self._makeMatchingDistroArchSeries()
        nervous_nit.enabled = False
        fa = FTPArchiveHandler(
            DevNullLogger(), None, None,
            manic_mantis.distroseries.distribution, None)
        self.assertContentEqual(
            [manic_mantis.architecturetag], fa._getArchitectureTags())

    def test_runApt_reports_failure(self):
        # If we sabotage apt-ftparchive, runApt notices that it failed
        # and raises an exception.
        distroarchseries = self.factory.makeDistroArchSeries()
        distro = distroarchseries.distroseries.distribution
        fa = FTPArchiveHandler(DevNullLogger(), None, None, distro, None)
        self.assertRaises(AptFTPArchiveFailure, fa.runApt, "bogus-config")
