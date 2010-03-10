# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=W0702

"""Code to talk to the database about what the worker script is doing."""

__metaclass__ = type
__all__ = []


import os
import tempfile

from twisted.internet import defer, error, reactor, task
from twisted.python import failure

from zope.component import getUtility

from canonical.config import config
from canonical.librarian.interfaces import IFileUploadClient
from canonical.twistedsupport.loggingsupport import (
    log_oops_from_failure)
from canonical.twistedsupport.processmonitor import (
    ProcessMonitorProtocolWithTimeout)
from lp.code.enums import CodeImportResultStatus
from lp.codehosting.codeimport.worker import CodeImportWorkerExitCode


class CodeImportWorkerMonitorProtocol(ProcessMonitorProtocolWithTimeout):
    """The protocol by which the child process talks to the monitor.

    In terms of bytes, the protocol is extremely simple: any output is stored
    in the log file and seen as timeout-resetting activity.  Every
    config.codeimportworker.heartbeat_update_interval seconds we ask the
    monitor to update the heartbeat of the job we are working on and pass the
    tail of the log output.
    """

    def __init__(self, deferred, worker_monitor, log_file, clock=None):
        """Construct an instance.

        :param deferred: See `ProcessMonitorProtocol.__init__` -- the deferred
            that will be fired when the process has exited.
        :param worker_monitor: A `CodeImportWorkerMonitor` instance.
        :param log_file: A file object that the output of the child
            process will be logged to.
        :param clock: A provider of Twisted's IReactorTime.  This parameter
            exists to allow testing that does not depend on an external clock.
            If a clock is not passed in explicitly the reactor is used.
        """
        ProcessMonitorProtocolWithTimeout.__init__(
            self, deferred, clock=clock,
            timeout=config.codeimport.worker_inactivity_timeout)
        self.worker_monitor = worker_monitor
        self._tail = ''
        self._log_file = log_file
        self._looping_call = task.LoopingCall(self._updateHeartbeat)
        self._looping_call.clock = self._clock

    def connectionMade(self):
        """See `BaseProtocol.connectionMade`.

        We call updateHeartbeat for the first time when we are connected to
        the process and every
        config.codeimportworker.heartbeat_update_interval seconds thereafter.
        """
        ProcessMonitorProtocolWithTimeout.connectionMade(self)
        self._looping_call.start(
            config.codeimportworker.heartbeat_update_interval)

    def _updateHeartbeat(self):
        """Ask the monitor to update the heartbeat.

        We use runNotification() to serialize the updates and ensure
        that any errors are handled properly.  We do not return the
        deferred, as we want this function to be called at a frequency
        independent of how long it takes to update the heartbeat."""
        self.runNotification(
            self.worker_monitor.updateHeartbeat, self._tail)

    def outReceived(self, data):
        """See `ProcessProtocol.outReceived`.

        Any output resets the timeout, is stored in the logfile and
        updates the tail of the log.
        """
        self.resetTimeout()
        self._log_file.write(data)
        self._tail = '\n'.join((self._tail + data).split('\n')[-5:])

    errReceived = outReceived

    def processEnded(self, reason):
        """See `ProcessMonitorProtocolWithTimeout.processEnded`.

        We stop updating the heartbeat when the process exits.
        """
        ProcessMonitorProtocolWithTimeout.processEnded(self, reason)
        self._looping_call.stop()


class ExitQuietly(Exception):
    """Raised to indicate that we should abort and exit without fuss.

    Raised when the job we are working on disappears, as we assume
    this is the result of the job being killed or reclaimed.
    """
    pass


