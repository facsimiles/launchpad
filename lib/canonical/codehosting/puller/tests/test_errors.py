import httplib
import os
import re
import socket
import tempfile
import urllib2
import unittest

import bzrlib
from bzrlib.branch import BranchReferenceFormat
from bzrlib import bzrdir
from bzrlib.errors import (
    BzrError, UnsupportedFormatError, UnknownFormatError, ParamikoNotPresent,
    NotBranchError)
from bzrlib.tests import TestCaseWithTransport
from bzrlib.transport import get_transport

from canonical.codehosting import branch_id_to_path
from canonical.codehosting.puller.tests import PullerWorkerMixin
from canonical.codehosting.puller.worker import (
    BadUrlSsh,
    BadUrlLaunchpad,
    BranchReferenceLoopError,
    PullerWorker,
    PullerWorkerProtocol)
from canonical.launchpad.interfaces import BranchType
from canonical.launchpad.webapp.uri import InvalidURIError
from canonical.testing import reset_logging


class StubbedPullerWorkerProtocol(PullerWorkerProtocol):
    """A `PullerWorkerProtocol` that logs events without acting on them."""

    def __init__(self):
        # We are deliberately not calling PullerWorkerProtocol.__init__:
        # pylint: disable-msg=W0231
        self.calls = []

    def sendEvent(self, command, *args):
        """Capture and log events."""
        log_event = tuple([command] + list(args))
        self.calls.append(log_event)


class StubbedPullerWorker(PullerWorker):
    """Partially stubbed subclass of PullerWorker, for unit tests."""

    enable_checkBranchReference = False
    enable_checkSourceUrl = True

    def _checkSourceUrl(self, url):
        if self.enable_checkSourceUrl:
            PullerWorker._checkSourceUrl(self, url)

    def _checkBranchReference(self, location):
        if self.enable_checkBranchReference:
            PullerWorker._checkBranchReference(self, location)

    def _openSourceBranch(self):
        self.testcase.open_call_count += 1

    def _mirrorToDestBranch(self):
        pass


class ErrorHandlingTestCase(unittest.TestCase):
    """Base class to test PullerWorker error reporting."""

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._errorHandlingSetUp()

    def _errorHandlingSetUp(self):
        """Setup code that is specific to ErrorHandlingTestCase.

        This is needed because TestReferenceMirroring uses a diamond-shaped
        class hierarchy and we do not want to end up calling
        unittest.TestCase.setUp twice.
        """
        self.protocol = StubbedPullerWorkerProtocol()
        self.branch = StubbedPullerWorker(
            src='foo', dest='bar', branch_id=1,
            unique_name='owner/product/foo', branch_type=None,
            protocol=self.protocol, oops_prefix='TOKEN')
        self.open_call_count = 0
        self.branch.testcase = self

    def runMirrorAndGetError(self):
        """Mirror the branch and return the error message.

        Runs mirror, checks that we receive exactly one error, and returns the
        str() of the error.
        """
        self.branch.mirror()
        self.assertEqual(
            2, len(self.protocol.calls),
            "Expected startMirroring and mirrorFailed, got: %r"
            % (self.protocol.calls,))
        startMirroring, mirrorFailed = self.protocol.calls
        self.assertEqual(('startMirroring',), startMirroring)
        self.assertEqual('mirrorFailed', mirrorFailed[0])
        self.assert_('TOKEN' in mirrorFailed[2])
        self.protocol.calls = []
        return str(mirrorFailed[1])

    def runMirrorAndAssertErrorStartsWith(self, expected_msg):
        """Mirror the branch and assert the error starts with `expected_msg`.

        Runs mirror and checks that we receive exactly one error, the str()
        of which starts with `expected_msg`.
        """
        error = self.runMirrorAndGetError()
        if not error.startswith(expected_msg):
            self.fail('Expected "%s" but got "%s"' % (expected_msg, error))

    def runMirrorAndAssertErrorEquals(self, expected_error):
        """Mirror the branch and assert the error message is `expected_error`.

        Runs mirror and checks that we receive exactly one error, the str() of
        which is equal to `expected_error`.
        """
        error = self.runMirrorAndGetError()
        self.assertEqual(error, expected_error)


