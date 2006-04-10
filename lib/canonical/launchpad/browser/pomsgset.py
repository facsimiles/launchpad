# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

__metaclass__ = type
__all__ = [
    'POMsgSetView',
    'POMsgSetURL'
    ]

import re
import gettextpo
from zope.exceptions import NotFoundError
from zope.component import getUtility
from zope.interface import implements

from canonical.cachedproperty import cachedproperty
from canonical.launchpad import helpers
from canonical.launchpad.interfaces import (
    UnexpectedFormData, IPOMsgSet, TranslationConstants, ILanguageSet,
    ICanonicalUrlData)
from canonical.launchpad.webapp import LaunchpadView, canonical_url

class POMsgSetURL:
    implements(ICanonicalUrlData)

    def __init__(self, context):
        self.context = context

    @property
    def path(self):
        pomsgset = self.context
        return '%s/%s' % (
            canonical_url(pomsgset.pofile), str(pomsgset.potmsgset.sequence))

    @property
    def inside(self):
        return self.context.pofile


class POMsgSetView(LaunchpadView):
    """Holds all data needed to show an IPOMsgSet.

    This view class could be used directly or as part of the POFileView class
    in which case, we would have up to 100 instances of this class using the
    same information at self.form.
    """

    __used_for__ = IPOMsgSet

    def initialize(self):
        self.form = self.request.form
        self.potmsgset = self.context.potmsgset
        self.pofile = self.context.pofile
        self.translations = None

        # By default the submitted values are None
        self.form_posted_translations = None
        self.form_posted_needsreview = None
        self.error = None

        # At this point, we don't know the alternative language selected.
        self.second_lang_pofile = None
        self.second_lang_msgset = None

        # We don't know the suggestions either.
        self._wiki_submissions = None
        self._current_submissions = None
        self._suggested_submissions = None
        self._second_language_submissions = None

        # Handle any form submission.
        self.process_form()

    @cachedproperty
    def msgids(self):
        msgids = helpers.shortlist(self.potmsgset.getPOMsgIDs())
        assert len(msgids) > 0, (
            'Found a POTMsgSet without any POMsgIDSighting')
        return msgids

    @property
    def is_plural(self):
        """Return whether there are plural forms."""
        return len(self.msgids) > 1

    @cachedproperty
    def max_lines_count(self):
        """Return the max number of lines a multiline entry will have

        It will never be bigger than 12.
        """
        if self.is_plural:
            singular_lines = helpers.count_lines(
                self.msgids[TranslationConstants.SINGULAR_FORM].msgid)
            plural_lines = helpers.count_lines(
                self.msgids[TranslationConstants.PLURAL_FORM].msgid)
            lines = max(singular_lines, plural_lines)
        else:
            lines = helpers.count_lines(
                self.msgids[TranslationConstants.SINGULAR_FORM].msgid)

        return min(lines, 12)

    @property
    def is_multi_line(self):
        """Return whether the singular or plural msgid have more than one line.
        """
        return self.max_lines_count > 1

    @property
    def sequence(self):
        """Return the position number of this potmsgset."""
        return self.potmsgset.sequence

    @property
    def msgid(self):
        """Return a msgid string prepared to render in a web page."""
        msgid = self.msgids[TranslationConstants.SINGULAR_FORM].msgid
        return helpers.msgid_html(msgid, self.potmsgset.flags())

    @property
    def msgid_plural(self):
        """Return a msgid plural string prepared to render as a web page.

        If there is no plural form, return None.
        """
        if self.is_plural:
            msgid = self.msgids[TranslationConstants.PLURAL_FORM].msgid
            return helpers.msgid_html(msgid, self.potmsgset.flags())
        else:
            return None

    @property
    def msgid_has_tab(self):
        """Return whether there are a msgid with a '\t' char."""
        for msgid in self.msgids:
            if '\t' in msgid.msgid:
                return True
        return False

    @property
    def source_comment(self):
        """Return the source code comments for this IPOMsgSet."""
        return self.potmsgset.sourcecomment

    @property
    def comment(self):
        """Return the translator comments for this IPOMsgSet."""
        return self.context.commenttext

    @property
    def file_references(self):
        """Return the file references for this IPOMsgSet."""
        return self.potmsgset.filereferences

    @property
    def translation_range(self):
        """Return a list with all indexes we have to get translations."""
        self._prepare_translations()
        return range(len(self.translations))

    @property
    def is_fuzzy(self):
        """Return whether this pomsgset is set as fuzzy."""
        if self.form_posted_needsreview is not None:
            return self.form_posted_needsreview
        else:
            return self.context.isfuzzy

    @property
    def lacks_plural_form_information(self):
        """Return whether we know the plural forms for this language."""
        if self.context.pofile.potemplate.hasPluralMessage():
            # If there are no plural forms, we don't mind if we have or not
            # the plural form information.
            return self.context.pofile.language.pluralforms is None
        else:
            return False

    @property
    def second_lang_code(self):
        second_lang_code = self.form.get('alt', '')
        if (second_lang_code == '' and
            self.context.pofile.language.alt_suggestion_language is not None):
            return self.context.pofile.language.alt_suggestion_language.code
        elif second_lang_code == '':
            return None
        else:
            return second_lang_code

    @property
    def is_at_beginning(self):
        """Return whether we are at the beginning of the form."""
        return self.context.potmsgset.sequence == 0

    @property
    def is_at_end(self):
        """Return whether we are at the end of the form."""
        potmsgset = self.context.potmsgset
        return potmsgset.sequence == len(potmsgset.potemplate)

    @property
    def beginning_URL(self):
        """Return the URL to be at the beginning of the translation form."""
        return self.createURL(sequence=1)

    @property
    def end_URL(self):
        """Return the URL to be at the end of the translation form."""
        number_msgsets = len(self.context.potmsgset.potemplate)
        return self.createURL(sequence=number_msgsets)

    @property
    def previous_URL(self):
        """Return the URL to get previous self.count number of message sets.
        """
        if self.context.potmsgset.sequence > 1:
            return self.createURL(self.context.potmsgset.sequence)
        else:
            # We don't have more entries before this one, return always the
            # first entry.
            return self.createURL(1)

    @property
    def next_URL(self):
        """Return the URL to get next self.count number of message sets."""
        number_msgsets = len(self.context.potmsgset.potemplate)
        current_msgset = self.context.potmsgset.sequence
        assert (current_msgset + 1 < number_msgsets), (
            'Only have %d messages, requested %d' % (
                number_msgsets, current_msgset + 1))

        return self.createURL(sequence=current_msgset + 1)

    def createURL(self, sequence=None):
        """Build the current URL."""
        if sequence is None:
            # We don't change the IPOMsgSet.
            url = canonical_url(self.context)
        else:
            assert sequence > 0, ("%r is not a valid sequence number." % name)

            potmsgset = self.potmsgset.potemplate.getPOTMsgSetBySequence(
                sequence)
            pomsgset = potmsgset.getPOMsgSet(
                self.context.pofile.language.code,
                self.context.pofile.variant)
            url = canonical_url(pomsgset)

        if self.second_lang_code is None:
            return url
        else:
            query = urllib.urlencode({'alt': self.second_lang_code})
            return '%s?%s' % (url, query)

    def _prepare_translations(self):
        """Prepare self.translations to be used."""
        if self.translations is not None:
            # We have already the translations prepared.
            return

        if self.form_posted_translations is None:
            self.form_posted_translations = {}

        # Fill the list of translations based on the input the user
        # submitted.
        form_posted_translations_keys = self.form_posted_translations.keys()
        form_posted_translations_keys.sort()
        self.translations = [
            self.form_posted_translations[form_posted_translations_key]
            for form_posted_translations_key in form_posted_translations_keys]

        if not self.translations:
            # We didn't get any translation from the website.
            self.translations = self.context.active_texts

    def getTranslation(self, index):
        """Return the active translation for the pluralform 'index'.

        There are as many translations as the plural form information defines
        for that language/pofile. If one of those translations does not
        exists, it will have a None value. If the potmsgset is not a plural
        form one, we only have one entry.
        """
        self._prepare_translations()

        if index in self.translation_range:
            translation = self.translations[index]
            # We store newlines as '\n', '\r' or '\r\n', depending on the
            # msgid but forms should have them as '\r\n' so we need to change
            # them before showing them.
            if translation is not None:
                return helpers.convert_newlines_to_web_form(translation)
            else:
                return None
        else:
            raise IndexError('Translation out of range')

    def lang_selector(self):
        second_lang_code = self.second_lang_code
        langset = getUtility(ILanguageSet)
        html = ('<select name="alt" title="Make suggestions from...">\n'
                '<option value=""')
        if self.second_lang_pofile is None:
            html += ' selected="yes"'
        html += '></option>\n'
        for lang in langset.common_languages:
            html += '<option value="' + lang.code + '"'
            if second_lang_code == lang.code:
                html += ' selected="yes"'
            html += '>' + lang.englishname + '</option>\n'
        html += '</select>\n'
        return html

    def set_second_lang_pofile(self, second_lang_pofile):
        """Store the selected second_lang_pofile reference.

        :second_lang_pofile: Is an IPOFile pointing to the language chosen by
            the user as the second language to see translations from.
        """
        self.second_lang_pofile = second_lang_pofile

        if self.second_lang_pofile:
            msgid_text = self.potmsgset.primemsgid_.msgid
            try:
                self.second_lang_msgset = (
                    second_lang_pofile[msgid_text]
                    )
            except NotFoundError:
                # The second language doesn't have this message ID.
                self.second_lang_msgset = None

        # Force a refresh of self._second_language_submissions
        self._second_language_submissions = None


    # The three functions below are tied to the UI policy. In essence, they
    # will present up to three proposed translations from each of the
    # following categories in order:
    #
    #   - new submissions to this pofile by people who don't have permission
    #     to write here
    #   - items actually published or currently active elsewhere
    #   - new submissions to ANY similar pofile for the same msgset from
    #     people who did not have write permission THERE
    def get_wiki_submissions(self, index):
        # the UI expects these to come after suggested and current, and will
        # present at most three of them
        if self._wiki_submissions is not None:
            return self._wiki_submissions
        curr = self.getTranslation(index)

        wiki = self.context.getWikiSubmissions(index)
        suggested = self.get_suggested_submissions(index)
        suggested_texts = [s.potranslation.translation
                           for s in suggested]
        current = self.get_current_submissions(index)
        current_texts = [c.potranslation.translation
                         for c in current]
        self._wiki_submissions = [submission for submission in wiki
            if submission.potranslation.translation != curr and
            submission.potranslation.translation not in suggested_texts and
            submission.potranslation.translation not in current_texts][:3]
        return self._wiki_submissions

    def get_current_submissions(self, index):
        # the ui expectes these after the suggested ones and will show at
        # most 3 of them
        if self._current_submissions is not None:
            return self._current_submissions
        curr = self.getTranslation(index)

        current = self.context.getCurrentSubmissions(index)
        suggested = self.get_suggested_submissions(index)
        suggested_texts = [s.potranslation.translation
                           for s in suggested]
        self._current_submissions = [submission
            for submission in current 
            if submission.potranslation.translation != curr and
            submission.potranslation.translation not in suggested_texts][:3]
        return self._current_submissions

    def get_suggested_submissions(self, index):
        # these are expected to be shown first, we will show at most 3 of
        # them
        if self._suggested_submissions is not None:
            return self._suggested_submissions

        sugg = self.context.getSuggestedSubmissions(index)
        self._suggested_submissions = helpers.shortlist(sugg[:3])
        return self._suggested_submissions

    def get_alternate_language_submissions(self, index):
        """Get suggestions for translations from the alternate language for
        this potemplate."""
        if self._second_language_submissions is not None:
            return self._second_language_submissions
        if self.second_lang_msgset is None:
            return []
        sec_lang = self.second_lang_pofile.language
        sec_lang_potmsgset = self.second_lang_msgset.potmsgset
        curr = sec_lang_potmsgset.getCurrentSubmissions(sec_lang, index)
        self._second_language_submissions = curr[:3]
        return self._second_language_submissions

    def process_form(self):
        """Check whether the form was submitted and calls the right callback.
        """
        if (self.request.method != 'POST' or self.user is None or
            'pofile_translation_filter' in self.form):
            # The form was not submitted or the user is not logged in.
            # If we get 'pofile_translation_filter' we should ignore that POST
            # because it's useless for this view.
            return

        dispatch_table = {
            'submit_translations': self._submit_translations
            }
        dispatch_to = [(key, method)
                        for key,method in dispatch_table.items()
                        if key in self.form
                      ]
        if len(dispatch_to) != 1:
            raise UnexpectedFormData(
                "There should be only one command in the form",
                dispatch_to)
        key, method = dispatch_to[0]
        method()

    def _extract_form_posted_translations(self):
        """Parse the form submitted to the translation widget looking for
        translations.

        Store the new translations at self.form_posted_translations and its
        status at self.form_posted_needsreview.

        In this method, we look for various keys in the form, and use them as
        follows:

        - 'msgset_ID' to know if self is part of the submitted form. If it
          isn't found, we stop parsing the form and return.
        - 'msgset_ID_LANGCODE_translation_PLURALFORM': Those will be the
          submitted translations and we will have as many entries as plural
          forms the language self.context.language has.
        - 'msgset_ID_LANGCODE_needsreview': If present, will note that the
          'needs review' flag has been set for the given translations.

        In all those form keys, 'ID' is self.potmsgset.id.
        """
        msgset_ID = 'msgset_%d' % self.potmsgset.id
        msgset_ID_LANGCODE_needsreview = 'msgset_%d_%s_needsreview' % (
            self.potmsgset.id, self.pofile.language.code)

        # We will add the plural form number later.
        msgset_ID_LANGCODE_translation_ = 'msgset_%d_%s_translation_' % (
            self.potmsgset.id, self.pofile.language.code)

        # If this form does not have data about the msgset id, then do nothing
        # at all.
        if msgset_ID not in self.form:
            return

        self.form_posted_translations = {}

        self.form_posted_needsreview = (
            msgset_ID_LANGCODE_needsreview in self.form)

        # Extract the translations from the form, and store them in
        # self.form_posted_translations .

        # There will never be 100 plural forms.  Usually, we'll be iterating
        # over just two or three.
        # We try plural forms in turn, starting at 0, and leave the loop as
        # soon as we don't find a translation for a plural form.
        for pluralform in xrange(100):
            msgset_ID_LANGCODE_translation_PLURALFORM = '%s%s' % (
                msgset_ID_LANGCODE_translation_, pluralform)
            if msgset_ID_LANGCODE_translation_PLURALFORM not in self.form:
                break
            value = self.form[msgset_ID_LANGCODE_translation_PLURALFORM]
            self.form_posted_translations[pluralform] = (
                helpers.contract_rosetta_tabs(value))
        else:
            raise AssertionError("There were more than 100 plural forms!")

    def _submit_translations(self):
        """Handle a form submission for the translation form.

        The form contains translations, some of which will be unchanged, some
        of which will be modified versions of old translations and some of
        which will be new. Returns a dictionary mapping sequence numbers to
        submitted message sets, where each message set will have information
        on any validation errors it has.
        """
        # Extract the values from the form and set self.form_posted_translations
        # and self.form_posted_needsreview.
        self._extract_form_posted_translations()

        if self.form_posted_translations is None:
            # There are not translations interesting for us.
            return

        has_translations = False
        for form_posted_translation_key in self.form_posted_translations.keys():
            if self.form_posted_translations[form_posted_translation_key] != '':
                has_translations = True
                break

        if has_translations and not self.form_posted_needsreview:
            # The submit has translations to validate and are not set as
            # needs review.

            msgids_text = [pomsgid.msgid
                           for pomsgid in self.potmsgset.getPOMsgIDs()]

            # Validate the translation we got from the translation form
            # to know if gettext is happy with the input.
            try:
                helpers.validate_translation(msgids_text,
                                             self.form_posted_translations,
                                             self.potmsgset.flags())
            except gettextpo.error, e:
                # Save the error message gettext gave us to show it to the
                # user and jump to the next entry so this messageSet is
                # not stored into the database.
                self.error = str(e)
                return

        try:
            self.context.updateTranslationSet(
                person=self.user,
                new_translations=self.form_posted_translations,
                fuzzy=self.form_posted_needsreview,
                published=False)
        except gettextpo.error, e:
            # Save the error message gettext gave us to show it to the
            # user.
            self.error = str(e)
