# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Test dscfile.py"""

__metaclass__ = type

import os
import unittest

from lp.archiveuploader.dscfile import findCopyright
from lp.archiveuploader.nascentuploadfile import UploadError
from lp.archiveuploader.tests import mock_logger_quiet
from lp.testing import TestCase


class TestDscFile(TestCase):

    class MockDSCFile:
        copyright = None

    def setUp(self):
        super(TestDscFile, self).setUp()
        self.tmpdir = self.makeTemporaryDirectory()
        self.dir_path = os.path.join(self.tmpdir, "foo", "debian")
        os.makedirs(self.dir_path)
        self.file_path = os.path.join(self.dir_path, "copyright")
        self.dsc_file = self.MockDSCFile()

    def testBadDebianCopyright(self):
        """Test that a symlink instead of a real file will fail."""
        os.symlink("/etc/passwd", self.file_path)
        errors = list(findCopyright(
            self.dsc_file, self.tmpdir, mock_logger_quiet))

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], UploadError)
        self.assertEqual(
            errors[0].message,
            "Symbolic link for debian/copyright not allowed")

    def testGoodDebianCopyright(self):
        copyright = "copyright for dummies"
        file = open(self.file_path, "w")
        file.write(copyright)
        file.close()

        errors = list(findCopyright(
            self.dsc_file, self.tmpdir, mock_logger_quiet))

        self.assertEqual(len(errors), 0)
        self.assertEqual(self.dsc_file.copyright, copyright)

def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
