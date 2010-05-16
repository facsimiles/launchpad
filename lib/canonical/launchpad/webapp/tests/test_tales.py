# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""tales.py doctests."""

from textwrap import dedent
import unittest

from zope.testing.doctestunit import DocTestSuite

from canonical.launchpad.testing.pages import find_tags_by_class
from canonical.testing import DatabaseFunctionalLayer
from lp.app.browser.stringformatter import FormattersAPI
from lp.testing import TestCase


def test_requestapi():
    """
    >>> from canonical.launchpad.webapp.tales import IRequestAPI, RequestAPI
    >>> from canonical.launchpad.interfaces import IPerson
    >>> from zope.interface.verify import verifyObject

    >>> class FakePrincipal:
    ...     def __conform__(self, protocol):
    ...         if protocol is IPerson:
    ...             return "This is a person"
    ...

    >>> class FakeApplicationRequest:
    ...    principal = FakePrincipal()
    ...    def getURL(self):
    ...        return 'http://launchpad.dev/'
    ...

    Let's make a fake request, where request.principal is a FakePrincipal
    object.  We can use a class or an instance here.  It really doesn't
    matter.

    >>> request = FakeApplicationRequest()
    >>> adapter = RequestAPI(request)

    >>> verifyObject(IRequestAPI, adapter)
    True

    >>> adapter.person
    'This is a person'

    """

def test_cookie_scope():
    """
    The 'request/lp:cookie_scope' TALES expression returns a string
    that represents the scope parameters necessary for a cookie to be
    available for the entire Launchpad site.  It takes into account
    the request URL and the cookie_domains setting in launchpad.conf.

        >>> from canonical.launchpad.webapp.tales import RequestAPI
        >>> def cookie_scope(url):
        ...     class FakeRequest:
        ...         def getURL(self):
        ...             return url
        ...     return RequestAPI(FakeRequest()).cookie_scope

    The cookie scope will use the secure attribute if the request was
    secure:

        >>> print cookie_scope('http://launchpad.net/')
        ; Path=/; Domain=.launchpad.net
        >>> print cookie_scope('https://launchpad.net/')
        ; Path=/; Secure; Domain=.launchpad.net

    The domain parameter is omitted for domains that appear to be
    separate from a Launchpad instance, such as shipit:

        >>> print cookie_scope('https://shipit.ubuntu.com/')
        ; Path=/; Secure
    """

def test_dbschemaapi():
    """
    >>> from canonical.launchpad.webapp.tales import DBSchemaAPI
    >>> from lp.code.enums import BranchType

    The syntax to get the title is: number/lp:DBSchemaClass

    >>> (str(DBSchemaAPI(1).traverse('BranchType', []))
    ...  == BranchType.HOSTED.title)
    True

    Using an inappropriate number should give a KeyError.

    >>> DBSchemaAPI(99).traverse('BranchType', [])
    Traceback (most recent call last):
    ...
    KeyError: 99

    Using a dbschema name that doesn't exist should give a LocationError

    >>> DBSchemaAPI(99).traverse('NotADBSchema', [])
    Traceback (most recent call last):
    ...
    LocationError: 'NotADBSchema'

    """

def test_split_paragraphs():
    r"""
    The split_paragraphs() method is used to split a block of text
    into paragraphs, which are separated by one or more blank lines.
    Paragraphs are yielded as a list of lines in the paragraph.

      >>> from canonical.launchpad.webapp.tales import split_paragraphs
      >>> for paragraph in split_paragraphs('\na\nb\n\nc\nd\n\n\n'):
      ...     print paragraph
      ['a', 'b']
      ['c', 'd']
    """

def test_re_substitute():
    """
    When formatting text, we want to replace portions with links.
    re.sub() works fairly well for this, but doesn't give us much
    control over the non-matched text.  The re_substitute() function
    lets us do that.

      >>> import re
      >>> from canonical.launchpad.webapp.tales import re_substitute

      >>> def match_func(match):
      ...     return '[%s]' % match.group()
      >>> def nomatch_func(text):
      ...     return '{%s}' % text

      >>> pat = re.compile('a{2,6}')
      >>> print re_substitute(pat, match_func, nomatch_func,
      ...                     'bbaaaabbbbaaaaaaa aaaaaaaab')
      {bb}[aaaa]{bbbb}[aaaaaa]{a }[aaaaaa][aa]{b}
    """

