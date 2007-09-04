# Copyright 2005-2007 Canonical Ltd. All rights reserved.

__metaclass__ = type

__all__ = [
    'ExportResult',
    'process_queue',
    ]

import os
import psycopg
import textwrap
import traceback
from StringIO import StringIO
from zope.proxy import removeAllProxies
from zope.component import getUtility

from canonical.config import config
from canonical.launchpad import helpers
from canonical.launchpad.interfaces import (
    ILibraryFileAliasSet, IPOExportRequestSet, IPOTemplate,
    ITranslationExporter, ITranslationFile)
from canonical.launchpad.mail import simple_sendmail


def get_template(obj):
    """Determine translation template that obj relates to.

    :param obj: a translation file or translation template object.  If obj is
        a template, then obj itself is returned.
    """
    if IPOTemplate.providedBy(obj):
        return obj
    return obj.potemplate


class ExportResult:
    """The results of a translation export request.

    This class has three main attributes:

     - name: A short identifying string for this export.
     - url: The Librarian URL for any successfully exported files.
     - failure: Failure got while exporting.
    """

    def __init__(self, name):
        self.name = name
        self.url = None
        self.failure = None

    def _getFailureEmailBody(self, person):
        """Send an email notification about the export failing."""
        return textwrap.dedent('''
            Hello %s,

            Rosetta encountered problems exporting the files you
            requested. The Rosetta team has been notified of this
            problem. Please reply to this email for further assistance.
            ''' % person.browsername)

    def _getSuccessEmailBody(self, person):
        """Send an email notification about the export working."""
        return textwrap.dedent('''
            Hello %s,

            The files you requested from Rosetta are ready for download
            from the following location:

            \t%s''' % (person.browsername, self.url)
            )

    def notify(self, person):
        """Send a notification email to the given person about the export.

        If there is a failure, a copy of the email is also sent to the
        Launchpad error mailing list for debugging purposes.
        """
        if self.failure is None and self.url is not None:
            # There is no failure, so we have a full export without
            # problems.
            body = self._getSuccessEmailBody(person)
        elif self.failure is not None and self.url is None:
            body = self._getFailureEmailBody(person)
        elif self.failure is not None and self.url is not None:
            raise AssertionError(
                'We cannot have a URL for the export and a failure.')
        else:
            raise AssertionError(
                'We neither have the exported URL nor we got a failure.')

        recipients = list(helpers.contactEmailAddresses(person))

        for recipient in [str(recipient) for recipient in recipients]:
            simple_sendmail(
                from_addr=config.rosetta.rosettaadmin.email,
                to_addrs=[recipient],
                subject='Translation download request: %s' % self.name,
                body=body)

        if self.failure is None:
            # There are no errors, so nothing else to do here.
            return

        # The export process had errors that we should notify to admins.
        admins_email_body = textwrap.dedent('''
            Hello admins,

            Rosetta encountered problems exporting some files requested by
            %s. This means we have a bug in
            Launchpad that needs to be fixed to be able to proceed with
            this export. You can see the list of failed files with the
            error we got:

            %s''') % (person.browsername, self.failure)

        simple_sendmail(
            from_addr=config.rosetta.rosettaadmin.email,
            to_addrs=[config.launchpad.errors_address],
            subject='Translation download errors: %s' % self.name,
            body=admins_email_body)

    def addFailure(self):
        """Store an exception that broke the export."""
        # Get the trace back that produced this failure.
        exception = StringIO()
        traceback.print_exc(file=exception)
        exception.seek(0)
        # And store it.
        self.failure = exception.read()


def process_request(person, objects, format, logger):
    """Process a request for an export of Launchpad translation files.

    After processing the request a notification email is sent to the requester
    with the URL to retrieve the file (or the tarball, in case of a request of
    multiple files) and information about files that we failed to export (if
    any).
    """
    translation_exporter = getUtility(ITranslationExporter)
    translation_format_exporter = (
        translation_exporter.getTranslationFormatExporterByFileFormat(format))

    result = ExportResult(person.name)
    translation_file_list = []
    last_template_name = None
    for obj in objects:
        template_name = get_template(obj).displayname
        if template_name != last_template_name:
            logger.debug(
                'Exporting objects for %s, related to template %s'
                % (person.displayname, template_name))
            last_template_name = template_name
        translation_file_list.append(ITranslationFile(obj))

    try:
        exported_file = translation_format_exporter.exportTranslationFiles(
            translation_file_list)
    except (KeyboardInterrupt, SystemExit):
        # We should never catch KeyboardInterrupt or SystemExit.
        raise
    except psycopg.Error:
        # It's a DB exception, we don't catch it either, the export
        # should be done again in a new transaction.
        raise
    except:
        # The export for the current entry failed with an unexpected
        # error, we add the entry to the list of errors.
        result.addFailure()
    else:
        if exported_file.path is None:
            # The exported path is unknown, use translation domain as its
            # filename.
            assert exported_file.file_extension, (
                'File extension must have a value!.')
            exported_path = 'launchpad-export.%s' % (
                exported_file.file_extension)
        else:
            # Convert the path to a single file name so it's noted in
            # librarian.
            exported_path = exported_file.path.replace(os.sep, '_')

        # XXX CarlosPerelloMarin 20070705: Reviewer, is there any way to avoid
        # this other than define the file object like interface in ZCML ?
        content_file = removeAllProxies(exported_file.content_file)
        # Go to the end of the file.
        content_file.seek(0, 2)
        size = content_file.tell()
        # Go back to the start of the file.
        content_file.seek(0)
        alias_set = getUtility(ILibraryFileAliasSet)
        alias = alias_set.create(
            name=exported_path,
            size=size,
            file=content_file,
            contentType=exported_file.content_type)
        result.url = alias.http_url

    result.notify(person)


def process_queue(transaction_manager, logger):
    """Process each request in the translation export queue.

    Each item is removed from the queue as it is processed, so the queue will
    be empty when this function returns.
    """
    request_set = getUtility(IPOExportRequestSet)

    request = request_set.popRequest()
    while request is not None:
        person, objects, format = request

        try:
            process_request(person, objects, format, logger)
        except psycopg.Error:
            # We had a DB error, we don't try to recover it here, just exit
            # from the script and next run will retry the export.
            logger.error(
                "A DB exception was raised when exporting files for %s" % (
                    person.displayname),
                exc_info=True)
            transaction_manager.abort()
            break

        # This is here in case we need to process the same file twice in the
        # same queue run. If we try to do that all in one transaction, the
        # second time we get to the file we'll get a Librarian lookup error
        # because files are not accessible in the same transaction as they're
        # created.
        transaction_manager.commit()
        request = request_set.popRequest()
