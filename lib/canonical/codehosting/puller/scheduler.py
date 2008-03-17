# Copyright 2006-2007 Canonical Ltd.  All rights reserved.

__metaclass__ = type
__all__ = ['BadMessage',
           'BranchStatusClient',
           'JobScheduler',
           'LockError',
           'PullerMaster',
           'PullerMasterProtocol',
           'TimeoutError',
           ]


import os
from StringIO import StringIO
import socket
import sys

from twisted.internet import defer, error, reactor
from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import NetstringReceiver, NetstringParseError
from twisted.protocols.policies import TimeoutMixin
from twisted.python import failure

from contrib.glock import GlobalLock, LockAlreadyAcquired

import canonical
from canonical.authserver.client import get_twisted_proxy
from canonical.cachedproperty import cachedproperty
from canonical.codehosting import branch_id_to_path
from canonical.codehosting.puller.worker import (
    get_canonical_url_for_branch_name)
from canonical.codehosting.puller import get_lock_id_for_branch_id
from canonical.config import config
from canonical.launchpad.webapp import errorlog


class BadMessage(Exception):
    """Raised when the protocol receives a message that we don't recognize."""

    def __init__(self, bad_netstring):
        Exception.__init__(
            self, 'Received unrecognized message: %r' % bad_netstring)


class TimeoutError(Exception):
    """Raised when the listener doesn't receive messages for a long time."""


class BranchStatusClient:
    """Twisted client for the branch status methods on the authserver."""

    def __init__(self):
        self.proxy = get_twisted_proxy(config.supermirror.authserver_url)

    def getBranchPullQueue(self, branch_type):
        return self.proxy.callRemote('getBranchPullQueue', branch_type)

    def startMirroring(self, branch_id):
        return self.proxy.callRemote('startMirroring', branch_id)

    def mirrorComplete(self, branch_id, last_revision_id):
        return self.proxy.callRemote(
            'mirrorComplete', branch_id, last_revision_id)

    def mirrorFailed(self, branch_id, reason):
        return self.proxy.callRemote('mirrorFailed', branch_id, reason)

    def recordSuccess(self, name, hostname, date_started, date_completed):
        started_tuple = tuple(date_started.utctimetuple())
        completed_tuple = tuple(date_completed.utctimetuple())
        return self.proxy.callRemote(
            'recordSuccess', name, hostname, started_tuple, completed_tuple)


class ProcessMonitorProtocol(ProcessProtocol):
    """XXX."""

    def __init__(self, deferred, clock=None):
        """Construct an instance of the protocol, for listening to a worker.

        :param deferred: A Deferred that will be fired when the worker has
            finished (either successfully or unsuccesfully).
        :param clock: A provider of Twisted's IReactorTime.  This parameter
            exists to allow testing that does not depend on an external clock.
            If a clock is not passed in explicitly the reactor is used.
        """
        self.deferred = deferred
        if clock is None:
            clock = reactor
        self.clock = clock
        self.notification_lock = defer.DeferredLock()
        self._sigkill_delayed_call = None
        self._termination_failure = None

    def runNotification(self, func, *args):
        d = self.notification_lock.run(func, *args)
        return d.addErrback(self.unexpectedError)

    def unexpectedError(self, failure):
        """
        XXX.
        """
        self._termination_failure = failure
        try:
            self.transport.signalProcess('INT')
            self._sigkill_delayed_call = self.clock.callLater(
                5, self._sigkill)
        except error.ProcessExitedAlready:
            # The process has already died. Fine.
            pass

    def _sigkill(self):
        """Send SIGKILL to the child process.

        We rely on this killing the process, i.e. we assume that
        processEnded() will be called soon after this.
        """
        self._sigkill_delayed_call = None
        try:
            self.transport.signalProcess('KILL')
        except error.ProcessExitedAlready:
            # The process has already died. Fine.
            pass

    def processEnded(self, reason):
        """See `ProcessProtocol.processEnded`.

        Fires the termination deferred with reason or, if the process died
        because we killed it, why we killed it.
        """
        ProcessProtocol.processEnded(self, reason)
        if self._sigkill_delayed_call is not None:
            self._sigkill_delayed_call.cancel()
            self._sigkill_delayed_call = None

        if self._termination_failure is not None:
            reason = self._termination_failure

        def fire_final_deferred():
            if reason.check(error.ProcessDone):
                # self._termination_failure will have been set if a
                # notification that was pending when processEnded was
                # called failed, or None otherwise.
                self.deferred.callback(self._termination_failure)
            else:
                self.deferred.errback(reason)

        self.notification_lock.run(fire_final_deferred)


