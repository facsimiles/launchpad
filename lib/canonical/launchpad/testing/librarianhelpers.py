# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Various helper functions for using the librarian in testing.."""

__metaclass__ = type
__all__ = [
    'get_newest_librarian_file',
]

from storm.expr import Desc
from zope.component import getUtility

from canonical.launchpad.database.librarian import LibraryFileAlias
from canonical.launchpad.webapp.interfaces import (
    IStoreSelector, MAIN_STORE, DEFAULT_FLAVOR)
from canonical.librarian.interfaces import ILibrarianClient


def get_newest_librarian_file():
    """Return the file that was last stored in the librarian.

    Note that a transaction.commit() call is needed before a new file is
    readable from the librarian.

    :return: A file-like object of the file content.
    """
    store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
    alias = store.find(LibraryFileAlias).order_by(
        Desc(LibraryFileAlias.date_created)).first()
    return getUtility(ILibrarianClient).getFileByAlias(alias.id)
