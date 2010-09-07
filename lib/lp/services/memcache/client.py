# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Launchpad Memcache client."""

__metaclass__ = type
__all__ = []

import re

from lazr.restful.utils import get_current_browser_request
import memcache

from canonical.config import config
from lp.services.timeline.requesttimeline import get_request_timeline


def memcache_client_factory():
    """Return a memcache.Client for Launchpad."""
    servers = [
        (host, int(weight)) for host, weight in re.findall(
            r'\((.+?),(\d+)\)', config.memcache.servers)]
    assert len(servers) > 0, "Invalid memcached server list %r" % (
        config.memcache.addresses,)
    return TimelineRecordingClient(servers)


class TimelineRecordingClient(memcache.Client):

    def __get_timeline_action(self, suffix, key):
        request = get_current_browser_request()
        timeline = get_request_timeline(request)
        return timeline.start("memcache-%s" % suffix, key)

    def get(self, key):
        action = self.__get_timeline_action("get", key)
        try:
            return memcache.Client.get(self, key)
        finally:
            action.finish()

    def set(self, key, value, time=0, min_compress_len=0):
        action = self.__get_timeline_action("set", key)
        try:
            return memcache.Client.set(self, key, value, time=time,
                min_compress_len=min_compress_len)
        finally:
            action.finish()
