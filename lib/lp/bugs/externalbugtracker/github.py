# Copyright 2016 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""GitHub ExternalBugTracker utility."""

__metaclass__ = type
__all__ = [
    'BadGitHubURL',
    'GitHub',
    'GitHubRateLimit',
    'IGitHubRateLimit',
    ]

import httplib
import time
from urllib import urlencode
from urlparse import (
    urljoin,
    urlunsplit,
    )

import pytz
import requests
from zope.component import getUtility
from zope.interface import Interface

from lp.bugs.externalbugtracker import (
    BugTrackerConnectError,
    BugWatchUpdateError,
    ExternalBugTracker,
    UnknownRemoteStatusError,
    UnparsableBugTrackerVersion,
    )
from lp.bugs.externalbugtracker.base import LP_USER_AGENT
from lp.bugs.interfaces.bugtask import (
    BugTaskImportance,
    BugTaskStatus,
    )
from lp.bugs.interfaces.externalbugtracker import UNKNOWN_REMOTE_IMPORTANCE
from lp.services.config import config
from lp.services.database.isolation import ensure_no_transaction
from lp.services.webapp.url import urlsplit


class GitHubExceededRateLimit(BugWatchUpdateError):

    def __init__(self, host, reset):
        self.host = host
        self.reset = reset

    def __str__(self):
        return "Rate limit for %s exceeded (resets at %s)" % (
            self.host, time.ctime(self.reset))


class IGitHubRateLimit(Interface):
    """Interface for rate-limit tracking for the GitHub Issues API."""

    def makeRequest(method, url, token=None, **kwargs):
        """Make a request, but only if the remote host's rate limit permits it.

        :param method: The HTTP request method.
        :param url: The URL to request.
        :param token: If not None, an OAuth token to use as authentication
            to the remote host when asking it for the current rate limit.
        :return: A `requests.Response` object.
        :raises GitHubExceededRateLimit: if the rate limit was exceeded.
        """

    def clearCache():
        """Forget any cached rate limits."""


class GitHubRateLimit:
    """Rate-limit tracking for the GitHub Issues API."""

    def __init__(self):
        self.clearCache()

    def _update(self, host, token=None):
        headers = {
            "User-Agent": LP_USER_AGENT,
            "Host": host,
            "Accept": "application/vnd.github.v3+json",
            }
        if token is not None:
            headers["Authorization"] = "token %s" % token
        url = "https://%s/rate_limit" % host
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self._limits[(host, token)] = response.json()["resources"]["core"]
        except requests.RequestException as e:
            raise BugTrackerConnectError(url, e)

    @ensure_no_transaction
    def makeRequest(self, method, url, token=None, **kwargs):
        """See `IGitHubRateLimit`."""
        host = urlsplit(url).netloc
        if (host, token) not in self._limits:
            self._update(host, token=token)
        limit = self._limits[(host, token)]
        if not limit["remaining"]:
            raise GitHubExceededRateLimit(host, limit["reset"])
        response = requests.request(method, url, **kwargs)
        limit["remaining"] -= 1
        return response

    def clearCache(self):
        """See `IGitHubRateLimit`."""
        self._limits = {}


class BadGitHubURL(UnparsableBugTrackerVersion):
    """The GitHub Issues URL is malformed."""


