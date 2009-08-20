# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import unittest
import os.path

from canonical.zeca.zeca import locate_key


class LocateKeyTestCase(unittest.TestCase):
    root = os.path.join(os.path.dirname(__file__), 'keys')

    def assertKeyFile(self, suffix, filename):
        """Verify that a suffix maps to the given filename."""

        if filename is not None:
            filename = os.path.join(self.root, filename)
        self.assertEqual(locate_key(self.root, suffix), filename)

    def test_exact_fingerprint_match(self):
        self.assertKeyFile(
            '0xA419AE861E88BC9E04B9C26FBA2B9389DFD20543.get',
            '0xA419AE861E88BC9E04B9C26FBA2B9389DFD20543.get')

    def test_keyid_glob_match(self):
        self.assertKeyFile(
            '0xDFD20543.get',
            '0xA419AE861E88BC9E04B9C26FBA2B9389DFD20543.get')

    def test_keyid_without_prefix_glob_match(self):
        self.assertKeyFile(
            'DFD20543.get',
            '0xA419AE861E88BC9E04B9C26FBA2B9389DFD20543.get')

    def test_keyid_no_match(self):
        self.assertKeyFile('0xDEADBEEF.get', None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LocateKeyTestCase))
    return suite

