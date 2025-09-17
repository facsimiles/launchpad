Creating a code import
======================

Users are able to specifically request a code import of their
project's code.  The main link to this is a large button on
the code home page "Import your project".

    >>> browser = setupBrowser(auth="Basic no-priv@canonical.com:test")
    >>> browser.open("http://code.launchpad.test")
    >>> print(find_tag_by_id(browser.contents, "new-code-import"))
    <a href="/+code-imports/+new" id="new-code-import">
       <img alt="Import your project" ...>
    </a>

    >>> browser.getLink(id="new-code-import").click()
    >>> print(browser.title)
    Request a code import...

    >>> browser.contents
    '...You will not be able to push directly to the
    imported\n        branch or repository...'

There is a cancel link on this page near the buttons to take the
user back to the main code page.

    >>> browser.getLink("Cancel").click()
    >>> print(browser.url)
    http://code.launchpad.test/

For projects that don't officially use Launchpad for code, there is also a
link on the main branch listing page for the product.

    >>> browser.open("http://code.launchpad.test/firefox")
    >>> browser.getLink("Import a branch").click()
    Traceback (most recent call last):
    ...
    zope.testbrowser.browser.LinkNotFoundError

The owner can configure code hosting for the project and then
importing will be available to any user.

    >>> from lp.code.tests.helpers import GitHostingFixture
    >>> owner_browser = setupBrowser(auth="Basic test@canonical.com:test")
    >>> owner_browser.open("http://code.launchpad.test/firefox")
    >>> owner_browser.getLink("Configure Code").click()
    >>> owner_browser.getControl("Git", index=0).click()
    >>> owner_browser.getControl("Import a Git").click()
    >>> owner_browser.getControl("Git repository URL").value = (
    ...     "git://example.com/firefox"
    ... )
    >>> with GitHostingFixture():
    ...     owner_browser.getControl("Update").click()
    ...

Requesting a Git-to-Git import
==============================

The user is required to enter a project that the import is for,
a name for the import repository, and a Git repository location.  The URL is
allowed to match that of an existing Bazaar-targeted import.

    >>> browser.open("http://code.launchpad.test/+code-imports/+new")
    >>> browser.getControl("Project").value = "firefox"
    >>> browser.getControl("Name").value = "upstream"
    >>> browser.getControl("Git", index=0).click()
    >>> browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/firefox.git"
    ... )
    >>> with GitHostingFixture():
    ...     browser.getControl("Request Import").click()
    ...

When the user clicks continue, the approved import repository is created.

    >>> print(
    ...     extract_text(find_tag_by_id(browser.contents, "import-details"))
    ... )
    Import Status: Reviewed
    This repository is an import of the Git repository at
    git://example.com/firefox.git.
    The next import is scheduled to run as soon as possible.
    Edit import source or review import


Requesting an import that is already being imported
===================================================

If a user requests an import that is already being imported, then
the validation message points the user to the existing branch.

    >>> browser.open("http://code.launchpad.test/+code-imports/+new")

The error is shown even if the project is different.

    >>> browser.open("http://code.launchpad.test/+code-imports/+new")
    >>> browser.getControl("Project").value = "firefox"
    >>> browser.getControl("Name").value = "upstream"
    >>> browser.getControl("Git", index=0).click()
    >>> browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/firefox.git"
    ... )
    >>> with GitHostingFixture():
    ...     browser.getControl("Request Import").click()
    ...
    >>> browser.open("http://code.launchpad.test/+code-imports/+new")
    >>> browser.getControl("Project").value = "firefox"
    >>> browser.getControl("Name").value = "upstream"
    >>> browser.getControl("Git", index=0).click()
    >>> browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/firefox.git"
    ... )
    >>> with GitHostingFixture():
    ...     browser.getControl("Request Import").click()
    ...
    >>> print_feedback_messages(browser.contents)
    There is 1 error.
    This foreign branch URL is already specified
    for the imported repository ~no-priv/firefox/+git/upstream.


Requesting an import on a project where the user doesn't have permission
========================================================================

If there are privacy policies that disallow the user from creating branches
then an error is shown to the user.

    >>> browser.open("http://code.launchpad.test/+code-imports/+new")
    >>> browser.getControl("Project").value = "launchpad"
    >>> browser.getControl("Name").value = "upstream"
    >>> browser.getControl("Git", index=0).click()
    >>> browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/launchpad.git"
    ... )
    >>> with GitHostingFixture():
    ...     browser.getControl("Request Import").click()
    ...
    >>> print_feedback_messages(browser.contents)
    There is 1 error.
    You are not allowed to register imports for Launchpad.


Requesting an import for a product that does not exist
======================================================

If the name typed in the product field does not match that of an
existing product, an error is shown to the user.

    >>> browser.open("http://code.launchpad.test/+code-imports/+new")
    >>> browser.getControl("Project").value = "no-such-product"
    >>> browser.getControl("Name").value = "upstream"
    >>> browser.getControl("Git", index=0).click()
    >>> browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/launchpad.git"
    ... )
    >>> browser.getControl("Request Import").click()
    >>> print_feedback_messages(browser.contents)
    There is 1 error.
    Invalid value


Specifying the owner of the branch when it is being created
===========================================================

When a user is requesting a new code import, they are the owner of the new
import branch.  sometimes the user may wish for the import branch to be owned
by a team rather than just themselves.  There is a drop down choice shown for
the user for the teams that they are a member of.

    >>> sample_browser = setupBrowser(auth="Basic test@canonical.com:test")
    >>> sample_browser.open("http://code.launchpad.test/firefox/+new-import")
    >>> sample_browser.getControl("Owner").displayValue
    ['Sample Person (name12)']

Change the owner to be a team that sample person is a member of.

    >>> sample_browser.getControl("Owner").value = ["landscape-developers"]
    >>> sample_browser.getControl("Owner").displayValue
    ['Landscape Developers (landscape-developers)']
    >>> sample_browser.getControl("Repo URL", index=0).value = (
    ...     "http://svn.example.com/firefox-beta/trunk"
    ... )
    >>> with GitHostingFixture():
    ...     sample_browser.getControl("Request Import").click()
    ...

    >>> print_tag_with_id(sample_browser.contents, "registration")
    Owned by Landscape Developers

Admins can specify any owner for a new code import.

    >>> admin_browser = setupBrowser(auth="Basic admin@canonical.com:test")
    >>> admin_browser.open("http://code.launchpad.test/firefox/+new-import")
    >>> admin_browser.getControl("Owner").value = "mark"
    >>> admin_browser.getControl("Repo URL", index=0).value = (
    ...     "git://example.com/firefox-theta.git"
    ... )
    >>> with GitHostingFixture():
    ...     admin_browser.getControl("Request Import").click()
    ...

    >>> print_tag_with_id(admin_browser.contents, "registration")
    Owned by Mark Shuttleworth
