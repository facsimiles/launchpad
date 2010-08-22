# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Fake, in-process implementation of the Librarian API.

This works in-process only.  It does not support exchange of files
between processes, or URL access.  Nor will it completely support all
details of the Librarian interface.  But where it's enough, this
provides a simple and fast alternative to the full Librarian in unit
tests.
"""

__metaclass__ = type
__all__ = [
    'FakeLibrarian',
    ]

import hashlib
from StringIO import StringIO
from urlparse import urljoin

import transaction
from transaction.interfaces import ISynchronizer
import zope.component
from zope.interface import implements

from canonical.config import config
from canonical.launchpad.database.librarian import (
    LibraryFileAlias,
    LibraryFileContent,
    )
from canonical.launchpad.interfaces.librarian import ILibraryFileAliasSet
from canonical.librarian.client import get_libraryfilealias_download_path
from canonical.librarian.interfaces import (
    ILibrarianClient,
    LIBRARIAN_SERVER_DEFAULT_TIMEOUT,
    )


class InstrumentedLibraryFileAlias(LibraryFileAlias):
    """A `ILibraryFileAlias` implementation that fakes library access."""

    file_committed = False

    def checkCommitted(self):
        """Raise an error if this file has not been committed yet."""
        if not self.file_committed:
            raise LookupError(
                "Attempting to retrieve file '%s' from the fake "
                "librarian, but the file has not yet been committed to "
                "storage." % self.filename)

    def open(self, timeout=LIBRARIAN_SERVER_DEFAULT_TIMEOUT):
        self.checkCommitted()
        self._datafile = StringIO(self.content_string)

    def read(self, chunksize=None, timeout=LIBRARIAN_SERVER_DEFAULT_TIMEOUT):
        return self._datafile.read(chunksize)


class FakeLibrarian(object):
    """A fake, in-process Librarian.

    This takes the role of both the librarian client and the LibraryFileAlias
    utility.
    """
    provided_utilities = [ILibrarianClient, ILibraryFileAliasSet]
    implements(ISynchronizer, *provided_utilities)

    installed_as_librarian = False

    def installAsLibrarian(self):
        """Install this `FakeLibrarian` as the default Librarian."""
        if self.installed_as_librarian:
            return

        transaction.manager.registerSynch(self)

        # Original utilities that need to be restored.
        self.original_utilities = {}

        site_manager = zope.component.getGlobalSiteManager()
        for utility in self.provided_utilities:
            original = zope.component.getUtility(utility)
            if site_manager.unregisterUtility(original, utility):
                # We really disabled a utility, so remember to restore
                # it later.  (Alternatively, the utility object might
                # implement an interface that extends the utility one,
                # in which case we should not restore it.)
                self.original_utilities[utility] = original
            zope.component.provideUtility(self, utility)

        self.installed_as_librarian = True

    def uninstall(self):
        """Un-install this `FakeLibrarian` as the default Librarian."""
        if not self.installed_as_librarian:
            return

        transaction.manager.unregisterSynch(self)

        site_manager = zope.component.getGlobalSiteManager()
        for utility in reversed(self.provided_utilities):
            site_manager.unregisterUtility(self, utility)
            original_utility = self.original_utilities.get(utility)
            if original_utility is not None:
                # We disabled a utility to get here; restore the
                # original.  We do not do this for utilities that were
                # implemented through interface inheritance, because in
                # that case we would never have unregistered anything in
                # the first place.  Re-registering would register the
                # same object twice, for related but different
                # interfaces.
                zope.component.provideUtility(original_utility, utility)

        self.installed_as_librarian = False

    def __init__(self):
        self.aliases = {}
        self.download_url = config.librarian.download_url

    def addFile(self, name, size, file, contentType, expires=None):
        """See `IFileUploadClient`."""
        content = file.read()
        real_size = len(content)
        if real_size != size:
            raise AssertionError(
                "Uploading '%s' to the fake librarian with incorrect "
                "size %d; actual size is %d." % (name, size, real_size))

        file_ref = self._makeLibraryFileContent(content)
        alias = self._makeAlias(file_ref.id, name, content, contentType)
        self.aliases[alias.id] = alias

        return alias.id

    def remoteAddFile(self, name, size, file, contentType, expires=None):
        """See `IFileUploadClient`."""
        return NotImplementedError()

    def getURLForAlias(self, aliasID):
        """See `IFileDownloadClient`."""
        alias = self.aliases.get(aliasID)
        path = get_libraryfilealias_download_path(aliasID, alias.filename)
        return urljoin(self.download_url, path)

    def getFileByAlias(self, aliasID,
                       timeout=LIBRARIAN_SERVER_DEFAULT_TIMEOUT):
        """See `IFileDownloadClient`."""
        alias = self[aliasID]
        alias.checkCommitted()
        return StringIO(alias.content_string)

    def _makeAlias(self, file_id, name, content, content_type):
        """Create a `LibraryFileAlias`."""
        alias = InstrumentedLibraryFileAlias(
            contentID=file_id, filename=name, mimetype=content_type)
        alias.content_string = content
        return alias

    def _makeLibraryFileContent(self, content):
        """Create a `LibraryFileContent`."""
        size = len(content)
        sha1 = hashlib.sha1(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()

        content_object = LibraryFileContent(filesize=size, sha1=sha1, md5=md5)
        return content_object

    def create(self, name, size, file, contentType, expires=None,
               debugID=None, restricted=False):
        "See `ILibraryFileAliasSet`."""
        return self.addFile(
            name, size, file, contentType, expires=expires, debugID=debugID)

    def __getitem__(self, key):
        "See `ILibraryFileAliasSet`."""
        alias = self.aliases.get(key)
        if alias is None:
            raise LookupError(
                "Attempting to retrieve file alias %d from the fake "
                "librarian, who has never heard of it." % key)
        return alias

    def findBySHA1(self, sha1):
        "See `ILibraryFileAliasSet`."""
        for alias in self.aliases.itervalues():
            if alias.content.sha1 == sha1:
                return alias

        return None

    def beforeCompletion(self, txn):
        """See `ISynchronizer`."""

    def afterCompletion(self, txn):
        """See `ISynchronizer`."""
        # Note that all files have been committed to storage.
        for alias in self.aliases.itervalues():
            alias.file_committed = True

    def newTransaction(self, txn):
        """See `ISynchronizer`."""