class PullerMasterProtocol(ProcessMonitorProtocol, NetstringReceiver,
                           TimeoutMixin):
    """The protocol for receiving events from the puller worker."""

    def __init__(self, deferred, listener, clock=None):
        """Construct an instance of the protocol, for listening to a worker.

        :param deferred: A Deferred that will be fired when the worker has
            finished (either successfully or unsuccesfully).
        :param listener: A PullerMaster object that is notified when the
            protocol receives events from the worker.
        :param clock: A provider of Twisted's IReactorTime.  This parameter
            exists to allow testing that does not depend on an external clock.
            If a clock is not passed in explicitly the reactor is used.
        """
        # If the subprocess terminates before it tells us whether the
        # mirroring succeeded or failed, we assume it failed.  That means we
        # have to record whether the subprocess has told us such or not...
        ProcessMonitorProtocol.__init__(self, deferred, clock)
        self.reported_mirror_finished = False
        self.listener = listener
        self._resetState()
        self._stderr = StringIO()
        if clock is None:
            clock = reactor
        self.clock = clock

        self.deferred.addBoth(self.checkReportingFinished)

    def checkReportingFinished(self, reason):
        if not self.reported_mirror_finished:
            # If the process finished before reporting, this is a failure.  If
            # there was any output on stderr, it was probably a traceback and
            # so we use the last line of it as the reason for failing.
            error = self._stderr.getvalue()
            if isinstance(reason, failure.Failure):
                reason.error = error
            if error:
                errorline = error.splitlines()[-1]
            elif isinstance(reason, failure.Failure):
                errorline = str(reason.value)
            else:
                errorline = ('Process exited successfully without reporting '
                             'success or failure?')
                reason = failure.Failure(AssertionError(errorline))
            d = defer.maybeDeferred(
                self.listener.mirrorFailed, errorline, None)
            return d.addBoth(lambda result: reason)
        else:
            return reason

    def reportMirrorFinished(self, ignored):
        self.reported_mirror_finished = True

    def _resetState(self):
        self._current_command = None
        self._expected_args = None
        self._current_args = []

    def callLater(self, period, func):
        """Override TimeoutMixin.callLater so we use self.clock.

        This allows us to write unit tests that don't depend on actual wall
        clock time.
        """
        return self.clock.callLater(period, func)

    def connectionMade(self):
        """Start the timeout counter when connection is made."""
        self.setTimeout(config.supermirror.worker_timeout)

    def dataReceived(self, data):
        NetstringReceiver.dataReceived(self, data)
        # XXX: JonathanLange 2007-10-16
        # bug=http://twistedmatrix.com/trac/ticket/2851: There are no hooks in
        # NetstringReceiver to catch a NetstringParseError. The best we can do
        # is check the value of brokenPeer.
        if self.brokenPeer:
            self.unexpectedError(failure.Failure(NetstringParseError(data)))

    def stringReceived(self, line):
        if (self._current_command is not None
            and self._expected_args is not None):
            self._current_args.append(line)
        elif self._current_command is not None:
            self._expected_args = int(line)
        else:
            if getattr(self, 'do_%s' % line, None) is None:
                self.unexpectedError(failure.Failure(BadMessage(line)))
            else:
                self._current_command = line

        if len(self._current_args) == self._expected_args:
            method = getattr(self, 'do_%s' % self._current_command)
            try:
                method(*self._current_args)
            finally:
                self._resetState()

    def do_startMirroring(self):
        self.resetTimeout()
        self.runNotification(self.listener.startMirroring)

    def do_mirrorSucceeded(self, latest_revision):
        def mirrorSucceeded():
            d = defer.maybeDeferred(
                self.listener.mirrorSucceeded, latest_revision)
            d.addCallback(self.reportMirrorFinished)
            return d
        self.runNotification(mirrorSucceeded)

    def do_mirrorFailed(self, reason, oops):
        def mirrorFailed():
            d = defer.maybeDeferred(
                self.listener.mirrorFailed, reason, oops)
            d.addCallback(self.reportMirrorFinished)
            return d
        self.runNotification(mirrorFailed)

    def do_progressMade(self):
        """Any progress resets the timout counter."""
        self.resetTimeout()

    def outReceived(self, data):
        self.dataReceived(data)

    def errReceived(self, data):
        self._stderr.write(data)

    def timeoutConnection(self):
        """When a timeout occurs, kill the process and record a TimeoutError.
        """
        self.unexpectedError(failure.Failure(TimeoutError()))

    def processEnded(self, reason):
        """See `ProcessProtocol.processEnded`.

        Fires the termination deferred with reason or, if the process died
        because we killed it, why we killed it.
        """
        self.setTimeout(None)
        ProcessMonitorProtocol.processEnded(self, reason)


