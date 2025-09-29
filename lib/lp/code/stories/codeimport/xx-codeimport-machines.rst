Code Import Machines
====================

As an import operator, it is often desirable to see what the
import machines are doing.

At this stage, the page isn't linked from any other page, and has to
be entered manually (or from a bookmark).  Given that this is a view
that is more interesting to import operators, and not so much to
individual users, this seems like a fair compromise.

    >>> from lp.code.tests.helpers import GitHostingFixture
    >>> browser = setupBrowser(auth="Basic test@canonical.com:test")
    >>> browser.open("http://code.launchpad.test/+code-imports/+machines")
    >>> def print_table(browser):
    ...     table = find_tag_by_id(
    ...         browser.contents, "code-import-machine-listing"
    ...     )
    ...     print(extract_text(table))
    ...

Initially only the machine in sample data is shown.

    >>> print_table(browser)
    Machine                            Status
    bazaar-importer (0 jobs running)   Online

If we create some jobs that are running, then we can see the currently
running jobs in the table.

    >>> from lp.testing import login, logout
    >>> login("admin@canonical.com")

    >>> apollo, odin, saturn = (
    ...     factory.makeCodeImportMachine(set_online=True, hostname="apollo"),
    ...     factory.makeCodeImportMachine(set_online=True, hostname="odin"),
    ...     factory.makeCodeImportMachine(hostname="saturn"),
    ... )

    >>> from lp.code.tests.codeimporthelpers import make_running_import
    >>> from lp.registry.interfaces.person import IPersonSet
    >>> from lp.registry.interfaces.product import IProductSet
    >>> from zope.component import getUtility
    >>> with GitHostingFixture():
    ...     name12 = getUtility(IPersonSet).getByName("name12")
    ...     imp1 = factory.makeCodeImport(
    ...         registrant=name12,
    ...         context=getUtility(IProductSet).getByName("evolution"),
    ...         branch_name="foo",
    ...         git_repo_url="git://git.gnome.org/gnome-terminal/foo",
    ...     )
    ...     imp2 = factory.makeCodeImport(
    ...         registrant=name12,
    ...         context=getUtility(IProductSet).getByName("evolution"),
    ...         branch_name="bar",
    ...         git_repo_url="git://git.gnome.org/gnome-terminal/bar",
    ...     )
    ...     imp3 = factory.makeCodeImport(
    ...         registrant=name12,
    ...         context=getUtility(IProductSet).getByName("evolution"),
    ...         branch_name="baz",
    ...         git_repo_url="git://git.gnome.org/gnome-terminal/baz",
    ...     )
    ...     ignored = make_running_import(
    ...         code_import=imp1,
    ...         factory=factory,
    ...         machine=apollo,
    ...         logtail="Creating changeset 1\nCreating changeset 2",
    ...     )
    ...     ignored = make_running_import(
    ...         code_import=imp2, factory=factory, machine=apollo
    ...     )
    ...     ignored = make_running_import(
    ...         code_import=imp3, factory=factory, machine=odin
    ...     )
    ...
    >>> logout()

    >>> browser.open("http://code.launchpad.test/+code-imports/+machines")
    >>> print_table(browser)
    Machine
    Status
    apollo
    (2
    jobs
    running)
    Online
    lp:~name12/evolution/+git/foo
    Started: a moment ago
    Last heartbeat: a moment ago
    lp:~name12/evolution/+git/bar
    Started: a moment ago
    Last heartbeat: a moment ago
    bazaar-importer
    (0
    jobs
    running)
    Online
    odin
    (1
    job
    running)
    Online
    lp:~name12/evolution/+git/baz
    Started: a moment ago
    Last heartbeat: a moment ago
    saturn
    Offline


Individual machine views
------------------------

Each of the machine names is a hyperlink to a detailed machine page.

    >>> browser.getLink("apollo").click()

The heading of the page shows the import machine name, and the machine's
current status.

    >>> def print_heading(browser):
    ...     print(find_main_content(browser.contents).h1.decode_contents())
    ...
    >>> print_heading(browser)
    apollo: Online

The page also shows the current running jobs for that machine.

    >>> print(extract_text(find_tag_by_id(browser.contents, "current-jobs")))
    Current jobs
    lp:~name12/evolution/+git/foo
    Started: a moment ago
    Last heartbeat: a moment ago
    Creating changeset 1
    Creating changeset 2
    lp:~name12/evolution/+git/bar
    Started: a moment ago
    Last heartbeat: a moment ago

And also shows the most recent ten events for the machine, with the most
recent event first.

    >>> def print_events(browser):
    ...     recent_events = find_tag_by_id(browser.contents, "recent-events")
    ...     lines = extract_text(recent_events).splitlines()
    ...     for line in lines:
    ...         # Skip timestamps
    ...         if "AWST" in line:
    ...             continue
    ...         print(line)
    ...
    >>> print_events(browser)
    Related events
    Job Started
    lp:~name12/evolution/+git/bar
    Job Started
    lp:~name12/evolution/+git/foo
    Machine Online

Changing the machine's status
.............................

If the user is an admin or member of VCS Imports, they are able to change
the status of the machine.

    >>> print(find_tag_by_id(browser.contents, "update-status"))
    None

    >>> admin_browser.open(browser.url)

    >>> print(
    ...     find_tag_by_id(
    ...         admin_browser.contents, "update-status"
    ...     ).h2.decode_contents()
    ... )
    Update machine status

    >>> admin_browser.getControl("Reason").value = "Testing quiescing."
    >>> admin_browser.getControl("Set Quiescing").click()
    >>> print_heading(admin_browser)
    apollo: Quiescing

    >>> print_events(admin_browser)
    Related events
    ...: ... set Quiescing Requested
      Message: Testing quiescing.
    ...
