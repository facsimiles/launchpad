# Copyright 2006-2007 Canonical Ltd.  All rights reserved.

__metaclass__ = type

__all__ = [
    'KdePOImporter'
    ]

from zope.interface import implements

from canonical.launchpad.interfaces import ITranslationFormatImporter
from canonical.launchpad.translationformat.gettext_po_parser import POParser
from canonical.launchpad.translationformat.gettext_po_importer import (
    GettextPOImporter)
from canonical.lp.dbschema import TranslationFileFormat


class KdePOImporter(GettextPOImporter):
    """Support class to import KDE .po files."""
    implements(ITranslationFormatImporter)

    def format(self, content):
        """See `ITranslationFormatImporter`."""
        # XXX DaniloSegan 20070904: I first tried using POParser()
        # to check if the file is a legacy KDE PO file or not, but
        # that is too slow in some cases like tarball uploads (processing
        # of all PO files in a tarball is done in the same transaction,
        # and with extremely big PO files, this will be too slow).  Thus,
        # a heuristic verified to be correct on all PO files from
        # Ubuntu language packs.
        if ("""msgid "_n: """ in content or
            """msgid ""\n"_n: """ in content or
            """msgid "_: """ in content or
            """msgid ""\n"_: """ in content):
            return TranslationFileFormat.KDEPO
        return TranslationFileFormat.PO

    @property
    def content_type(self):
        """See `ITranslationFormatImporter`."""
        return 'application/x-po'

    def parse(self, translation_import_queue_entry):
        """See `ITranslationFormatImporter`."""
        translation_file = GettextPOImporter.parse(
            self, translation_import_queue_entry)

        for message in translation_file.messages:
            msgid = message.msgid
            if msgid.lower().startswith('_n: ') and '\n' in msgid:
                # This is a KDE plural form
                singular, plural = msgid[4:].split('\n')

                message.msgid = singular
                message.msgid_plural = plural
                msgstrs = message._translations
                if len(msgstrs)>0:
                    message._translations = msgstrs[0].split('\n')

                self.internal_format = TranslationFileFormat.KDEPO
            elif msgid.lower().startswith('_: ') and '\n' in msgid:
                # This is a KDE context message
                message.context, message.msgid = msgid[3:].split('\n')
                self.internal_format = TranslationFileFormat.KDEPO
            else:
                # Other messages are left as they are parsed by
                # GettextPOImporter
                pass

        return translation_file
