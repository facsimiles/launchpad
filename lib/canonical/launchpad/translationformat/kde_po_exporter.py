# Copyright 2007 Canonical Ltd.  All rights reserved.

"""Export module for KDE legacy .po file format.

This is an extension of standard gettext PO files.
You can read more about this file format from:

 * http://l10n.kde.org/docs/translation-howto/gui-peculiarities.html
 * http://docs.kde.org/development/en/kdesdk/kbabel/kbabel-pluralforms.html
 * http://websvn.kde.org/branches/KDE/3.5/kdelibs/kdecore/klocale.cpp
"""

__metaclass__ = type

__all__ = [
    'KdePOExporter'
    ]

from zope.interface import implements

from canonical.launchpad.interfaces import (
    ITranslationFormatExporter, TranslationFileFormat)

from canonical.launchpad.translationformat.gettext_po_exporter import (
    GettextPOExporter)


class KdePOExporter(GettextPOExporter):
    """Support class for exporting legacy KDE .po files."""
    implements(ITranslationFormatExporter)

    msgid_plural_distinguishes_messages = True

    def __init__(self, context=None):
        # See GettextPOExporter.__init__ for explanation of `context`.
        self.format = TranslationFileFormat.KDEPO
        # KdePOExporter is also able to export `TranslationFileFormat.PO`,
        # but there is not much practical use for that, so we are not listing
        # it as one of the supported formats for this exporter.
        self.supported_source_formats = [TranslationFileFormat.KDEPO]

    def exportTranslationMessageData(self, translation_message):
        """See `ITranslationFormatExporter`."""
        # Special handling of context and plural forms.
        if translation_message.context is not None:
            # Let's turn context messages into legacy KDE context.
            translation_message.msgid_singular = u"_: %s\n%s" % (
                translation_message.context,
                translation_message.msgid_singular)
            translation_message.context = None
        elif translation_message.msgid_plural is not None:
            # Also, let's handle legacy KDE plural forms.
            translations = translation_message.translations
            for pluralform_index in xrange(len(translations)):
                if translations[pluralform_index] is None:
                    translations[pluralform_index] = ''
            translation_message._translations = ["\n".join(translations)]
            translation_message.msgid_singular = u"_n: %s\n%s" % (
                translation_message.msgid_singular,
                translation_message.msgid_plural)
            translation_message.msgid_plural = None

        return GettextPOExporter.exportTranslationMessageData(
            self, translation_message)
