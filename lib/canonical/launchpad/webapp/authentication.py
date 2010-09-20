# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type

__all__ = [
    'check_oauth_signature',
    'extract_oauth_access_token',
    'get_oauth_principal',
    'get_oauth_authorization',
    'LaunchpadLoginSource',
    'LaunchpadPrincipal',
    'OAuthSignedRequest',
    'PlacelessAuthUtility',
    'SSHADigestEncryptor',
    ]


import binascii
from datetime import datetime
import hashlib
import pytz
import random
from UserDict import UserDict

from contrib.oauth import OAuthRequest
from zope.annotation.interfaces import IAnnotations
from zope.app.security.interfaces import ILoginPassword
from zope.app.security.principalregistry import UnauthenticatedPrincipal
from zope.authentication.interfaces import IUnauthenticatedPrincipal

from zope.component import (
    adapts,
    getUtility,
    )
from zope.event import notify
from zope.interface import (
    alsoProvides,
    implements,
    )
from zope.preference.interfaces import IPreferenceGroup
from zope.security.interfaces import Unauthorized
from zope.security.proxy import removeSecurityProxy
from zope.session.interfaces import ISession

from canonical.config import config
from canonical.launchpad.interfaces.account import IAccountSet
from canonical.launchpad.interfaces.launchpad import IPasswordEncryptor
from canonical.launchpad.interfaces.oauth import OAUTH_CHALLENGE
from canonical.launchpad.webapp.interfaces import (
    AccessLevel,
    BasicAuthLoggedInEvent,
    CookieAuthPrincipalIdentifiedEvent,
    ILaunchpadPrincipal,
    IPlacelessAuthUtility,
    IPlacelessLoginSource,
    OAuthPermission,
    )
from canonical.launchpad.interfaces.oauth import (
    ClockSkew,
    IOAuthConsumerSet,
    IOAuthSignedRequest,
    NonceAlreadyUsed,
    TimestampOrderingError,
    )
from lp.registry.interfaces.person import (
    IPerson,
    IPersonSet,
    )


def extract_oauth_access_token(request):
    """Find the OAuth access token that signed the given request.

    :param request: An incoming request.

    :return: an IOAuthAccessToken, or None if the request is not
        signed at all.

    :raise Unauthorized: If the token is invalid or the request is an
        anonymously-signed request that doesn't meet our requirements.
    """
    # Fetch OAuth authorization information from the request.
    form = get_oauth_authorization(request)

    consumer_key = form.get('oauth_consumer_key')
    consumers = getUtility(IOAuthConsumerSet)
    consumer = consumers.getByKey(consumer_key)
    token_key = form.get('oauth_token')
    anonymous_request = (token_key == '')

    if consumer_key is None:
        # Either the client's OAuth implementation is broken, or
        # the user is trying to make an unauthenticated request
        # using wget or another OAuth-ignorant application.
        # Try to retrieve a consumer based on the User-Agent
        # header.
        anonymous_request = True
        consumer_key = request.getHeader('User-Agent', '')
        if consumer_key == '':
            raise Unauthorized(
                'Anonymous requests must provide a User-Agent.')
        consumer = consumers.getByKey(consumer_key)

    if consumer is None:
        if anonymous_request:
            # This is the first time anyone has tried to make an
            # anonymous request using this consumer name (or user
            # agent). Dynamically create the consumer.
            #
            # In the normal website this wouldn't be possible
            # because GET requests have their transactions rolled
            # back. But webservice requests always have their
            # transactions committed so that we can keep track of
            # the OAuth nonces and prevent replay attacks.
            if consumer_key == '' or consumer_key is None:
                raise Unauthorized("No consumer key specified.")
            consumer = consumers.new(consumer_key, '')
        else:
            # An unknown consumer can never make a non-anonymous
            # request, because access tokens are registered with a
            # specific, known consumer.
            raise Unauthorized('Unknown consumer (%s).' % consumer_key)
    if anonymous_request:
        # Skip the OAuth verification step and let the user access the
        # web service as an unauthenticated user.
        #
        # XXX leonardr 2009-12-15 bug=496964: Ideally we'd be
        # auto-creating a token for the anonymous user the first
        # time, passing it through the OAuth verification step,
        # and using it on all subsequent anonymous requests.
        return None

    token = consumer.getAccessToken(token_key)
    if token is None:
        raise Unauthorized('Unknown access token (%s).' % token_key)
    return token