class TestBadUrl(ErrorHandlingTestCase):
    """Test that PullerWorker does not try mirroring from bad URLs.

    Bad URLs use schemes like sftp or bzr+ssh that usually require
    authentication, and hostnames in the launchpad.net domains.

    This prevents errorspam produced by ssh when it cannot connect and saves
    timing out when trying to connect to chinstrap, sodium (always using a
    ssh-based scheme) or launchpad.net.

    That also allows us to display a more informative error message to the
    user.
    """

    def testBadUrlSftp(self):
        # If the scheme of the source url is sftp, _openSourceBranch raises
        # BadUrlSsh.
        self.assertRaises(
            BadUrlSsh, self.branch._checkSourceUrl,
            'sftp://example.com/foo')

    def testBadUrlBzrSsh(self):
        # If the scheme of the source url is bzr+ssh, _openSourceBracnh raises
        # BadUrlSsh.
        self.assertRaises(
            BadUrlSsh, self.branch._checkSourceUrl,
            'bzr+ssh://example.com/foo')

    def testBadUrlBzrSshCaught(self):
        # The exception raised if the scheme of the source url is sftp or
        # bzr+ssh is caught and an informative error message is displayed to
        # the user.
        expected_msg = "Launchpad cannot mirror branches from SFTP "
        self.branch.source = 'sftp://example.com/foo'
        self.runMirrorAndAssertErrorStartsWith(expected_msg)
        self.branch.source = 'bzr+ssh://example.com/foo'
        self.runMirrorAndAssertErrorStartsWith(expected_msg)

    def testBadUrlLaunchpadDomain(self):
        # If the host of the source branch is in the launchpad.net domain,
        # _openSourceBranch raises BadUrlLaunchpad.
        self.assertRaises(
            BadUrlLaunchpad, self.branch._checkSourceUrl,
            'http://bazaar.launchpad.dev/foo')
        self.assertRaises(
            BadUrlLaunchpad, self.branch._checkSourceUrl,
            'sftp://bazaar.launchpad.dev/bar')
        self.assertRaises(
            BadUrlLaunchpad, self.branch._checkSourceUrl,
            'http://launchpad.dev/baz')

    def testBadUrlLaunchpadCaught(self):
        # The exception raised if the host of the source url is launchpad.net
        # or a host in this domain is caught, and an informative error message
        # is displayed to the user.
        expected_msg = "Launchpad does not mirror branches from Launchpad."
        self.branch.source = 'http://bazaar.launchpad.dev/foo'
        self.runMirrorAndAssertErrorEquals(expected_msg)
        self.branch.source = 'http://launchpad.dev/foo'
        self.runMirrorAndAssertErrorEquals(expected_msg)


class TestReferenceMirroring(TestCaseWithTransport, ErrorHandlingTestCase):
    """Feature tests for mirroring of branch references."""

    def setUp(self):
        TestCaseWithTransport.setUp(self)
        ErrorHandlingTestCase._errorHandlingSetUp(self)
        self.branch.enable_checkBranchReference = True

    def tearDown(self):
        TestCaseWithTransport.tearDown(self)
        reset_logging()

    def testCreateBranchReference(self):
        # createBranchReference creates a branch reference and returns a URL
        # that points to that branch reference.

        # First create a branch and a reference to that branch.
        target_branch = self.make_branch('repo')
        reference_url = self.createBranchReference(target_branch.base)

        # References are transparent, so we can't test much about them. The
        # least we can do is confirm that the reference URL isn't the branch
        # URL.
        self.assertNotEqual(reference_url, target_branch.base)

        # Open the branch reference and check that the result is indeed the
        # branch we wanted it to point at.
        opened_branch = bzrlib.branch.Branch.open(reference_url)
        self.assertEqual(opened_branch.base, target_branch.base)

    def createBranchReference(self, url):
        """Create a pure branch reference that points to the specified URL.

        :param url: target of the branch reference.
        :return: file url to the created pure branch reference.
        """
        # XXX DavidAllouche 2007-09-12
        # We do this manually because the bzrlib API does not support creating
        # a branch reference without opening it. See bug 139109.
        t = get_transport(self.get_url('.'))
        t.mkdir('reference')
        a_bzrdir = bzrdir.BzrDir.create(self.get_url('reference'))
        branch_reference_format = BranchReferenceFormat()
        branch_transport = a_bzrdir.get_branch_transport(
            branch_reference_format)
        branch_transport.put_bytes('location', url)
        branch_transport.put_bytes(
            'format', branch_reference_format.get_format_string())
        return a_bzrdir.root_transport.base

    def testGetBranchReferenceValue(self):
        # PullerWorker._getBranchReference gives the reference value for
        # a branch reference.
        reference_value = 'http://example.com/branch'
        reference_url = self.createBranchReference(reference_value)
        self.branch.source = reference_url
        self.assertEqual(
            self.branch._getBranchReference(reference_url), reference_value)

    def testGetBranchReferenceNone(self):
        # PullerWorker._getBranchReference gives None for a normal branch.
        self.make_branch('repo')
        branch_url = self.get_url('repo')
        self.assertIs(
            self.branch._getBranchReference(branch_url), None)

    def testHostedBranchReference(self):
        # A branch reference for a hosted branch must cause an error.
        reference_url = self.createBranchReference(
            'http://example.com/branch')
        self.branch.branch_type = BranchType.HOSTED
        self.branch.source = reference_url
        expected_msg = (
            "Branch references are not allowed for branches of type Hosted.")
        error = self.runMirrorAndAssertErrorEquals(expected_msg)
        self.assertEqual(self.open_call_count, 0)

    def testMirrorLocalBranchReference(self):
        # A file:// branch reference for a mirror branch must cause an error.
        reference_url = self.createBranchReference('file:///sauces/sikrit')
        self.branch.branch_type = BranchType.MIRRORED
        self.branch.source = reference_url
        expected_msg = ("Bad branch reference value: file:///sauces/sikrit")
        self.runMirrorAndAssertErrorEquals(expected_msg)
        self.assertEqual(self.open_call_count, 0)


