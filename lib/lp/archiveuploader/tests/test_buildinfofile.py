# Copyright 2017 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Build information file tests."""

import os

from debian.deb822 import Changes

from lp.archiveuploader.buildinfofile import BuildInfoFile
from lp.archiveuploader.nascentuploadfile import UploadError
from lp.archiveuploader.tests.test_nascentuploadfile import (
    PackageUploadFileTestCase,
)
from lp.testing.layers import LaunchpadZopelessLayer


class TestBuildInfoFile(PackageUploadFileTestCase):
    layer = LaunchpadZopelessLayer

    def getBaseBuildInfo(self):
        # XXX cjwatson 2017-03-20: This will need to be fleshed out if we
        # ever start doing non-trivial buildinfo parsing.
        # A Changes object is close enough.
        buildinfo = Changes()
        buildinfo["Format"] = "1.0"
        return buildinfo

    def makeBuildInfoFile(
        self,
        filename,
        buildinfo,
        component_and_section,
        priority_name,
        package,
        version,
        changes,
    ):
        path, md5, sha1, size = self.writeUploadFile(
            filename, buildinfo.dump().encode("UTF-8")
        )
        return BuildInfoFile(
            path,
            {"MD5": md5},
            size,
            component_and_section,
            priority_name,
            package,
            version,
            changes,
            self.policy,
            self.logger,
        )

    def test_properties(self):
        buildinfo = self.getBaseBuildInfo()
        changes = self.getBaseChanges()
        for arch, is_sourceful, is_binaryful, is_archindep in (
            ("source", True, False, False),
            ("all", False, True, True),
            ("i386", False, True, False),
        ):
            buildinfofile = self.makeBuildInfoFile(
                "foo_0.1-1_%s.buildinfo" % arch,
                buildinfo,
                "main/net",
                "extra",
                "dulwich",
                "0.42",
                self.createChangesFile("foo_0.1-1_%s.changes" % arch, changes),
            )
            self.assertEqual(arch, buildinfofile.filename_archtag)
            self.assertEqual(is_sourceful, buildinfofile.is_sourceful)
            self.assertEqual(is_binaryful, buildinfofile.is_binaryful)
            self.assertEqual(is_archindep, buildinfofile.is_archindep)

    def test_storeInDatabase(self):
        buildinfo = self.getBaseBuildInfo()
        changes = self.getBaseChanges()
        buildinfofile = self.makeBuildInfoFile(
            "foo_0.1-1_source.buildinfo",
            buildinfo,
            "main/net",
            "extra",
            "dulwich",
            "0.42",
            self.createChangesFile("foo_0.1-1_source.changes", changes),
        )
        lfa = buildinfofile.storeInDatabase()
        self.layer.txn.commit()
        self.assertEqual(buildinfo.dump().encode("UTF-8"), lfa.read())

    def test_checkBuild(self):
        das = self.factory.makeDistroArchSeries(
            distroseries=self.policy.distroseries, architecturetag="i386"
        )
        build = self.factory.makeBinaryPackageBuild(
            distroarchseries=das, archive=self.policy.archive
        )
        buildinfo = self.getBaseBuildInfo()
        changes = self.getBaseChanges()
        buildinfofile = self.makeBuildInfoFile(
            "foo_0.1-1_i386.buildinfo",
            buildinfo,
            "main/net",
            "extra",
            "dulwich",
            "0.42",
            self.createChangesFile("foo_0.1-1_i386.changes", changes),
        )
        buildinfofile.checkBuild(build)

    def test_checkBuild_inconsistent(self):
        das = self.factory.makeDistroArchSeries(
            distroseries=self.policy.distroseries, architecturetag="amd64"
        )
        build = self.factory.makeBinaryPackageBuild(
            distroarchseries=das, archive=self.policy.archive
        )
        buildinfo = self.getBaseBuildInfo()
        changes = self.getBaseChanges()
        buildinfofile = self.makeBuildInfoFile(
            "foo_0.1-1_i386.buildinfo",
            buildinfo,
            "main/net",
            "extra",
            "dulwich",
            "0.42",
            self.createChangesFile("foo_0.1-1_i386.changes", changes),
        )
        self.assertRaises(UploadError, buildinfofile.checkBuild, build)

    def test_corrupted_buildinfo_files_are_rejected(self):
        # Ensure that we preemptively check and verify checksums before
        # parsing Buildinfo files, as corrupted files can lead to segfaults.

        # Create a corrupted Buildinfo file
        binary_content = os.urandom(1000)
        path, actual_md5, _, size = self.writeUploadFile(
            "foo_0.1-1_i386.buildinfo", binary_content
        )

        changes = self.getBaseChanges()

        # The Changes file specifies a different MD5 hash than the actual file
        expected_md5 = "correct-md5"

        self.assertRaisesWithContent(
            UploadError,
            "File foo_0.1-1_i386.buildinfo mentioned in the changes has a "
            "MD5 mismatch. "
            f"{actual_md5} != {expected_md5}",
            BuildInfoFile,
            path,
            {"MD5": expected_md5, "SHA1": "correct-sha1"},
            size,
            "main/net",
            "extra",
            "dulwich",
            "0.42",
            self.createChangesFile("foo_0.1-1_i386.changes", changes),
            self.policy,
            self.logger,
        )
