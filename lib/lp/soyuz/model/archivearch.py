# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = ['ArchiveArch', 'ArchiveArchSet']

from zope.component import getUtility
from zope.interface import implements

from lp.soyuz.interfaces.archivearch import (
    IArchiveArch, IArchiveArchSet)
from lp.soyuz.model.processor import ProcessorFamily
from canonical.launchpad.webapp.interfaces import (
    IStoreSelector, MAIN_STORE, DEFAULT_FLAVOR)

from storm.expr import Join, LeftJoin
from storm.locals import Int, Reference, Storm


class ArchiveArch(Storm):
    """See `IArchiveArch`."""
    implements(IArchiveArch)
    __storm_table__ = 'ArchiveArch'
    id = Int(primary=True)

    archive_id = Int(name='archive', allow_none=False)
    archive = Reference(archive_id, 'Archive.id')
    processorfamily_id = Int(name='processorfamily', allow_none=True)
    processorfamily = Reference(processorfamily_id, 'ProcessorFamily.id')


class ArchiveArchSet:
    """See `IArchiveArchSet`."""
    implements(IArchiveArchSet)

    def new(self, archive, processorfamily):
        """See `IArchiveArchSet`."""
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        archivearch = ArchiveArch()
        archivearch.archive = archive
        archivearch.processorfamily = processorfamily
        store.add(archivearch)
        return archivearch

    def getByArchive(self, archive, processorfamily=None):
        """See `IArchiveArchSet`."""
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        base_clauses = (ArchiveArch.archive == archive,)
        if processorfamily is not None:
            optional_clauses = (
                ArchiveArch.processorfamily == processorfamily,)
        else:
            optional_clauses = ()

        results = store.find(
            ArchiveArch, *(base_clauses + optional_clauses))
        results = results.order_by(ArchiveArch.id)

        return results

    def getRestrictedfamilies(self, archive):
        """See `IArchiveArchSet`."""
        store = getUtility(IStoreSelector).get(MAIN_STORE, DEFAULT_FLAVOR)
        origin = (
            ProcessorFamily,
            LeftJoin(
                ArchiveArch,
                ArchiveArch.processorfamily == ProcessorFamily.id))
        result_set = store.using(*origin).find(
            (ProcessorFamily, ArchiveArch),
            (ProcessorFamily.restricted == True))

        return result_set.order_by(ProcessorFamily.name)