class TestErrorHandling(ErrorHandlingTestCase):
    """Test our error messages for when the source branch has problems."""

    def setUp(self):
        ErrorHandlingTestCase.setUp(self)
        self.branch.enable_checkSourceUrl = False

    def testHTTPError(self):
        # If the source branch requires HTTP authentication, say so in the
        # error message.
        def stubOpenSourceBranch(url):
            raise urllib2.HTTPError(
                'http://something', httplib.UNAUTHORIZED,
                'Authorization Required', 'some headers',
                open(tempfile.mkstemp()[1]))
        self.branch._openSourceBranch = stubOpenSourceBranch
        self.runMirrorAndAssertErrorEquals("Authentication required.")

    def testSocketErrorHandling(self):
        # If a socket error occurs accessing the source branch, say so in the
        # error message.
        def stubOpenSourceBranch(url):
            raise socket.error('foo')
        self.branch._openSourceBranch = stubOpenSourceBranch
        expected_msg = 'A socket error occurred:'
        self.runMirrorAndAssertErrorStartsWith(expected_msg)

    def testUnsupportedFormatErrorHandling(self):
        # If we don't support the format that the source branch is in, say so
        # in the error message.
        def stubOpenSourceBranch(url):
            raise UnsupportedFormatError('Bazaar-NG branch, format 0.0.4')
        self.branch._openSourceBranch = stubOpenSourceBranch
        expected_msg = 'Launchpad does not support branches '
        self.runMirrorAndAssertErrorStartsWith(expected_msg)

    def testUnknownFormatError(self):
        # If the format is completely unknown to us, say so in the error
        # message.
        def stubOpenSourceBranch(url):
            raise UnknownFormatError(format='Bad format')
        self.branch._openSourceBranch = stubOpenSourceBranch
        self.runMirrorAndAssertErrorStartsWith('Unknown branch format: ')

    def testParamikoNotPresent(self):
        # If, somehow, we try to mirror a branch that requires SSH, we tell
        # the user we cannot do so.
        def stubOpenSourceBranch(url):
            # XXX: JonathanLange 2008-06-25: It's bogus to assume that this is
            # the error we'll get if we try to mirror over SSH.
            raise ParamikoNotPresent('No module named paramiko')
        self.branch._openSourceBranch = stubOpenSourceBranch
        expected_msg = ('Launchpad cannot mirror branches from SFTP and SSH '
                        'URLs. Please register a HTTP location for this '
                        'branch.')
        self.runMirrorAndAssertErrorEquals(expected_msg)

    def testNotBranchErrorMirrored(self):
        # Log a user-friendly message when we are asked to mirror a
        # non-branch.
        def stubOpenSourceBranch(url):
            raise NotBranchError('http://example.com/not-branch')
        self.branch._openSourceBranch = stubOpenSourceBranch
        self.branch.branch_type = BranchType.MIRRORED
        expected_msg = 'Not a branch: "http://example.com/not-branch".'
        self.runMirrorAndAssertErrorEquals(expected_msg)

    def testNotBranchErrorHosted(self):
        # The not-a-branch error message does *not* include the Branch id from
        # the database. Instead, the path is translated to a user-visible
        # location.
        split_id = branch_id_to_path(self.branch.branch_id)
        def stubOpenSourceBranch(url):
            raise NotBranchError('/srv/sm-ng/push-branches/%s/.bzr/branch/'
                                 % split_id)
        self.branch._openSourceBranch = stubOpenSourceBranch
        self.branch.branch_type = BranchType.HOSTED
        expected_msg = 'Not a branch: "sftp://bazaar.launchpad.net/~%s".' % (
            self.branch.unique_name,)
        self.runMirrorAndAssertErrorEquals(expected_msg)

    def testNotBranchErrorImported(self):
        # The not-a-branch error message for import branch does not disclose
        # the internal URL. Since there is no user-visible URL to blame, we do
        # not display any URL at all.
        def stubOpenSourceBranch(url):
            raise NotBranchError('http://canonical.example.com/internal/url')
        self.branch._openSourceBranch = stubOpenSourceBranch
        self.branch.branch_type = BranchType.IMPORTED
        self.runMirrorAndAssertErrorEquals('Not a branch.')

    def testBranchReferenceLoopError(self):
        """BranchReferenceLoopError exceptions are caught."""
        def stubCheckBranchReference(location):
            raise BranchReferenceLoopError()
        self.branch._checkBranchReference = stubCheckBranchReference
        self.runMirrorAndAssertErrorEquals("Circular branch reference.")

    def testInvalidURIError(self):
        """When a branch reference contains an invalid URL, an InvalidURIError
        is raised. The worker catches this and reports it to the scheduler.
        """
        def stubCheckBranchReference(location):
            raise InvalidURIError("This is not a URL")
        self.branch._checkBranchReference = stubCheckBranchReference
        self.runMirrorAndAssertErrorEquals("This is not a URL")

    def testBzrErrorHandling(self):
        def stubOpenSourceBranch(location):
            raise BzrError('A generic bzr error')
        self.branch._openSourceBranch = stubOpenSourceBranch
        expected_msg = 'A generic bzr error'
        self.runMirrorAndAssertErrorEquals(expected_msg)


