# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = [
    'TranslatorAdminView',
    'TranslatorEditView',
    'TranslatorRemoveView',
    ]

import cgi

from lp.translations.interfaces.translator import (
    ITranslator, IEditTranslator)
from canonical.launchpad.webapp import (
    action, canonical_url, LaunchpadEditFormView, LaunchpadFormView,
    Navigation)
from canonical.launchpad.webapp.breadcrumb import Breadcrumb
from canonical.launchpad.webapp.menu import structured


class TranslatorAdminView(LaunchpadEditFormView):
    """View class to administer ITranslator objects"""

    schema = ITranslator
    field_names = ['language', 'translator', 'style_guide_url']

    @action("Change")
    def change_action(self, action, data):
        """Edit the translator that does translations for a given language."""
        self.updateContextFromData(data)

    def validate(self, data):
        """Don't allow to change the language if it's already in the group."""
        language = data.get('language')
        translation_group = self.context.translationgroup
        existing_translator = translation_group.query_translator(language)
        if (self.context.language != language and
            existing_translator is not None):
            # The language changed but it already exists so we cannot accept
            # this edit.
            existing_translator_link = '<a href="%s">%s</a>' % (
                canonical_url(existing_translator.translator),
                cgi.escape(existing_translator.translator.displayname))

            self.setFieldError('language',
                structured(
                    '%s is already a translator for this language' %
                    existing_translator_link))

    @property
    def label(self):
        """Return form label describing the action one is doing."""
        return "Edit %s translation team in %s" % (
            self.context.language.englishname,
            self.context.translationgroup.title)

    @property
    def page_title(self):
        """Page title for the edit form."""
        return "Edit %s translation team" % self.context.language.englishname

    @property
    def cancel_url(self):
        return canonical_url(self.context.translationgroup,
                             rootsite='translations')

    @property
    def next_url(self):
        return self.cancel_url


class TranslatorEditView(LaunchpadEditFormView):
    """View class to edit ITranslator objects"""

    schema = IEditTranslator

    @action("Set guidelines")
    def change_action(self, action, data):
        """Set the translator guidelines for a given language."""
        self.updateContextFromData(data)

    @property
    def label(self):
        """Return form label describing the action one is doing."""
        return "Set %s guidelines for %s" % (
            self.context.language.englishname,
            self.context.translationgroup.title)

    @property
    def page_title(self):
        """Page title for the edit form."""
        return "Set %s guidelines" % self.context.language.englishname

    @property
    def cancel_url(self):
        return canonical_url(self.context.translator, rootsite='translations')

    @property
    def next_url(self):
        return self.cancel_url


class TranslatorRemoveView(LaunchpadFormView):
    schema = ITranslator
    field_names = []

    @action("Remove")
    def remove(self, action, data):
        """Remove the ITranslator from the associated ITranslationGroup."""
        message = 'Removed %s as the %s translator for %s.' % (
            self.context.translator.displayname,
            self.context.language.englishname,
            self.context.translationgroup.title)
        self.context.translationgroup.remove_translator(self.context)
        self.request.response.addInfoNotification(message)

    @property
    def label(self):
        """Return form label describing the action one is doing."""
        return "Unset '%s' as the %s translator in %s" % (
            self.context.translator.displayname,
            self.context.language.englishname,
            self.context.translationgroup.title)

    @property
    def page_title(self):
        """Page title for the edit form."""
        return "Remove translation team"

    @property
    def cancel_url(self):
        return canonical_url(self.context.translationgroup,
                             rootsite='translations')

    @property
    def next_url(self):
        return self.cancel_url