def get_oauth_principal(request):
    """Find the principal to use for this OAuth-signed request.

    :param request: An incoming request.
    :return: An ILaunchpadPrincipal with the appropriate access level.
    """
    token = extract_oauth_access_token(request)

    if token is None:
        # The consumer is making an anonymous request. If there was a
        # problem with the access token, extract_oauth_access_token
        # would have raised Unauthorized.
        alsoProvides(request, IOAuthSignedRequest)
        auth_utility = getUtility(IPlacelessAuthUtility)
        return auth_utility.unauthenticatedPrincipal()

    form = get_oauth_authorization(request)
    nonce = form.get('oauth_nonce')
    timestamp = form.get('oauth_timestamp')
    try:
        token.checkNonceAndTimestamp(nonce, timestamp)
    except (NonceAlreadyUsed, TimestampOrderingError, ClockSkew), e:
        raise Unauthorized('Invalid nonce/timestamp: %s' % e)
    now = datetime.now(pytz.timezone('UTC'))
    if token.permission == OAuthPermission.UNAUTHORIZED:
        raise Unauthorized('Unauthorized token (%s).' % token.key)
    elif token.date_expires is not None and token.date_expires <= now:
        raise Unauthorized('Expired token (%s).' % token.key)
    elif not check_oauth_signature(request, token.consumer, token):
        raise Unauthorized('Invalid signature.')
    else:
        # Everything is fine, let's return the principal.
        pass
    alsoProvides(request, IOAuthSignedRequest)
    return getUtility(IPlacelessLoginSource).getPrincipal(
        token.person.account.id, access_level=token.permission,
        scope=token.context)


class PlacelessAuthUtility:
    """An authentication service which holds no state aside from its
    ZCML configuration, implemented as a utility.
    """
    implements(IPlacelessAuthUtility)

    def __init__(self):
        self.nobody = UnauthenticatedPrincipal(
            'Anonymous', 'Anonymous', 'Anonymous User')
        self.nobody.__parent__ = self

    def _authenticateUsingBasicAuth(self, credentials, request):
        login = credentials.getLogin()
        if login is not None:
            login_src = getUtility(IPlacelessLoginSource)
            principal = login_src.getPrincipalByLogin(login)
            if principal is not None and principal.account.is_valid:
                password = credentials.getPassword()
                if principal.validate(password):
                    # We send a LoggedInEvent here, when the
                    # cookie auth below sends a PrincipalIdentified,
                    # as the login form is never visited for BasicAuth.
                    # This we treat each request as a separate
                    # login/logout.
                    notify(
                        BasicAuthLoggedInEvent(request, login, principal))
                    return principal

    def _authenticateUsingCookieAuth(self, request):
        session = ISession(request)
        authdata = session['launchpad.authenticateduser']
        id = authdata.get('accountid')
        if id is None:
            # XXX: salgado, 2009-02-17: This is for backwards compatibility,
            # when we used to store the person's ID in the session.
            person_id = authdata.get('personid')
            if person_id is not None:
                person = getUtility(IPersonSet).get(person_id)
                if person is not None and person.accountID is not None:
                    id = person.accountID

        if id is None:
            return None

        login_src = getUtility(IPlacelessLoginSource)
        principal = login_src.getPrincipal(id)
        # Note, not notifying a LoggedInEvent here as for session-based
        # auth the login occurs when the login form is submitted, not
        # on each request.
        if principal is None:
            # XXX Stuart Bishop 2006-05-26 bug=33427:
            # User is authenticated in session, but principal is not"
            # available in login source. This happens when account has
            # become invalid for some reason, such as being merged.
            return None
        elif principal.account.is_valid:
            login = authdata['login']
            assert login, 'login is %s!' % repr(login)
            notify(CookieAuthPrincipalIdentifiedEvent(
                principal, request, login))
            return principal
        else:
            return None

    def authenticate(self, request):
        """See IAuthentication."""
        # To avoid confusion (hopefully), basic auth trumps cookie auth
        # totally, and all the time.  If there is any basic auth at all,
        # then cookie auth won't even be considered.

        # XXX daniels 2004-12-14: allow authentication scheme to be put into
        #     a view; for now, use basic auth by specifying ILoginPassword.
        credentials = ILoginPassword(request, None)
        if credentials is not None and credentials.getLogin() is not None:
            return self._authenticateUsingBasicAuth(credentials, request)
        else:
            # Hack to make us not even think of using a session if there
            # isn't already a cookie in the request, or one waiting to be
            # set in the response.
            cookie_name = config.launchpad_session.cookie
            if (request.cookies.get(cookie_name) is not None or
                request.response.getCookie(cookie_name) is not None):
                return self._authenticateUsingCookieAuth(request)
            else:
                return None

    def unauthenticatedPrincipal(self):
        """See IAuthentication."""
        return self.nobody

    def unauthorized(self, id, request):
        """See IAuthentication."""
        a = ILoginPassword(request)
        # TODO maybe configure the realm from zconfigure.
        a.needLogin(realm="launchpad")

    def getPrincipal(self, id):
        """See IAuthentication."""
        utility = getUtility(IPlacelessLoginSource)
        return utility.getPrincipal(id)

    # XXX: This is part of IAuthenticationUtility, but that interface doesn't
    # exist anymore and I'm not sure this is used anywhere.  Need to
    # investigate further.
    def getPrincipals(self, name):
        """See IAuthenticationUtility."""
        utility = getUtility(IPlacelessLoginSource)
        return utility.getPrincipals(name)

    def getPrincipalByLogin(self, login, want_password=True):
        """See IAuthenticationService."""
        utility = getUtility(IPlacelessLoginSource)
        return utility.getPrincipalByLogin(login, want_password=want_password)