# XXX: JonathanLange 2008-06-25: This test case checks source problems, just
# like the test case above. They should be combined.
class TestPullerWorker_SourceProblems(TestCaseWithTransport,
                                      PullerWorkerMixin):
    """Tests for robustness in the face of source branch problems."""

    def tearDown(self):
        super(TestPullerWorker_SourceProblems, self).tearDown()
        reset_logging()

    def makePullerWorker(self, *args, **kwargs):
        """Make a puller worker with a stub protocol."""
        return PullerWorkerMixin.makePullerWorker(
            self, protocol=StubbedPullerWorkerProtocol(), *args, **kwargs)

    def assertMirrorFailed(self, puller_worker, message_substring):
        """Assert that puller_worker failed with a particular message.

        Asserts that `message_substring` is in the message. Note that
        `puller_worker` must use a `StubbedPullerWorkerProtocol`.
        """
        protocol = puller_worker.protocol
        self.assertEqual(
            2, len(protocol.calls),
            "Expected startMirroring and mirrorFailed, got: %r"
            % (protocol.calls,))
        startMirroring, mirrorFailed = protocol.calls
        self.assertEqual(('startMirroring',), startMirroring)
        self.assertEqual('mirrorFailed', mirrorFailed[0])
        self.assertContainsRe(
            str(mirrorFailed[1]), re.escape(message_substring))

    def testUnopenableSourceDoesNotCreateMirror(self):
        # The destination branch is not created if we cannot open the source
        # branch.
        non_existent_source = os.path.abspath('nonsensedir')
        dest_dir = 'dest-dir'
        my_branch = self.makePullerWorker(
            src_dir=non_existent_source, dest_dir=dest_dir)
        my_branch.mirror()
        self.failIf(os.path.exists(dest_dir), 'dest-dir should not exist')

    def testMissingSourceWhines(self):
        # If we can't open the source branch, we get an error message
        # complaining of the problem.
        non_existent_source = os.path.abspath('nonsensedir')
        my_branch = self.makePullerWorker(
            src_dir=non_existent_source, dest_dir="non-existent-destination")
        my_branch.mirror()
        self.assertMirrorFailed(my_branch, 'Not a branch')


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
