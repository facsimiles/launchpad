# Copyright 2012 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Keep `POFileTranslator` more or less consistent with the real data."""

__all__ = [
    "ScrubPOFileTranslator",
]

from collections import namedtuple

import transaction
from storm.expr import Coalesce, Desc

from lp.registry.model.distribution import Distribution
from lp.registry.model.distroseries import DistroSeries
from lp.registry.model.product import Product
from lp.registry.model.productseries import ProductSeries
from lp.services.database.bulk import load, load_related
from lp.services.database.interfaces import IStore
from lp.services.looptuner import TunableLoop
from lp.services.worlddata.model.language import Language
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
        POFile.potemplate_id == POTemplate.id,
        POTemplate.iscurrent == True,
    )
    return query.order_by(POTemplate.name, POFile.language_id)


def summarize_pofiles(pofile_ids):
    """Retrieve relevant parts of `POFile`s with given ids.

    This gets just enough information to determine whether any of the
    `POFile`s need their `POFileTranslator` records fixed.

    :param pofile_ids: Iterable of `POFile` ids.
    :return: Dict mapping each id in `pofile_ids` to a duple of
        `POTemplate` id and `Language` id for the associated `POFile`.
    """
    store = IStore(POFile)
    rows = store.find(
        (POFile.id, POFile.potemplate_id, POFile.language_id),
        POFile.id.is_in(pofile_ids),
    )
    return {row[0]: row[1:] for row in rows}


def get_potmsgset_ids(potemplate_id):
    """Get the ids for each current `POTMsgSet` in a `POTemplate`."""
    store = IStore(POTemplate)
    return set(
        store.find(
            TranslationTemplateItem.potmsgset_id,
            TranslationTemplateItem.potemplate_id == potemplate_id,
            TranslationTemplateItem.sequence > 0,
        )
    )


def summarize_contributors(potemplate_id, language_ids, potmsgset_ids):
    """Return per-language sets of person ids who contributed to a `POFile`.

    This is a limited version of `get_contributions` that is easier to
    compute.
    """
    store = IStore(POFile)
    contribs = {language_id: set() for language_id in language_ids}
    for language_id, submitter_id in store.find(
        (TranslationMessage.language_id, TranslationMessage.submitter_id),
        TranslationMessage.potmsgset_id.is_in(potmsgset_ids),
        TranslationMessage.language_id.is_in(language_ids),
        TranslationMessage.msgstr0 != None,
        Coalesce(TranslationMessage.potemplate_id, potemplate_id)
        == potemplate_id,
    ).config(distinct=True):
        contribs[language_id].add(submitter_id)
    return contribs


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
        (TranslationMessage.submitter_id, TranslationMessage.date_created),
        TranslationMessage.potmsgset_id.is_in(potmsgset_ids),
        TranslationMessage.language_id == language_id,
        TranslationMessage.msgstr0 != None,
        Coalesce(TranslationMessage.potemplate_id, template_id) == template_id,
    )
    contribs = contribs.config(distinct=(TranslationMessage.submitter_id,))
    contribs = contribs.order_by(
        TranslationMessage.submitter_id, Desc(TranslationMessage.date_created)
    )
    return dict(contribs)


def get_pofiletranslators(pofile_ids):
    """Get `Person` ids from `POFileTranslator` entries for a set of `POFile`s.

    Returns a mapping of `POFile` IDs to `set`s of `Person` ids.
    """
    store = IStore(POFileTranslator)
    pofts = {pofile_id: set() for pofile_id in pofile_ids}
    for pofile_id, person_id in store.find(
        (POFileTranslator.pofile_id, POFileTranslator.person_id),
        POFileTranslator.pofile_id.is_in(pofile_ids),
    ):
        pofts[pofile_id].add(person_id)
    return pofts


def remove_pofiletranslators(logger, pofile, person_ids):
    """Delete `POFileTranslator` records."""
    logger.debug(
        "Removing %d POFileTranslator(s) for %s.",
        len(person_ids),
        pofile.title,
    )
    store = IStore(pofile)
    pofts = store.find(
        POFileTranslator,
        POFileTranslator.pofile == pofile,
        POFileTranslator.person_id.is_in(person_ids),
    )
    pofts.remove()


def remove_unwarranted_pofiletranslators(logger, pofile, pofts, contribs):
    """Delete `POFileTranslator` records that shouldn't be there."""
    excess = pofts - set(contribs)
    if len(excess) > 0:
        remove_pofiletranslators(logger, pofile, excess)