class SSHADigestEncryptor:
    """SSHA is a modification of the SHA digest scheme with a salt
    starting at byte 20 of the base64-encoded string.
    """
    implements(IPasswordEncryptor)

    # Source: http://developer.netscape.com/docs/technote/ldap/pass_sha.html

    saltLength = 20

    def generate_salt(self):
        # Salt can be any length, but not more than about 37 characters
        # because of limitations of the binascii module.
        # All 256 characters are available.
        salt = ''
        for n in range(self.saltLength):
            salt += chr(random.randrange(256))
        return salt

    def encrypt(self, plaintext, salt=None):
        plaintext = str(plaintext)
        if salt is None:
            salt = self.generate_salt()
        v = binascii.b2a_base64(
            hashlib.sha1(plaintext + salt).digest() + salt)
        return v[:-1]

    def validate(self, plaintext, encrypted):
        encrypted = str(encrypted)
        plaintext = str(plaintext)
        try:
            ref = binascii.a2b_base64(encrypted)
        except binascii.Error:
            # Not valid base64.
            return False
        salt = ref[20:]
        v = binascii.b2a_base64(
            hashlib.sha1(plaintext + salt).digest() + salt)[:-1]
        pw1 = (v or '').strip()
        pw2 = (encrypted or '').strip()
        return pw1 == pw2


