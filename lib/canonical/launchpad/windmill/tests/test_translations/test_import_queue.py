# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Test for translation import queue behaviour."""

__metaclass__ = type
__all__ = []

# Generated by the windmill services transformer
from windmill.authoring import WindmillTestClient

from canonical.launchpad.windmill.testing import lpuser

class ImportQueueEntryTest:
    """Test that the entries in the import queue can switch types."""

    def __init__(self, name=None,
                 url='http://translations.launchpad.dev:8085/+imports/1',
                 suite='translations', user=lpuser.TRANSLATIONS_ADMIN):
        """Create a new ImportQueueEntryTest.

        :param name: Name of the test.
        :param url: Start at, default http://translation.launchpad.net:8085.
        :param suite: The suite in which this test is part of.
        :param user: The user who should be logged in.
        """
        self.url = url
        if name is None:
            self.__name__ = 'test_%s_import_queue_entry' % suite
        else:
            self.__name__ = name
        self.suite = suite
        self.user = user

    def __call__(self):
        """Tests that documentation links are shown/hidden properly.

        The test:
        * sets translation instructions link for a translation group;
        * opens a Spanish translation page;
        * tries hiding the notification box;
        * makes sure it's hidden when you stay on the same translation;
        * makes sure it's shown again when you go to a different translation.
        """
        client = WindmillTestClient(self.suite)

        # Go to import queue page logged in as translations admin.
        self.user.ensure_login(client)
        client.open(url=self.url)
        client.waits.forPageLoad(timeout=u'20000')

        # When the page is first called tha file_type is set to POT and
        # only the relevant form fields are displayed. When the file type
        # select box is changed to PO, other fields are shown hidden while
        # the first ones are hidden. Finally, all fields are hidden if the
        # file type is unspecified.
        client.waits.forElement(id=u'field.file_type', timeout=u'8000')
        client.asserts.assertSelected(id=u'field.file_type', validator=u'POT')
        client.asserts.assertProperty(classname="POT_row",
                                      validator="style.visibility|visible")
        client.asserts.assertProperty(classname="PO_row",
                                      validator="style.visibility|collapse")

        client.select(id=u'field.file_type', val=u'PO')
        client.asserts.assertProperty(classname="POT_row",
                                      validator="style.visibility|collapse")
        client.asserts.assertProperty(classname="PO_row",
                                      validator="style.visibility|visible")

        client.select(id=u'field.file_type', val=u'UNSPEC')
        client.asserts.assertProperty(classname="POT_row",
                                      validator="style.visibility|collapse")
        client.asserts.assertProperty(classname="PO_row",
                                      validator="style.visibility|collapse")

test_import_queue = ImportQueueEntryTest(
    name='test_import_queue')
