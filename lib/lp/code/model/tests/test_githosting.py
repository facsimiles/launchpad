# Copyright 2016 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Unit tests for `GitHostingClient`.

We don't currently do integration testing against a real hosting service,
but we at least check that we're sending the right requests.
"""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type

from contextlib import contextmanager
import json

from httmock import (
    all_requests,
    HTTMock,
    )
from testtools.matchers import MatchesStructure
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.code.errors import (
    GitRepositoryCreationFault,
    GitRepositoryDeletionFault,
    GitRepositoryScanFault,
    )
from lp.code.interfaces.githosting import IGitHostingClient
from lp.services.webapp.url import urlappend
from lp.testing import TestCase
from lp.testing.layers import LaunchpadZopelessLayer


class TestGitHostingClient(TestCase):

    layer = LaunchpadZopelessLayer

    def setUp(self):
        super(TestGitHostingClient, self).setUp()
        self.client = getUtility(IGitHostingClient)
        self.endpoint = removeSecurityProxy(self.client).endpoint
        self.request = None

    @contextmanager
    def mockRequests(self, status_code=200, content=b""):
        @all_requests
        def handler(url, request):
            self.assertIsNone(self.request)
            self.request = request
            return {"status_code": status_code, "content": content}

        with HTTMock(handler):
            yield

    def assertRequest(self, url_suffix, json_data=None, **kwargs):
        self.assertThat(self.request, MatchesStructure.byEquality(
            url=urlappend(self.endpoint, url_suffix), **kwargs))
        if json_data is not None:
            self.assertEqual(json_data, json.loads(self.request.body))

    def test_create(self):
        with self.mockRequests():
            self.client.create("123")
        self.assertRequest(
            "repo", method="POST", json_data={"repo_path": "123"})

    def test_create_clone_from(self):
        with self.mockRequests():
            self.client.create("123", clone_from="122")
        self.assertRequest(
            "repo", method="POST",
            json_data={"repo_path": "123", "clone_from": "122"})

    def test_create_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryCreationFault,
                "Failed to create Git repository: Bad request",
                self.client.create, "123")

    def test_getProperties(self):
        with self.mockRequests(
                content=b'{"default_branch": "refs/heads/master"}'):
            props = self.client.getProperties("123")
        self.assertEqual({"default_branch": "refs/heads/master"}, props)
        self.assertRequest("repo/123", method="GET")

    def test_getProperties_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to get properties of Git repository: Bad request",
                self.client.getProperties, "123")

    def test_setProperties(self):
        with self.mockRequests():
            self.client.setProperties("123", default_branch="refs/heads/a")
        self.assertRequest(
            "repo/123", method="PATCH",
            json_data={"default_branch": "refs/heads/a"})

    def test_setProperties_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to set properties of Git repository: Bad request",
                self.client.setProperties, "123",
                default_branch="refs/heads/a")

    def test_getRefs(self):
        with self.mockRequests(content=b'{"refs/heads/master": {}}'):
            refs = self.client.getRefs("123")
        self.assertEqual({"refs/heads/master": {}}, refs)
        self.assertRequest("repo/123/refs", method="GET")

    def test_getRefs_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to get refs from Git repository: Bad request",
                self.client.getRefs, "123")

    def test_getCommits(self):
        with self.mockRequests(content=b'[{"sha1": "0"}]'):
            commits = self.client.getCommits("123", ["0"])
        self.assertEqual([{"sha1": "0"}], commits)
        self.assertRequest(
            "repo/123/commits", method="POST", json_data={"commits": ["0"]})

    def test_getCommits_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to get commit details from Git repository: "
                "Bad request",
                self.client.getCommits, "123", ["0"])

    def test_getMergeDiff(self):
        with self.mockRequests(content=b'{"patch": ""}'):
            diff = self.client.getMergeDiff("123", "a", "b")
        self.assertEqual({"patch": ""}, diff)
        self.assertRequest("repo/123/compare-merge/a:b", method="GET")

    def test_getMergeDiff_prerequisite(self):
        with self.mockRequests(content=b'{"patch": ""}'):
            diff = self.client.getMergeDiff("123", "a", "b", prerequisite="c")
        self.assertEqual({"patch": ""}, diff)
        self.assertRequest(
            "repo/123/compare-merge/a:b?sha1_prerequisite=c", method="GET")

    def test_getMergeDiff_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to get merge diff from Git repository: Bad request",
                self.client.getMergeDiff, "123", "a", "b")

    def test_detectMerges(self):
        with self.mockRequests(content=b'{"b": "0"}'):
            merges = self.client.detectMerges("123", "a", ["b", "c"])
        self.assertEqual({"b": "0"}, merges)
        self.assertRequest(
            "repo/123/detect-merges/a", method="POST",
            json_data={"sources": ["b", "c"]})

    def test_detectMerges_failure(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryScanFault,
                "Failed to detect merges in Git repository: Bad request",
                self.client.detectMerges, "123", "a", ["b", "c"])

    def test_delete(self):
        with self.mockRequests():
            self.client.delete("123")
        self.assertRequest("repo/123", method="DELETE")

    def test_delete_failed(self):
        with self.mockRequests(status_code=400, content=b"Bad request"):
            self.assertRaisesWithContent(
                GitRepositoryDeletionFault,
                "Failed to delete Git repository: Bad request",
                self.client.delete, "123")
