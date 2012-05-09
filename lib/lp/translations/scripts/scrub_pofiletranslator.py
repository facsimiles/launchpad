# Copyright 2012 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Keep `POFileTranslator` more or less consistent with the real data."""

__metaclass__ = type
__all__ = [
    'ScrubPOFileTranslator',
    ]

from storm.expr import (
    Coalesce,
    Desc,
    )
import transaction

from lp.services.database.lpstorm import IStore
from lp.services.looptuner import TunableLoop
from lp.translations.model.pofile import POFile
from lp.translations.model.pofiletranslator import POFileTranslator
from lp.translations.model.potemplate import POTemplate
from lp.translations.model.translationmessage import TranslationMessage
from lp.translations.model.translationtemplateitem import (
    TranslationTemplateItem,
    )


def get_pofile_ids():
    """Retrieve ids of POFiles to scrub.

    The result's ordering is aimed at maximizing cache effectiveness:
    by POTemplate name for locality of shared POTMsgSets, and by language
    for locality of shared TranslationMessages.
    """
    store = IStore(POFile)
    query = store.find(
        POFile.id,
        POFile.potemplateID == POTemplate.id,
        POTemplate.iscurrent == True)
    return query.order_by(POTemplate.name, POFile.languageID)


def get_pofile_details(pofile_ids):
    """Retrieve relevant parts of `POFile`s with given ids.

    :param pofile_ids: Iterable of `POFile` ids.
    :return: Dict mapping each id in `pofile_ids` to a duple of
        `POTemplate` id and `Language` id for the associated `POFile`.
    """
    store = IStore(POFile)
    rows = store.find(
        (POFile.id, POFile.potemplateID, POFile.languageID),
        POFile.id.is_in(pofile_ids))
    return dict((row[0], row[1:]) for row in rows)


def get_potmsgset_ids(potemplate_id):
    """Get the ids for each current `POTMsgSet` in a `POTemplate`."""
    store = IStore(POTemplate)
    return store.find(
        TranslationTemplateItem.potmsgsetID,
        TranslationTemplateItem.potemplateID == potemplate_id,
        TranslationTemplateItem.sequence > 0)


def summarize_contributors(potemplate_id, language_id, potmsgset_ids):
    """Return the set of ids of persons who contributed to a `POFile`.

    This is a limited version of `get_contributions` that is easier to
    compute.
    """
    store = IStore(POFile)
    contribs = store.find(
        TranslationMessage.submitterID,
        TranslationMessage.potmsgsetID.is_in(potmsgset_ids),
        TranslationMessage.languageID == language_id,
        TranslationMessage.msgstr0 != None,
        Coalesce(TranslationMessage.potemplateID, potemplate_id) ==
            potemplate_id)
    contribs.config(distinct=True)
    return set(contribs)


def get_contributions(pofile, potmsgset_ids):
    """Map all users' most recent contributions to a `POFile`.

    Returns a dict mapping `Person` id to the creation time of their most
    recent `TranslationMessage` in `POFile`.

    This leaves some small room for error: a contribution that is masked by
    a diverged entry in this POFile will nevertheless produce a
    POFileTranslator record.  Fixing that would complicate the work more than
    it is probably worth.

    :param pofile: The `POFile` to find contributions for.
    :param potmsgset_ids: The ids of the `POTMsgSet`s to look for, as returned
        by `get_potmsgset_ids`.
    """
    store = IStore(pofile)
    language_id = pofile.language.id
    template_id = pofile.potemplate.id
    contribs = store.find(
        (TranslationMessage.submitterID, TranslationMessage.date_created),
        TranslationMessage.potmsgsetID.is_in(potmsgset_ids),
        TranslationMessage.languageID == language_id,
        TranslationMessage.msgstr0 != None,
        Coalesce(TranslationMessage.potemplateID, template_id) ==
            template_id)
    contribs = contribs.config(distinct=(TranslationMessage.submitterID,))
    contribs = contribs.order_by(
        TranslationMessage.submitterID, Desc(TranslationMessage.date_created))
    return dict(contribs)


def get_pofiletranslators(pofile_id):
    """Get `POFileTranslator` entries for a `POFile`.

    Returns a dict mapping each contributor's person id to their
    `POFileTranslator` record.
    """
    store = IStore(POFileTranslator)
    pofts = store.find(
        POFileTranslator, POFileTranslator.pofileID == pofile_id)
    return dict((poft.personID, poft) for poft in pofts)


def remove_pofiletranslators(logger, pofile, person_ids):
    """Delete `POFileTranslator` records."""
    logger.debug(
        "Removing %d POFileTranslator(s) for %s.",
        len(person_ids), pofile.title)
    store = IStore(pofile)
    pofts = store.find(
        POFileTranslator,
        POFileTranslator.pofileID == pofile.id,
        POFileTranslator.personID.is_in(person_ids))
    pofts.remove()


def remove_unwarranted_pofiletranslators(logger, pofile, pofts, contribs):
    """Delete `POFileTranslator` records that shouldn't be there."""
    excess = set(pofts) - set(contribs)
    if len(excess) > 0:
        remove_pofiletranslators(logger, pofile, excess)


def create_missing_pofiletranslators(logger, pofile, pofts, contribs):
    """Create `POFileTranslator` records that were missing."""
    shortage = set(contribs) - set(pofts)
    if len(shortage) == 0:
        return
    logger.debug(
        "Adding %d POFileTranslator(s) for %s.",
        len(shortage), pofile.title)
    store = IStore(pofile)
    for missing_contributor in shortage:
        store.add(POFileTranslator(
            pofile=pofile, personID=missing_contributor,
            date_last_touched=contribs[missing_contributor]))


def fix_pofile(logger, pofile_id, potmsgset_ids, pofiletranslators):
    """This `POFile` needs fixing.  Load its data & fix it."""
    pofile = IStore(POFile).get(POFile, pofile_id)
    contribs = get_contributions(pofile, potmsgset_ids)
    remove_unwarranted_pofiletranslators(
        logger, pofile, pofiletranslators, contribs)
    create_missing_pofiletranslators(
        logger, pofile, pofiletranslators, contribs)


def scrub_pofile(logger, pofile_id, template_id, language_id):
    """Scrub `POFileTranslator` entries for one `POFile`.

    Removes inappropriate entries and adds missing ones.
    """
    pofiletranslators = get_pofiletranslators(pofile_id)
    potmsgset_ids = get_potmsgset_ids(template_id)
    contributors = summarize_contributors(
        template_id, language_id, potmsgset_ids)
    if set(pofiletranslators) != set(contributors):
        fix_pofile(logger, pofile_id, potmsgset_ids, pofiletranslators)


class ScrubPOFileTranslator(TunableLoop):
    """Tunable loop, meant for running from inside Garbo."""

    maximum_chunk_size = 500

    def __init__(self, *args, **kwargs):
        super(ScrubPOFileTranslator, self).__init__(*args, **kwargs)
        self.pofile_ids = tuple(get_pofile_ids())
        self.next_offset = 0

    def __call__(self, chunk_size):
        """See `ITunableLoop`."""
        start_offset = self.next_offset
        self.next_offset = start_offset + int(chunk_size)
        batch = self.pofile_ids[start_offset:self.next_offset]
        if len(batch) == 0:
            self.next_offset = None
            return

        pofile_details = get_pofile_details(batch)
        for pofile_id in batch:
            template_id, language_id = pofile_details[pofile_id]
            scrub_pofile(self.log, pofile_id, template_id, language_id)
        transaction.commit()

    def isDone(self):
        """See `ITunableLoop`."""
        return self.next_offset is None