class PullerMaster:
    """Controller for a single puller worker.

    The `PullerMaster` kicks off a child worker process and handles the events
    generated by that process.
    """

    path_to_script = os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(canonical.__file__))),
        'scripts/mirror-branch.py')
    master_protocol_class = PullerMasterProtocol

    def __init__(self, branch_id, source_url, unique_name, branch_type,
                 logger, client, available_oops_prefixes):
        """Construct a PullerMaster object.

        :param branch_id: The database ID of the branch to be mirrored.
        :param source_url: The location from which the branch is to be
            mirrored.
        :param unique_name: The unique name of the branch to be mirrored.
        :param branch_type: The BranchType of the branch to be mirrored (e.g.
            BranchType.HOSTED).
        :param logger: A Python logging object.
        :param client: An asynchronous client for the branch status XML-RPC
            service.
        :param available_oops_prefixes: A set of OOPS prefixes to pass out to
            worker processes. The purpose is to ensure that there are no
            collisions in OOPS prefixes between currently-running worker
            processes.
        """
        self.branch_id = branch_id
        self.source_url = source_url.strip()
        path = branch_id_to_path(branch_id)
        self.destination_url = os.path.join(
            config.supermirror.branchesdest, path)
        self.unique_name = unique_name
        self.branch_type = branch_type
        self.logger = logger
        self.branch_status_client = client
        self._available_oops_prefixes = available_oops_prefixes

    @cachedproperty
    def oops_prefix(self):
        """Allocate and return an OOPS prefix for the worker process."""
        try:
            return self._available_oops_prefixes.pop()
        except KeyError:
            self.unexpectedError(failure.Failure())
            raise

    def releaseOopsPrefix(self, pass_through=None):
        """Release the OOPS prefix allocated to this worker.

        :param pass_through: An unused parameter that is returned unmodified.
            Useful for adding this method as a Twisted callback / errback.
        """
        self._available_oops_prefixes.add(self.oops_prefix)
        return pass_through

    def mirror(self):
        """Spawn a worker process to mirror a branch."""
        deferred = defer.Deferred()
        protocol = self.master_protocol_class(deferred, self)
        command = [
            sys.executable, self.path_to_script, self.source_url,
            self.destination_url, str(self.branch_id), self.unique_name,
            self.branch_type.name, self.oops_prefix]
        env = os.environ.copy()
        env['BZR_EMAIL'] = get_lock_id_for_branch_id(self.branch_id)
        reactor.spawnProcess(protocol, sys.executable, command, env=env)
        return deferred

    def run(self):
        """Launch a child worker and mirror a branch, handling errors.

        This is the main method to call to mirror a branch.
        """
        deferred = self.mirror()
        deferred.addErrback(self.unexpectedError)
        deferred.addBoth(self.releaseOopsPrefix)
        return deferred

    def startMirroring(self):
        self.logger.info(
            'Mirroring branch %d: %s to %s', self.branch_id, self.source_url,
            self.destination_url)
        return self.branch_status_client.startMirroring(self.branch_id)

    def mirrorFailed(self, reason, oops):
        self.logger.info('Recorded %s', oops)
        self.logger.info('Recorded failure: %s', str(reason))
        return self.branch_status_client.mirrorFailed(self.branch_id, reason)

    def mirrorSucceeded(self, revision_id):
        self.logger.info('Successfully mirrored to rev %s', revision_id)
        return self.branch_status_client.mirrorComplete(
            self.branch_id, revision_id)

    def unexpectedError(self, failure, now=None):
        request = errorlog.ScriptRequest([
            ('branch_id', self.branch_id),
            ('source', self.source_url),
            ('dest', self.destination_url),
            ('error-explanation', failure.getErrorMessage())])
        request.URL = get_canonical_url_for_branch_name(self.unique_name)
        # If the subeprocess exited abnormally, the stderr it produced is
        # probably a much more interesting traceback than the one attached to
        # the Failure we've been passed.
        tb = None
        if failure.check(error.ProcessTerminated):
            tb = getattr(failure, 'error', None)
        if tb is None:
            tb = failure.getTraceback()
        errorlog.globalErrorUtility.raising(
            (failure.type, failure.value, tb), request,
            now)
        self.logger.info('Recorded %s', request.oopsid)


