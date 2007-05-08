# Copyright 2007 Canonical Ltd.  All rights reserved.

__metaclass__ = type

__all__ = ['datadir', 'getPolicy', 'mock_options', 'mock_logger',
           'mock_logger_quiet']

import os
import sys
import traceback

from canonical.archiveuploader.uploadpolicy import findPolicyByName


here = os.path.dirname(os.path.realpath(__file__))


def datadir(path):
    """Return fully-qualified path inside the test data directory."""
    if path.startswith("/"):
        raise ValueError("Path is not relative: %s" % path)
    return os.path.join(here, 'data', path)




class MockUploadOptions:
    """Mock upload policy options helper"""

    def __init__(self, distro='ubuntutest', distrorelease=None, buildid=None):
        self.distro = distro
        self.distrorelease = distrorelease
        self.buildid = buildid


def getPolicy(name='anything', distro='ubuntu', distrorelease=None,
              buildid=None):
    """Build and return an Upload Policy for the given context."""
    policy = findPolicyByName(name)
    options = MockUploadOptions(distro, distrorelease, buildid)
    policy.setOptions(options)
    return policy


class MockUploadLogger:
    """Mock upload logger facility helper"""

    def __init__(self, verbose=True):
        self.verbose = verbose

    def print_traceback(self, exc_info):
        if exc_info:
            for err_msg in traceback.format_exception(*sys.exc_info()):
                print err_msg

    def debug(self, message, exc_info=False, **kw):
        if self.verbose is not True:
            return
        print 'DEBUG:', message
        self.print_traceback(exc_info)

    def info(self, message, exc_info=False, **kw):
        print 'INFO:', message
        self.print_traceback(exc_info)

    def warn(self, message, exc_info=False, **kw):
        print 'WARN:', message
        self.print_traceback(exc_info)

    def error(self, message, exc_info=False, **kw):
        print 'ERROR:', message
        self.print_traceback(exc_info)


mock_options = MockUploadOptions()
mock_logger = MockUploadLogger()
mock_logger_quiet = MockUploadLogger(verbose=False)
