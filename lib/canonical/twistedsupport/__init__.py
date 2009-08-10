# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Useful tools for interacting with Twisted."""

__metaclass__ = type
__all__ = [
    'defer_to_thread',
    'extract_result',
    'gatherResults',
    'suppress_stderr',
    ]


import StringIO
import sys

from twisted.internet import defer, threads
from twisted.python.util import mergeFunctionMetadata


def defer_to_thread(function):
    """Run in a thread and return a Deferred that fires when done."""

    def decorated(*args, **kwargs):
        return threads.deferToThread(function, *args, **kwargs)

    return mergeFunctionMetadata(function, decorated)


def gatherResults(deferredList):
    """Returns list with result of given Deferreds.

    This differs from Twisted's `defer.gatherResults` in two ways.

     1. It fires the actual first error that occurs, rather than wrapping
        it in a `defer.FirstError`.
     2. All errors apart from the first are consumed. (i.e. `consumeErrors`
        is True.)

    :type deferredList:  list of `defer.Deferred`s.
    :return: `defer.Deferred`.
    """
    def convert_first_error_to_real(failure):
        failure.trap(defer.FirstError)
        return failure.value.subFailure

    d = defer.DeferredList(deferredList, fireOnOneErrback=1, consumeErrors=1)
    d.addCallback(defer._parseDListResult)
    d.addErrback(convert_first_error_to_real)
    return d


def suppress_stderr(function):
    """Deferred friendly decorator that suppresses output from a function.
    """
    def set_stderr(result, stream):
        sys.stderr = stream
        return result

    def wrapper(*arguments, **keyword_arguments):
        saved_stderr = sys.stderr
        ignored_stream = StringIO.StringIO()
        sys.stderr = ignored_stream
        d = defer.maybeDeferred(function, *arguments, **keyword_arguments)
        return d.addBoth(set_stderr, saved_stderr)

    return mergeFunctionMetadata(function, wrapper)


def extract_result(deferred):
    """Extract the result from a fired deferred.

    It can happen that you have an API that returns Deferreds for
    compatibility with Twisted code, but is in fact synchronous, i.e. the
    Deferreds it returns have always fired by the time it returns.  In this
    case, you can use this function to convert the result back into the usual
    form for a synchronous API, i.e. the result itself or a raised exception.

    It would be very bad form to use this as some way of checking if a
    Deferred has fired.
    """
    failures = []
    successes = []
    deferred.addCallbacks(successes.append, failures.append)
    if len(failures) == 1:
        failures[0].raiseException()
    elif len(successes) == 1:
        return successes[0]
    else:
        raise AssertionError("%r has not fired yet." % (deferred,))
