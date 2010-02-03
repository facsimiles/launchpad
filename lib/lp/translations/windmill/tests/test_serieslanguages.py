# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for series languages."""

__metaclass__ = type
__all__ = []

from windmill.authoring import WindmillTestClient

from canonical.launchpad.windmill.testing.constants import (
    PAGE_LOAD, SLEEP)
from canonical.launchpad.windmill.testing import lpuser
from lp.translations.windmill.testing import TranslationsWindmillLayer
from lp.testing import TestCaseWithFactory

LANGUAGE=(u"//table[@id='languagestats']/descendant::a[text()='%s']"
         u"/parent::td/parent::tr")
UNSEEN_VALIDATOR='className|unseen'


class LanguagesSeriesTest(TestCaseWithFactory):
    """Tests for serieslanguages."""

    layer = TranslationsWindmillLayer

    def _toggle_languages_visiblity(self):
        self.client.click(id="toggle-languages-visibility")
        self.client.waits.sleep(milliseconds=SLEEP)

    def _assert_languages_visible(self, languages):
        for language, visibility in languages.items():
            xpath = LANGUAGE % language
            if visibility:
                self.client.asserts.assertNotProperty(
                    xpath=xpath, validator=UNSEEN_VALIDATOR)
            else:
                self.client.asserts.assertProperty(
                    xpath=xpath, validator=UNSEEN_VALIDATOR)

    def test_serieslanguages_table(self):
        """Test for filtering preferred languages in serieslanguages table.

        The test cannot fully cover all languages so we just test with a
        person having Catalan and Spanish as preferred languages.
        """
        self.client = WindmillTestClient('SeriesLanguages Tables')
        lpuser.TRANSLATIONS_ADMIN.ensure_login(self.client)
        start_url = 'http://translations.launchpad.dev:8085/ubuntu'
        # Go to the distribution languages page
        self.client.open(url=start_url)
        self.client.waits.forPageLoad(timeout=PAGE_LOAD)

        # A link will be displayed for viewing all languages
        # and only user preferred langauges are displayed
        self.client.asserts.assertProperty(
            id=u'toggle-languages-visibility',
            validator='text|View all languages')
        self._assert_languages_visible({
            u'Catalan': True,
            u'Spanish': True,
            u'French': False,
            u'Croatian': False,
            })

        # Toggle language visibility by clicking the toggle link.
        self._toggle_languages_visiblity()
        self.client.asserts.assertProperty(
            id=u'toggle-languages-visibility',
            validator='text|View only preferred languages')
        # All languages should be visible now
        self._assert_languages_visible({
            u'Catalan': True,
            u'Spanish': True,
            u'French': True,
            u'Croatian': True,
            })