class GitHub(ExternalBugTracker):
    """An `ExternalBugTracker` for dealing with GitHub issues."""

    # Avoid eating through our rate limit unnecessarily.
    batch_query_threshold = 1

    def __init__(self, baseurl):
        _, host, path, query, fragment = urlsplit(baseurl)
        host = "api." + host
        path = path.rstrip("/")
        if not path.endswith("/issues"):
            raise BadGitHubURL(baseurl)
        path = "/repos" + path[:-len("/issues")]
        baseurl = urlunsplit(("https", host, path, query, fragment))
        super(GitHub, self).__init__(baseurl)
        self.cached_bugs = {}

    @property
    def credentials(self):
        credentials_config = config["checkwatches.credentials"]
        # lazr.config.Section doesn't support get().
        try:
            token = credentials_config["%s.token" % self.basehost]
        except KeyError:
            token = None
        return {"token": token}

    def getModifiedRemoteBugs(self, bug_ids, last_accessed):
        """See `IExternalBugTracker`."""
        modified_bugs = self.getRemoteBugBatch(
            bug_ids, last_accessed=last_accessed)
        self.cached_bugs.update(modified_bugs)
        return list(modified_bugs)

    def getRemoteBug(self, bug_id):
        """See `ExternalBugTracker`."""
        bug_id = int(bug_id)
        if bug_id not in self.cached_bugs:
            self.cached_bugs[bug_id] = (
                self._getPage("issues/%s" % bug_id).json())
        return bug_id, self.cached_bugs[bug_id]

    def getRemoteBugBatch(self, bug_ids, last_accessed=None):
        """See `ExternalBugTracker`."""
        # The GitHub API does not support exporting only a subset of bug IDs
        # as a batch.  As a result, our caching is only effective if we have
        # cached *all* the requested bug IDs; this is the case when we're
        # being called on the result of getModifiedRemoteBugs, so it's still
        # a useful optimisation.
        bug_ids = [int(bug_id) for bug_id in bug_ids]
        bugs = {
            bug_id: self.cached_bugs[bug_id]
            for bug_id in bug_ids if bug_id in self.cached_bugs}
        if set(bugs) == set(bug_ids):
            return bugs
        params = [("state", "all")]
        if last_accessed is not None:
            since = last_accessed.astimezone(pytz.UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            params.append(("since", since))
        page = "issues?%s" % urlencode(params)
        for remote_bug in self._getCollection(page):
            # We're only interested in the bug if it's one of the ones in
            # bug_ids.
            if remote_bug["id"] not in bug_ids:
                continue
            bugs[remote_bug["id"]] = remote_bug
            self.cached_bugs[remote_bug["id"]] = remote_bug
        return bugs

    def getRemoteImportance(self, bug_id):
        """See `ExternalBugTracker`."""
        return UNKNOWN_REMOTE_IMPORTANCE

    def getRemoteStatus(self, bug_id):
        """See `ExternalBugTracker`."""
        remote_bug = self.bugs[int(bug_id)]
        state = remote_bug["state"]
        labels = [label["name"] for label in remote_bug["labels"]]
        return " ".join([state] + labels)

    def convertRemoteImportance(self, remote_importance):
        """See `IExternalBugTracker`."""
        return BugTaskImportance.UNKNOWN

    def convertRemoteStatus(self, remote_status):
        """See `IExternalBugTracker`.

        A GitHub status consists of the state followed by optional labels.
        """
        state = remote_status.split(" ", 1)[0]
        if state == "open":
            return BugTaskStatus.NEW
        elif state == "closed":
            return BugTaskStatus.FIXRELEASED
        else:
            raise UnknownRemoteStatusError(remote_status)

    def _getHeaders(self, last_accessed=None):
        """See `ExternalBugTracker`."""
        headers = super(GitHub, self)._getHeaders()
        token = self.credentials["token"]
        if token is not None:
            headers["Authorization"] = "token %s" % token
        headers["Accept"] = "application/vnd.github.v3+json"
        if last_accessed is not None:
            headers["If-Modified-Since"] = (
                last_accessed.astimezone(pytz.UTC).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"))
        return headers

    def _getPage(self, page, last_accessed=None):
        """See `ExternalBugTracker`."""
        # We prefer to use requests here because it knows how to parse Link
        # headers.  Note that this returns a `requests.Response`, not the
        # page data.
        try:
            response = getUtility(IGitHubRateLimit).makeRequest(
                "GET", urljoin(self.baseurl + "/", page),
                headers=self._getHeaders(last_accessed=last_accessed))
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise BugTrackerConnectError(self.baseurl, e)

    def _getCollection(self, base_page, last_accessed=None):
        """Yield each item from a batched remote collection.

        If the collection has not been modified since `last_accessed`, yield
        no items.
        """
        page = base_page
        while page is not None:
            try:
                response = self._getPage(page, last_accessed=last_accessed)
            except BugTrackerConnectError as e:
                if (e.response is not None and
                        e.response.status_code == httplib.NOT_MODIFIED):
                    return
                else:
                    raise
            for item in response.json():
                yield item
            if "next" in response.links:
                page = response.links["next"]["url"]
            else:
                page = None