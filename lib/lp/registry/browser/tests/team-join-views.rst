Joining a Team
==============

Tests for the team '+join' page's raw view objects.

Joining and Subscribing to the List
-----------------------------------

    >>> from lp.registry.interfaces.person import IPersonSet
    >>> personset = getUtility(IPersonSet)

    # Set up a harness to make form submission testing easier.
    >>> from zope.component import getMultiAdapter
    >>> from lp.services.webapp.servers import LaunchpadTestRequest
    >>> def join_team(team):
    ...     form = {
    ...         "field.actions.join": "1",
    ...         "field.mailinglist_subscribe": "on",
    ...     }
    ...     request = LaunchpadTestRequest(method="POST", form=form)
    ...     view = getMultiAdapter((team, request), name="+join")
    ...     view.initialize()
    ...     for notification in request.notifications:
    ...         print(notification.message)
    ...

    # Define a helper for creating teams with a specific subscription
    # policy.
    >>> from lp.registry.interfaces.person import TeamMembershipPolicy
    >>> def make_team(teamname, membership_policy):
    ...     creator = personset.getByName("no-priv")
    ...     team = personset.newTeam(
    ...         creator,
    ...         teamname,
    ...         teamname,
    ...         membership_policy=membership_policy,
    ...     )
    ...     return team
    ...

    >>> from lp.registry.interfaces.mailinglist import IMailingListSet
    >>> subscribers = getUtility(IMailingListSet)

Attempting to post a mailing list subscription request to a team that has no
list is thwarted by the view because it strips the checkbox from the form.
Therefore no error message is seen.

    >>> sample_person = personset.getByName("name12")
    >>> ignored = login_person(sample_person)
    >>> no_list_team = make_team(
    ...     "open-team-no-list", TeamMembershipPolicy.OPEN
    ... )

    >>> join_team(no_list_team)
    You have successfully joined open-team-no-list.
