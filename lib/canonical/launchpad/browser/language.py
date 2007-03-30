# Copyright 2007 Canonical Ltd.  All rights reserved.

"""Browser code for Language table."""

__metaclass__ = type
__all__ = [
    'LanguageAddView',
    'LanguageContextMenu',
    'LanguageAdminView',
    'LanguageNavigation',
    'LanguageRemoveView',
    'LanguageSetContextMenu',
    'LanguageSetNavigation',
    'LanguageSetView',
    'LanguageView',
    ]

import operator

from zope.app.event.objectevent import ObjectCreatedEvent
from zope.component import getUtility
from zope.event import notify

from canonical.cachedproperty import cachedproperty
from canonical.launchpad.browser.launchpad import RosettaContextMenu
from canonical.launchpad.interfaces import (
    ILanguageSet, ILanguage, NotFoundError)
from canonical.launchpad.webapp import (
    GetitemNavigation, LaunchpadView, LaunchpadFormView,
    LaunchpadEditFormView, action, canonical_url)


class LanguageNavigation(GetitemNavigation):
    usedfor = ILanguage

    def traverse(self, name):
        raise NotFoundError


class LanguageSetNavigation(GetitemNavigation):
    usedfor = ILanguageSet


class LanguageSetContextMenu(RosettaContextMenu):
    usedfor = ILanguageSet


class LanguageContextMenu(RosettaContextMenu):
    usedfor = ILanguage


class LanguageSetView:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        form = self.request.form
        self.text = form.get('text')
        self.searchrequested = self.text is not None
        self.results = None
        self.matches = 0

    def searchresults(self):
        if self.results is None:
            self.results = self.context.search(text=self.text)
        if self.results is not None:
            self.matches = self.results.count()
        else:
            self.matches = 0
        return self.results


class LanguageAddView(LaunchpadFormView):

    schema = ILanguage
    field_names = ['code', 'englishname', 'nativename', 'pluralforms',
                   'pluralexpression', 'visible', 'direction']
    label = _('Register a language in Launchpad')
    language = None

    @action(_('Add'), name='add')
    def add_action(self, action, data):
        """Create the new Language from the form details."""
        self.language = getUtility(ILanguageSet).createLanguage(
            code=data['code'],
            englishname=data['englishname'],
            nativename=data['nativename'],
            pluralforms=data['pluralforms'],
            pluralexpression=data['pluralexpression'],
            visible=data['visible'],
            direction=data['direction'])
        notify(ObjectCreatedEvent(self.language))

    @property
    def next_url(self):
        assert self.language is not None, 'No language has been created'
        return canonical_url(self.language)


class LanguageView(LaunchpadView):

    @cachedproperty
    def language_name(self):
        if self.context.nativename is None:
            return self.context.englishname
        else:
            return self.context.nativename

    @cachedproperty
    def translation_teams(self):
        return []

    def getTopFiveContributors(self):
        return []


class LanguageRemoveView:

    def removals(self):
        pass

class LanguageAdminView(LaunchpadEditFormView):
    """Handle and admin form submission."""
    schema = ILanguage

    field_names = ['code', 'englishname', 'nativename', 'pluralforms',
                   'pluralexpression', 'visible', 'direction']

    @action("Admin Language", name="admin")
    def admin_action(self, action, data):
        self.updateContextFromData(data)