def test_add_word_breaks():
    """
    Long words can cause page layout problems, so we insert manual
    word breaks into long words.  Breaks are added at least once every
    15 characters, but will break on as little as 7 characters if
    there is a suitable non-alphanumeric character to break after.

      >>> from canonical.launchpad.webapp.tales import add_word_breaks

      >>> print add_word_breaks('abcdefghijklmnop')
      abcdefghijklmno<wbr></wbr>p

      >>> print add_word_breaks('abcdef/ghijklmnop')
      abcdef/<wbr></wbr>ghijklmnop

      >>> print add_word_breaks('ab/cdefghijklmnop')
      ab/cdefghijklmn<wbr></wbr>op

    The string can contain HTML entities, which do not get split:

      >>> print add_word_breaks('abcdef&anentity;hijklmnop')
      abcdef&anentity;<wbr></wbr>hijklmnop
    """

def test_break_long_words():
    """
    If we have a long HTML string, break_long_words() can be used to
    add word breaks to the long words.  It will not add breaks inside HTML
    tags.  Only words longer than 20 characters will have breaks added.

      >>> from canonical.launchpad.webapp.tales import break_long_words

      >>> print break_long_words('1234567890123456')
      1234567890123456

      >>> print break_long_words('12345678901234567890')
      123456789012345<wbr></wbr>67890

      >>> print break_long_words('<tag a12345678901234567890="foo"></tag>')
      <tag a12345678901234567890="foo"></tag>

      >>> print break_long_words('12345678901234567890 1234567890.1234567890')
      123456789012345<wbr></wbr>67890 1234567890.<wbr></wbr>1234567890

      >>> print break_long_words('1234567890&abcdefghi;123')
      1234567890&abcdefghi;123

      >>> print break_long_words('<tag>1234567890123456</tag>')
      <tag>1234567890123456</tag>
    """


class TestDiffFormatter(TestCase):
    """Test the string formtter fmt:diff."""
    layer = DatabaseFunctionalLayer

    def test_emptyString(self):
        # An empty string gives an empty string.
        self.assertEqual(
            '', FormattersAPI('').format_diff())

    def test_almostEmptyString(self):
        # White space doesn't count as empty, and is formtted.
        self.assertEqual(
            '<table class="diff"><tr><td class="line-no">1</td>'
            '<td class="text"> </td></tr></table>',
            FormattersAPI(' ').format_diff())

    def test_format_unicode(self):
        # Sometimes the strings contain unicode, those should work too.
        self.assertEqual(
            u'<table class="diff"><tr><td class="line-no">1</td>'
            u'<td class="text">Unicode \u1010</td></tr></table>',
            FormattersAPI(u'Unicode \u1010').format_diff())

    def test_cssClasses(self):
        # Different parts of the diff have different css classes.
        diff = dedent('''\
            === modified file 'tales.py'
            --- tales.py
            +++ tales.py
            @@ -2435,6 +2435,8 @@
                 def format_diff(self):
            -        removed this line
            +        added this line
            ########
            # A merge directive comment.
            ''')
        html = FormattersAPI(diff).format_diff()
        line_numbers = find_tags_by_class(html, 'line-no')
        self.assertEqual(
            ['1','2','3','4','5','6','7','8','9'],
            [tag.renderContents() for tag in line_numbers])
        text = find_tags_by_class(html, 'text')
        self.assertEqual(
            ['diff-file text',
             'diff-header text',
             'diff-header text',
             'diff-chunk text',
             'text',
             'diff-removed text',
             'diff-added text',
             'diff-comment text',
             'diff-comment text'],
            [str(tag['class']) for tag in text])

    def test_config_value_limits_line_count(self):
        # The config.diff.max_line_format contains the maximum number of lines
        # to format.
        diff = dedent('''\
            === modified file 'tales.py'
            --- tales.py
            +++ tales.py
            @@ -2435,6 +2435,8 @@
                 def format_diff(self):
            -        removed this line
            +        added this line
            ########
            # A merge directive comment.
            ''')
        self.pushConfig("diff", max_format_lines=3)
        html = FormattersAPI(diff).format_diff()
        line_count = html.count('<td class="line-no">')
        self.assertEqual(3, line_count)


def test_suite():
    """Return this module's doctest Suite. Unit tests are also run."""
    suite = unittest.TestSuite()
    suite.addTests(DocTestSuite())
    suite.addTests(unittest.TestLoader().loadTestsFromName(__name__))
    return suite


if __name__ == '__main__':
    unittest.main()
