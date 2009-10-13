# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Utilities for Windmill tests written in Python."""

__metaclass__ = type
__all__ = []


class LaunchpadUser:
    """Object representing well-known user on Launchpad."""

    def __init__(self, display_name, email, password):
        self.display_name = display_name
        self.email = email
        self.password = password

    def ensure_login(self, client):
        """Ensure that this user is logged on the page under windmill."""
        result = client.asserts.assertNode(
            link=u'Log in / Register', assertion=False)
        if not result['result']:
            # User is probably logged in.
            # Check under which name they are logged in.
            result = client.commands.execJS(
                code="""lookupNode({xpath: '//div[@id="logincontrol"]//a'}).text""")
            if (result['result'] is not None and
                result['result'].strip() == self.display_name):
                # We are logged as that user.
                return
            client.click(name="logout")
            client.waits.forPageLoad(timeout=u'20000')
        client.click(link=u'Log in / Register')
        client.waits.forPageLoad(timeout=u'20000')
        client.waits.forElement(timeout=u'8000', id=u'email')
        client.type(text=self.email, id=u'email')
        client.type(text=self.password, id=u'password')
        client.click(name=u'loginpage_submit_login')
        client.waits.forPageLoad(timeout=u'20000')


class AnonymousUser:
    """Object representing the anonymous user."""

    def ensure_login(self, client):
        """Ensure that the user is surfing anonymously."""
        result = client.asserts.assertNode(
            link=u'Log in / Register', assertion=False)
        if result['result']:
            return
        client.waits.forElement(name="logout", timeout=u"100000")
        client.click(name="logout")
        client.waits.forPageLoad(timeout=u'100000')


def login_person(person, password, client):
    """Create a LaunchpadUser for a person and password."""
    user = LaunchpadUser(
        person.displayname, person.preferredemail.email, password)
    user.ensure_login(client)


# Well Known Users
ANONYMOUS = AnonymousUser()

SAMPLE_PERSON = LaunchpadUser(
    'Sample Person', 'test@canonical.com', 'test')

FOO_BAR = LaunchpadUser(
    'Foo Bar', 'foo.bar@canonical.com', 'test')

NO_PRIV = LaunchpadUser(
    'No Privileges User', 'no-priv@canonical.com', 'test')

TRANSLATIONS_ADMIN = LaunchpadUser(
    u'Carlos Perell\xf3 Mar\xedn', 'carlos@canonical.com', 'test')