class JobScheduler:
    """Schedule and manage the mirroring of branches.

    The jobmanager is responsible for organizing the mirroring of all
    branches.
    """

    def __init__(self, branch_status_client, logger, branch_type):
        self.branch_status_client = branch_status_client
        self.logger = logger
        self.actualLock = None
        self.branch_type = branch_type
        self.name = 'branch-puller-%s' % branch_type.name.lower()
        self.lockfilename = '/var/lock/launchpad-%s.lock' % self.name

    @cachedproperty
    def available_oops_prefixes(self):
        """Generate and return a set of OOPS prefixes for worker processes.

        This set will contain at most config.supermirror.maximum_workers
        elements. It's expected that the contents of the set will be modified
        by `PullerMaster` objects.
        """
        return set(
            [config.launchpad.errorreports.oops_prefix + str(i)
             for i in range(config.supermirror.maximum_workers)])

    def _run(self, puller_masters):
        """Run all branches_to_mirror registered with the JobScheduler."""
        self.logger.info('%d branches to mirror', len(puller_masters))
        assert config.supermirror.maximum_workers is not None, (
            "config.supermirror.maximum_workers is not defined.")
        semaphore = defer.DeferredSemaphore(
            config.supermirror.maximum_workers)
        deferreds = [
            semaphore.run(puller_master.run)
            for puller_master in puller_masters]
        deferred = defer.gatherResults(deferreds)
        deferred.addCallback(self._finishedRunning)
        return deferred

    def run(self):
        deferred = self.branch_status_client.getBranchPullQueue(
            self.branch_type.name)
        deferred.addCallback(self.getPullerMasters)
        deferred.addCallback(self._run)
        return deferred

    def _finishedRunning(self, ignored):
        self.logger.info('Mirroring complete')
        return ignored

    def getPullerMaster(self, branch_id, branch_src, unique_name):
        branch_src = branch_src.strip()
        return PullerMaster(
            branch_id, branch_src, unique_name, self.branch_type, self.logger,
            self.branch_status_client, self.available_oops_prefixes)

    def getPullerMasters(self, branches_to_pull):
        return [
            self.getPullerMaster(*branch) for branch in branches_to_pull]

    def lock(self):
        self.actualLock = GlobalLock(self.lockfilename)
        try:
            self.actualLock.acquire()
        except LockAlreadyAcquired:
            raise LockError(self.lockfilename)

    def unlock(self):
        self.actualLock.release()

    def recordActivity(self, date_started, date_completed):
        """Record successful completion of the script."""
        return self.branch_status_client.recordSuccess(
            self.name, socket.gethostname(), date_started, date_completed)


class LockError(StandardError):

    def __init__(self, lockfilename):
        StandardError.__init__(self)
        self.lockfilename = lockfilename

    def __str__(self):
        return 'Jobmanager unable to get master lock: %s' % self.lockfilename

