# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Frequently-used logging utilities for test suite."""

__metaclass__ = type
__all__ = ['MockLogger']

import logging
import sys

# XXX cprov 20071018: This class should be combined with
# launchpad.scripts.logger.FakeLogger at some point.

class MockLogger:
    """Imitates a logger, but prints to standard output."""
    loglevel = logging.INFO

    def __init__(self, outfile=sys.stdout):
        self.outfile = outfile

    def setLevel(self, loglevel):
        self.loglevel = loglevel

    def getEffectiveLevel(self):
        return self.loglevel

    def log(self, *args, **kwargs):
        # The standard logger takes a template string as the first argument.
        log_line = args[0]

        # Only attempt this if we have arguments.
        # Otherwise logging messages with string formatting sequences
        # will die.
        if len(args) > 1:
            log_line %= args[1:]

        self.outfile.write("log> %s\n" % log_line)

        if "exc_info" in kwargs:
            import sys
            import traceback
            exception = traceback.format_exception(*sys.exc_info())
            for item in exception:
                for line in item.splitlines():
                    self.log(line)

    def debug(self, *args, **kwargs):
        if self.loglevel <= logging.DEBUG:
            self.log(*args, **kwargs)

    def info(self, *args, **kwargs):
        if self.loglevel <= logging.INFO:
            self.log(*args, **kwargs)

    def warn(self, *args, **kwargs):
        if self.loglevel <= logging.WARN:
            self.log(*args, **kwargs)

    def error(self, *args, **kwargs):
        if self.loglevel <= logging.ERROR:
            self.log(*args, **kwargs)

    def exception(self, *args):
        self.log(*args, **{'exc_info': True})

