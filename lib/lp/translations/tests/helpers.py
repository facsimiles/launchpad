# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    'get_all_important_translations',
    'make_translationmessage',
    'make_translationmessage_for_context',
    ]

from zope.security.proxy import removeSecurityProxy

from canonical.database.sqlbase import sqlvalues

from lp.translations.interfaces.translationmessage import (
    RosettaTranslationOrigin,
    TranslationValidationStatus)
from lp.translations.model.translationmessage import (
    TranslationMessage)

def make_translationmessage_for_context(factory, pofile, potmsgset=None,
                                        current=True, other=False,
                                        diverged=False, translations=None):
    """A low-level way of constructing TMs appropriate to `pofile` context."""
    assert pofile is not None, "You must pass in an existing POFile."

    potemplate = pofile.potemplate
    if potemplate.distroseries is not None:
        ubuntu = current
        upstream = other
    else:
        ubuntu = other
        upstream = current
    return make_translationmessage(
        factory, pofile, potmsgset, ubuntu, upstream, diverged, translations)

def make_translationmessage(factory, pofile=None, potmsgset=None,
                            ubuntu=True, upstream=True,
                            diverged=False, translations=None):
    """Creates a TranslationMessage directly and sets relevant parameters.

    This is very low level function used to test core Rosetta
    functionality such as setCurrentTranslation() method.  If not used
    correctly, it will trigger unique constraints.
    """
    if pofile is None:
        pofile = factory.makePOFile('sr')
    if potmsgset is None:
        potmsgset = factory.makePOTMsgSet(
            potemplate=pofile.potemplate)
    if translations is None:
        translations = [factory.getUniqueString()]
    if diverged:
        potemplate = pofile.potemplate
    else:
        potemplate = None

    # Parameters we don't care about are origin, submitter and
    # validation_status.
    origin = RosettaTranslationOrigin.SCM
    submitter = pofile.owner
    validation_status = TranslationValidationStatus.UNKNOWN

    potranslations = removeSecurityProxy(
        potmsgset)._findPOTranslations(translations)
    new_message = TranslationMessage(
        potmsgset=potmsgset,
        potemplate=potemplate,
        pofile=None,
        language=pofile.language,
        variant=pofile.variant,
        origin=origin,
        submitter=submitter,
        msgstr0=potranslations[0],
        msgstr1=potranslations[1],
        msgstr2=potranslations[2],
        msgstr3=potranslations[3],
        msgstr4=potranslations[4],
        msgstr5=potranslations[5],
        validation_status=validation_status,
        is_current_ubuntu=ubuntu,
        is_current_upstream=upstream)
    return new_message

def get_all_translations_current_anywhere(pofile, potmsgset):
    """Get all translation messages on this POTMsgSet used anywhere."""
    used_clause = ('(is_current_ubuntu IS TRUE OR '
                   'is_current_upstream IS TRUE)')
    template_clause = 'TranslationMessage.potemplate IS NOT NULL'
    clauses = [
        'potmsgset = %s' % sqlvalues(potmsgset),
        used_clause,
        template_clause,
        'TranslationMessage.language = %s' % sqlvalues(pofile.language)]
    if pofile.variant is None:
        clauses.append('TranslationMessage.variant IS NULL')
    else:
        clauses.append(
            'TranslationMessage.variant=%s' % sqlvalues(pofile.variant))

    order_by = '-COALESCE(potemplate, -1)'

    return TranslationMessage.select(
        ' AND '.join(clauses), orderBy=[order_by])

def get_all_important_translations(pofile, potmsgset):
    """Return all existing current translations.

    Returns a tuple containing 4 elements:
     * current, shared translation for `potmsgset`.
     * diverged translation for `potmsgset` in `pofile` or None.
     * shared translation for `potmsgset` in "other" context.
     * list of all other diverged translations (not including the one
       diverged in `pofile`) or an empty list if there are none.
    """
    current_shared = potmsgset.getCurrentTranslationMessage(
        None, pofile.language, pofile.variant)
    current_diverged = potmsgset.getCurrentTranslationMessage(
        pofile.potemplate, pofile.language, pofile.variant)
    if (current_diverged is not None and
        current_diverged.potemplate is None):
        current_diverged = None

    other_shared = potmsgset.getImportedTranslationMessage(
        None, pofile.language, pofile.variant)
    other_diverged = potmsgset.getImportedTranslationMessage(
        pofile.potemplate, pofile.language, pofile.variant)
    assert other_diverged is None or other_diverged.potemplate is None, (
        "There is a diverged 'other' translation for "
        "this same template, which isn't impossible.")

    all_used = get_all_translations_current_anywhere(
        pofile, potmsgset)
    diverged = []
    for suggestion in all_used:
        if ((suggestion.potemplate is not None and
             suggestion.potemplate != pofile.potemplate) and
            (suggestion.is_current_ubuntu or
             suggestion.is_current_upstream)):
            # It's diverged for another template and current somewhere.
            diverged.append(suggestion)
    return (
        current_shared, current_diverged,
        other_shared, diverged)