class LaunchpadLoginSource:
    """A login source that uses the launchpad SQL database to look up
    principal information.
    """
    implements(IPlacelessLoginSource)

    def getPrincipal(self, id, access_level=AccessLevel.WRITE_PRIVATE,
                     scope=None):
        """Return an `ILaunchpadPrincipal` for the account with the given id.

        Return None if there is no account with the given id.

        The `access_level` can be used for further restricting the capability
        of the principal.  By default, no further restriction is added.

        Similarly, when a `scope` is given, the principal's capabilities will
        apply only to things within that scope.  For everything else that is
        not private, the principal will have only read access.

        Note that we currently need to be able to retrieve principals for
        invalid People, as the login machinery needs the principal to
        validate the password against so it may then email a validation
        request to the user and inform them it has done so.
        """
        try:
            account = getUtility(IAccountSet).get(id)
        except LookupError:
            return None

        return self._principalForAccount(account, access_level, scope)

    def getPrincipals(self, name):
        raise NotImplementedError

    def getPrincipalByLogin(self, login,
                            access_level=AccessLevel.WRITE_PRIVATE,
                            scope=None, want_password=True):
        """Return a principal based on the account with the email address
        signified by "login".

        :param want_password: If want_password is False, the pricipal
        will have None for a password. Use this when trying to retrieve a
        principal in contexts where we don't need the password and the
        database connection does not have access to the Account or
        AccountPassword tables.

        :return: None if there is no account with the given email address.

        The `access_level` can be used for further restricting the capability
        of the principal.  By default, no further restriction is added.

        Similarly, when a `scope` is given, the principal's capabilities will
        apply only to things within that scope.  For everything else that is
        not private, the principal will have only read access.


        Note that we currently need to be able to retrieve principals for
        invalid People, as the login machinery needs the principal to
        validate the password against so it may then email a validation
        request to the user and inform them it has done so.
        """
        try:
            account = getUtility(IAccountSet).getByEmail(login)
        except LookupError:
            return None
        else:
            return self._principalForAccount(
                account, access_level, scope, want_password)

    def _principalForAccount(self, account, access_level, scope,
                             want_password=True):
        """Return a LaunchpadPrincipal for the given account.

        The LaunchpadPrincipal will also have the given access level and
        scope.

        If want_password is True, the principal's password will be set to the
        account's password.  Otherwise it's set to None.
        """
        naked_account = removeSecurityProxy(account)
        if want_password:
            password = naked_account.password
        else:
            password = None
        principal = LaunchpadPrincipal(
            naked_account.id, naked_account.displayname,
            naked_account.displayname, account, password,
            access_level=access_level, scope=scope)
        principal.__parent__ = self
        return principal


# Fake a containment hierarchy because Zope3 is on crack.
authService = PlacelessAuthUtility()
loginSource = LaunchpadLoginSource()
loginSource.__parent__ = authService


class LaunchpadPrincipal:

    implements(ILaunchpadPrincipal)

    def __init__(self, id, title, description, account, pwd=None,
                 access_level=AccessLevel.WRITE_PRIVATE, scope=None):
        self.id = id
        self.title = title
        self.description = description
        self.access_level = access_level
        self.scope = scope
        self.account = account
        self.person = IPerson(account, None)
        self.__pwd = pwd

    def getLogin(self):
        return self.title

    def validate(self, pw):
        encryptor = getUtility(IPasswordEncryptor)
        pw1 = (pw or '').strip()
        pw2 = (self.__pwd or '').strip()
        return encryptor.validate(pw1, pw2)


# zope.app.apidoc expects our principals to be adaptable into IAnnotations, so
# we use these dummy adapters here just to make that code not OOPS.

class TemporaryPrincipalAnnotations(UserDict):
    implements(IAnnotations)
    adapts(ILaunchpadPrincipal, IPreferenceGroup)

    def __init__(self, principal, pref_group):
        UserDict.__init__(self)


class TemporaryUnauthenticatedPrincipalAnnotations(
        TemporaryPrincipalAnnotations):
    implements(IAnnotations)
    adapts(IUnauthenticatedPrincipal, IPreferenceGroup)


def get_oauth_authorization(request):
    """Retrieve OAuth authorization information from a request.

    The authorization information may be in the Authorization header,
    or it might be in the query string or entity-body.

    :return: a dictionary of authorization information.
    """
    header = request._auth
    if header is not None and header.startswith("OAuth "):
        return OAuthRequest._split_header(header)
    else:
        return request.form


def check_oauth_signature(request, consumer, token):
    """Check that the given OAuth request is correctly signed.

    If the signature is incorrect or its method is not supported, set the
    appropriate status in the request's response and return False.
    """
    authorization = get_oauth_authorization(request)

    if authorization.get('oauth_signature_method') != 'PLAINTEXT':
        # XXX: 2008-03-04, salgado: Only the PLAINTEXT method is supported
        # now. Others will be implemented later.
        request.response.setStatus(400)
        return False

    if token is not None:
        token_secret = token.secret
    else:
        token_secret = ''
    expected_signature = "&".join([consumer.secret, token_secret])
    if expected_signature != authorization.get('oauth_signature'):
        request.unauthorized(OAUTH_CHALLENGE)
        return False

    return True