class CodeImportWorkerMonitor:
    """Controller for a single import job.

    An instance of `CodeImportWorkerMonitor` runs a child process to
    perform an import and communicates status to the database.
    """

    path_to_script = os.path.join(
        config.root, 'scripts', 'code-import-worker.py')

    def __init__(self, job_id, logger, codeimport_endpoint):
        """Construct an instance.

        :param job_id: The ID of the CodeImportJob we are to work on.
        :param logger: A `Logger` object.
        """
        self._job_id = job_id
        self._logger = logger
        self.codeimport_endpoint = codeimport_endpoint
        self._call_finish_job = True
        self._log_file = tempfile.TemporaryFile()
        self._branch_url = None

    def _logOopsFromFailure(self, failure):
        request = log_oops_from_failure(
            failure, code_import_job_id=self._job_id, URL=self._branch_url)
        self._logger.info(
            "Logged OOPS id %s: %s: %s",
            request.oopsid, failure.type.__name__, failure.value)

    def _trap_nosuchcodeimportjob(self, failure):
        # XXX if ...
        raise ExitQuietly

    def getWorkerArguments(self):
        """Get XXX for the job we are working on."""
        deferred = self.codeimport_endpoint.callRemote(
            'getImportDataForJobID', self._job_id)
        def _cb(result):
            code_import_arguments, branch_url, log_file_name = result
            self._branch_url = branch_url
            self._log_file_name = log_file_name
            self._logger.info(
                'Found source details: %s', code_import_arguments)
            return code_import_arguments
        return deferred.addCallbacks(_cb, self._trap_nosuchcodeimportjob)

    def updateHeartbeat(self, tail):
        """Call the updateHeartbeat method for the job we are working on."""
        self._logger.debug("Updating heartbeat.")
        deferred = self.codeimport_endpoint.callRemote(
            'updateHeartbeat', self._job_id, tail)
        return deferred.addErrback(self._trap_nosuchcodeimportjob)

    def _createLibrarianFileAlias(self, name, size, file, contentType):
        """Call `IFileUploadClient.remoteAddFile` with the given parameters.

        This is a separate method that exists only to be patched in tests.
        """
        # This blocks, but never mind: nothing else is going on in the process
        # by this point.
        return getUtility(IFileUploadClient).remoteAddFile(
            name, size, file, contentType)

    def finishJob(self, status):
        """Call the finishJob method for the job we are working on.

        This method uploads the log file to the librarian first.
        """
        log_file_size = self._log_file.tell()
        if log_file_size > 0:
            self._log_file.seek(0)
            try:
                log_file_alias_url = self._createLibrarianFileAlias(
                    self._log_file_name, log_file_size, self._log_file,
                    'text/plain')
                self._logger.info(
                    "Uploaded logs to librarian %s.", log_file_alias_url)
            except:
                self._logger.error("Upload to librarian failed.")
                self._logOopsFromFailure(failure.Failure())
                log_file_alias_url = ''
        else:
            log_file_alias_url = ''
        return self.codeimport_endpoint.callRemote(
            'finishJobID', self._job_id, status.name, log_file_alias_url)

    def _makeProcessProtocol(self, deferred):
        """Make an `CodeImportWorkerMonitorProtocol` for a subprocess."""
        return CodeImportWorkerMonitorProtocol(deferred, self, self._log_file)

    def _launchProcess(self, worker_arguments):
        """Launch the code-import-worker.py child process."""
        deferred = defer.Deferred()
        protocol = self._makeProcessProtocol(deferred)
        interpreter = '%s/bin/py' % config.root
        command = [interpreter, self.path_to_script] + worker_arguments
        self._logger.info(
            "Launching worker child process %s.", command)
        reactor.spawnProcess(
            protocol, interpreter, command, env=os.environ, usePTY=True)
        return deferred

    def run(self):
        """Perform the import."""
        return self.getWorkerArguments().addCallback(
            self._launchProcess).addBoth(
            self.callFinishJob).addErrback(
            self._silenceQuietExit)

    def _silenceQuietExit(self, failure):
        """Quietly swallow a ExitQuietly failure."""
        failure.trap(ExitQuietly)
        return None

    def _reasonToStatus(self, reason):
        if isinstance(reason, failure.Failure):
            if reason.check(error.ProcessTerminated):
                if reason.value.exitCode == \
                       CodeImportWorkerExitCode.SUCCESS_NOCHANGE:
                    return CodeImportResultStatus.SUCCESS_NOCHANGE
                elif reason.value.exitCode == \
                       CodeImportWorkerExitCode.SUCCESS_PARTIAL:
                    return CodeImportResultStatus.SUCCESS_PARTIAL
            return CodeImportResultStatus.FAILURE
        else:
            return CodeImportResultStatus.SUCCESS

    def callFinishJob(self, reason):
        """Call finishJob() with the appropriate status."""
        if not self._call_finish_job:
            return reason
        status = self._reasonToStatus(reason)
        if status == CodeImportResultStatus.FAILURE:
            self._log_file.write("Import failed:\n")
            reason.printTraceback(self._log_file)
            self._logOopsFromFailure(reason)
        else:
            self._logger.info('Import succeeded.')
        return self.finishJob(status)
