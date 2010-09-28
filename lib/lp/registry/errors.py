# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = [
    'PrivatePersonLinkageError',
    'NameAlreadyTaken',
    'NoSuchDistroSeries',
    'UserCannotChangeMembershipSilently',
    'NoSuchSourcePackageName',
    'CannotTransitionToCountryMirror',
    'CountryMirrorAlreadySet',
    'MirrorNotOfficial',
    'MirrorHasNoHTTPURL',
    'MirrorNotProbed',
    'DeleteSubscriptionError',
    'UserCannotSubscribePerson',
    ]

import httplib

from lazr.restful.declarations import webservice_error

from lp.app.errors import NameLookupFailed

# Done
class PrivatePersonLinkageError(ValueError):
    """An attempt was made to link a private person/team to something."""
    webservice_error(httplib.FORBIDDEN)

    
# Done
class NameAlreadyTaken(Exception):
    """The name given for a person is already in use by other person."""
    webservice_error(httplib.CONFLICT)


# Done
class NoSuchDistroSeries(NameLookupFailed):
    """Raised when we try to find a DistroSeries that doesn't exist."""
    webservice_error(httplib.BAD_REQUEST)
    _message_prefix = "No such distribution series"


# Done
class UserCannotChangeMembershipSilently(Unauthorized):
    """User not permitted to change membership status silently.

    Raised when a user tries to change someone's membership silently, and is
    not a Launchpad Administrator.
    """
    webservice_error(httplib.UNAUTHORIZED)


#Done
class NoSuchSourcePackageName(NameLookupFailed):
    """Raised when we can't find a particular sourcepackagename."""
    webservice_error(httplib.BAD_REQUEST)
    _message_prefix = "No such source package"


class CannotTransitionToCountryMirror(Exception):
    """Root exception for transitions to country mirrors."""
    webservice_error(httplib.BAD_REQUEST)


class CountryMirrorAlreadySet(CannotTransitionToCountryMirror):
    """Distribution mirror cannot be set as a country mirror.

    Raised when a user tries to change set a distribution mirror as a country
    mirror, however there is already one set for that country.
    """


class MirrorNotOfficial(CannotTransitionToCountryMirror):
    """Distribution mirror is not permitted to become a country mirror.

    Raised when a user tries to change set a distribution mirror as a country
    mirror, however the mirror in question is not official.
    """


class MirrorHasNoHTTPURL(CannotTransitionToCountryMirror):
    """Distribution mirror has no HTTP URL.

    Raised when a user tries to make an official mirror a country mirror,
    however the mirror has not HTTP URL set.
    """


class MirrorNotProbed(CannotTransitionToCountryMirror):
    """Distribution mirror has not been probed.

    Raised when a user tries to set an official mirror as a country mirror,
    however the mirror has not been probed yet.
    """


class DeleteSubscriptionError(Exception):
    """Delete Subscription Error.

    Raised when an error occurred trying to delete a
    structural subscription."""
    webservice_error(httplib.BAD_REQUEST)


class UserCannotSubscribePerson(Exception):
    """User does not have permission to subscribe the person or team."""
    webservice_error(httplib.UNAUTHORIZED)