def create_missing_pofiletranslators(logger, pofile, pofts, contribs):
    """Create `POFileTranslator` records that were missing."""
    shortage = set(contribs) - pofts
    if len(shortage) == 0:
        return
    logger.debug(
        "Adding %d POFileTranslator(s) for %s.", len(shortage), pofile.title
    )
    store = IStore(pofile)
    for missing_contributor in shortage:
        store.add(
            POFileTranslator(
                pofile=pofile,
                person_id=missing_contributor,
                date_last_touched=contribs[missing_contributor],
            )
        )


def fix_pofile(logger, pofile, potmsgset_ids, pofiletranslators):
    """This `POFile` needs fixing.  Load its data & fix it."""
    contribs = get_contributions(pofile, potmsgset_ids)
    remove_unwarranted_pofiletranslators(
        logger, pofile, pofiletranslators, contribs
    )
    create_missing_pofiletranslators(
        logger, pofile, pofiletranslators, contribs
    )


# A tuple describing a POFile that needs its POFileTranslators fixed.
WorkItem = namedtuple(
    "WorkItem",
    [
        "pofile_id",
        "potmsgset_ids",
        "pofiletranslators",
    ],
)


def gather_work_items(pofile_ids):
    """Produce `WorkItem`s for those `POFile`s that need fixing.

    :param pofile_ids: An iterable of `POFile` ids to check.
    :param pofile_summaries: Dict as returned by `summarize_pofiles`.
    :return: A sequence of `WorkItem`s for those `POFile`s that need fixing.
    """
    pofile_summaries = summarize_pofiles(pofile_ids)
    cached_potmsgsets = {}
    cached_contributors = {}
    cached_pofts = get_pofiletranslators(pofile_ids)
    work_items = []
    for pofile_id in pofile_ids:
        template_id, language_id = pofile_summaries[pofile_id]
        if template_id not in cached_potmsgsets:
            cached_potmsgsets[template_id] = get_potmsgset_ids(template_id)
        potmsgset_ids = cached_potmsgsets[template_id]
        if template_id not in cached_contributors:
            all_language_ids = [
                lang_id
                for temp_id, lang_id in pofile_summaries.values()
                if temp_id == template_id
            ]
            cached_contributors[template_id] = summarize_contributors(
                template_id, all_language_ids, potmsgset_ids
            )
        contributor_ids = cached_contributors[template_id][language_id]
        pofts = cached_pofts[pofile_id]
        # Does this `POFile` need `POFileTranslator` changes?
        if pofts != contributor_ids:
            work_items.append(WorkItem(pofile_id, potmsgset_ids, pofts))

    return work_items


def preload_work_items(work_items):
    """Bulk load data that will be needed to process `work_items`.

    :param work_items: A sequence of `WorkItem` records.
    :return: A dict mapping `POFile` ids from `work_items` to their
        respective `POFile` objects.
    """
    pofiles = load(POFile, [work_item.pofile_id for work_item in work_items])
    load_related(Language, pofiles, ["language_id"])
    templates = load_related(POTemplate, pofiles, ["potemplate_id"])
    distroseries = load_related(DistroSeries, templates, ["distroseries_id"])
    load_related(Distribution, distroseries, ["distribution_id"])
    productseries = load_related(
        ProductSeries, templates, ["productseries_id"]
    )
    load_related(Product, productseries, ["product_id"])
    return {pofile.id: pofile for pofile in pofiles}


def process_work_items(logger, work_items, pofiles):
    """Fix the `POFileTranslator` records covered by `work_items`."""
    for work_item in work_items:
        pofile = pofiles[work_item.pofile_id]
        fix_pofile(
            logger,
            pofile,
            work_item.potmsgset_ids,
            work_item.pofiletranslators,
        )


class ScrubPOFileTranslator(TunableLoop):
    """Tunable loop, meant for running from inside Garbo."""

    maximum_chunk_size = 2500

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pofile_ids = tuple(get_pofile_ids())
        self.log.info(
            f"[ScrubPOFileTranslator] Found {len(self.pofile_ids)} "
            "PO Files to process."
        )
        self.next_offset = 0

    def __call__(self, chunk_size):
        """See `ITunableLoop`."""
        start_offset = self.next_offset
        self.next_offset = start_offset + int(chunk_size)
        batch = self.pofile_ids[start_offset : self.next_offset]
        if len(batch) == 0:
            self.next_offset = None
        else:
            work_items = gather_work_items(batch)
            pofiles = preload_work_items(work_items)
            process_work_items(self.log, work_items, pofiles)
            transaction.commit()

    def isDone(self):
        """See `ITunableLoop`."""
        return self.next_offset is None
