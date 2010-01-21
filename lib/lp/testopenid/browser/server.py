# Copyright 2010 Canonical Ltd.  All rights reserved.

"""Test OpenID server."""

__metaclass__ = type
__all__ = [
    'TestOpenIDApplicationNavigation',
    'TestOpenIDIndexView'
    'TestOpenIDLoginView',
    'TestOpenIDRootUrlData',
    'TestOpenIDView',
    ]

from datetime import timedelta
from time import time

from z3c.ptcompat import ViewPageTemplateFile
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.component import getUtility
from zope.interface import implements
from zope.security.proxy import isinstance as zisinstance
from zope.session.interfaces import ISession

from openid.server.server import CheckIDRequest, Server
from openid.store.memstore import MemoryStore

from canonical.cachedproperty import cachedproperty
from canonical.launchpad import _
from canonical.launchpad.interfaces.account import AccountStatus, IAccountSet
from canonical.launchpad.webapp import (
    action, LaunchpadFormView, LaunchpadView)
from canonical.launchpad.webapp.interfaces import (
    ICanonicalUrlData, IPlacelessLoginSource, UnexpectedFormData)
from canonical.launchpad.webapp.login import (
    allowUnauthenticatedSession, logInPrincipal, logoutPerson)
from canonical.launchpad.webapp.publisher import Navigation, stepthrough
from canonical.launchpad.webapp.url import urlappend
from canonical.launchpad.webapp.vhosts import allvhosts
from canonical.uuid import generate_uuid

from lp.services.openid.browser.openiddiscovery import (
    XRDSContentNegotiationMixin)
from lp.testopenid.interfaces.server import (
    ITestOpenIDApplication, ITestOpenIDLoginForm,
    ITestOpenIDPersistentIdentity)


OPENID_REQUEST_TIMEOUT = 3600
SESSION_PKG_KEY = 'TestOpenID'
SERVER_URL = urlappend(allvhosts.configs['testopenid'].rooturl, '+openid')
openid_store = MemoryStore()


class TestOpenIDRootUrlData:
    """`ICanonicalUrlData` for the test OpenID provider."""

    implements(ICanonicalUrlData)

    path = ''
    inside = None
    rootsite = 'testopenid'

    def __init__(self, context):
        self.context = context


class TestOpenIDApplicationNavigation(Navigation):
    """Navigation for `ITestOpenIDApplication`"""
    usedfor = ITestOpenIDApplication

    @stepthrough('+id')
    def traverse_id(self, name):
        """Traverse to persistent OpenID identity URLs."""
        try:
            account = getUtility(IAccountSet).getByOpenIDIdentifier(name)
        except LookupError:
            account = None
        if account is None or account.status != AccountStatus.ACTIVE:
            return None
        return ITestOpenIDPersistentIdentity(account)


class TestOpenIDXRDSContentNegotiationMixin(XRDSContentNegotiationMixin):
    """Custom XRDSContentNegotiationMixin that overrides openid_server_url."""

    @property
    def openid_server_url(self):
        """The OpenID Server endpoint URL for Launchpad."""
        return SERVER_URL


class TestOpenIDIndexView(
        TestOpenIDXRDSContentNegotiationMixin, LaunchpadView):
    template = ViewPageTemplateFile("../templates/application-index.pt")
    xrds_template = ViewPageTemplateFile("../templates/application-xrds.pt")


class OpenIDMixin:

    openid_request = None

    def __init__(self, context, request):
        super(OpenIDMixin, self).__init__(context, request)
        self.server_url = SERVER_URL
        self.openid_server = Server(openid_store, self.server_url)

    @property
    def user_identity_url(self):
        return ITestOpenIDPersistentIdentity(self.account).openid_identity_url

    def isIdentityOwner(self):
        """Return True if the user can authenticate as the given ID."""
        assert self.account is not None, "user should be logged in by now."
        return (self.openid_request.idSelect() or
                self.openid_request.identity == self.user_identity_url)

    @cachedproperty('_openid_parameters')
    def openid_parameters(self):
        """A dictionary of OpenID query parameters from request."""
        query = {}
        for key, value in self.request.form.items():
            if key.startswith('openid.'):
                query[key.encode('US-ASCII')] = value.encode('US-ASCII')
        return query

    def getSession(self):
        if IUnauthenticatedPrincipal.providedBy(self.request.principal):
            # A dance to assert that we want to break the rules about no
            # unauthenticated sessions. Only after this next line is it
            # safe to set session values.
            allowUnauthenticatedSession(
                self.request, duration=timedelta(minutes=60))
        return ISession(self.request)[SESSION_PKG_KEY]

    @staticmethod
    def _sweep(now, session):
        """Clean our Session of nonces older than 1 hour.

        The session argument is edited in place to remove the expired items:
          >>> now = 10000
          >>> session = {
          ...     'x': (9999, 'foo'),
          ...     'y': (11000, 'bar'),
          ...     'z': (100, 'baz')
          ...     }
          >>> OpenIDMixin._sweep(now, session)
          >>> for key in sorted(session):
          ...     print key, session[key]
          x (9999, 'foo')
          y (11000, 'bar')
        """
        to_delete = []
        for key, value in session.items():
            timestamp = value[0]
            if timestamp < now - OPENID_REQUEST_TIMEOUT:
                to_delete.append(key)
        for key in to_delete:
            del session[key]

    def restoreRequestFromSession(self, key):
        """Get the OpenIDRequest from our session using the given key."""
        session = self.getSession()
        try:
            timestamp, self._openid_parameters = session[key]
        except KeyError:
            raise UnexpectedFormData("Invalid or expired nonce")

        # Decode the request parameters and create the request object.
        self.openid_request = self.openid_server.decodeRequest(
            self.openid_parameters)
        assert zisinstance(self.openid_request, CheckIDRequest), (
            'Invalid OpenIDRequest in session')

    def saveRequestInSession(self, key):
        """Save the OpenIDRequest in our session using the given key."""
        query = self.openid_parameters
        assert query.get('openid.mode') == 'checkid_setup', (
            'Can only serialise checkid_setup OpenID requests')

        session = self.getSession()
        # We also store the time with the openid_request so we can clear
        # out old requests after some time, say 1 hour.
        now = time()
        self._sweep(now, session)
        session[key] = (now, query)

    def renderOpenIDResponse(self, openid_response):
        webresponse = self.openid_server.encodeResponse(openid_response)
        response = self.request.response
        response.setStatus(webresponse.code)
        for header, value in webresponse.headers.items():
            response.setHeader(header, value)
        return webresponse.body

    def createPositiveResponse(self):
        """Create a positive assertion OpenIDResponse.

        This method should be called to create the response to
        successful checkid requests.

        If the trust root for the request is in openid_sreg_trustroots,
        then additional user information is included with the
        response.
        """
        assert self.account is not None, (
            'Must be logged in for positive OpenID response')
        assert self.openid_request is not None, (
            'No OpenID request to respond to.')

        if not self.isIdentityOwner():
            return self.createFailedResponse()

        if self.openid_request.idSelect():
            response = self.openid_request.answer(
                True, identity=self.user_identity_url)
        else:
            response = self.openid_request.answer(True)

        return response

    def createFailedResponse(self):
        """Create a failed assertion OpenIDResponse.

        This method should be called to create the response to
        unsuccessful checkid requests.
        """
        assert self.openid_request is not None, (
            'No OpenID request to respond to.')
        response = self.openid_request.answer(False, self.server_url)
        return response


class TestOpenIDView(OpenIDMixin, LaunchpadView):
    """An OpenID Provider endpoint for Launchpad.

    This class implements an OpenID endpoint using the python-openid
    library.  In addition to the normal modes of operation, it also
    implements the OpenID 2.0 identifier select mode.
    
    Note that the checkid_immediate mode is not supported.
    """

    def render(self):
        """Handle all OpenID requests and form submissions."""
        # NB: Will be None if there are no parameters in the request.
        self.openid_request = self.openid_server.decodeRequest(
            self.openid_parameters)

        if self.openid_request.mode == 'checkid_setup':
            referer = self.request.get("HTTP_REFERER")
            if referer:
                self.request.response.setCookie("openid_referer", referer)

            # Log the user out and present the login page so that they can
            # authenticate as somebody else if they want.
            logoutPerson(self.request)
            return self.showLoginPage()
        elif self.openid_request.mode == 'checkid_immediate':
            raise UnexpectedFormData(
                'We do not handle checkid_immediate requests.')
        else:
            return self.renderOpenIDResponse(
                self.openid_server.handleRequest(self.openid_request))


    def storeOpenIDRequestInSession(self):
        # To ensure that the user has seen this page and it was actually the
        # user that clicks the 'Accept' button, we generate a nonce and
        # use it to store the openid_request in the session. The nonce
        # is passed through by the form, but it is only meaningful if
        # it was used to store information in the actual users session,
        # rather than the session of a malicious connection attempting a
        # man-in-the-middle attack.
        nonce = generate_uuid()
        self.saveRequestInSession('nonce' + nonce)
        self.nonce = nonce

    def showLoginPage(self):
        """Render the login dialog."""
        self.storeOpenIDRequestInSession()
        return TestOpenIDLoginView(self.context, self.request, self.nonce)()


class TestOpenIDLoginView(OpenIDMixin, LaunchpadFormView):

    page_title = "Login"
    schema = ITestOpenIDLoginForm
    action_url = '+auth'
    template = ViewPageTemplateFile("../templates/auth.pt")

    def __init__(self, context, request, nonce=None):
        super(TestOpenIDLoginView, self).__init__(context, request)
        self.nonce = nonce

    @property
    def initial_values(self):
        return {'nonce': self.nonce}

    def setUpWidgets(self):
        """Set up the widgets, and restore the OpenID request."""
        super(TestOpenIDLoginView, self).setUpWidgets()

        # Restore the OpenID request.
        widget = self.widgets['nonce']
        widget.visible = False
        if widget.hasValidInput():
            self.nonce = widget.getInputValue()
        if self.nonce is None:
            raise UnexpectedFormData("No OpenID request.")
        self.restoreRequestFromSession('nonce' + self.nonce)

    def validate(self, data):
        """Check that the email address and password are valid for login."""
        loginsource = getUtility(IPlacelessLoginSource)
        principal = loginsource.getPrincipalByLogin(data['email'])
        if principal is None or not principal.validate(data['password']):
            self.addError(
                _("Incorrect password for the provided email address."))

    @action('Continue', name='continue')
    def continue_action(self, action, data):
        email = data['email']
        principal = getUtility(IPlacelessLoginSource).getPrincipalByLogin(
            email)
        logInPrincipal(self.request, principal, email)
        # Update the attribute holding the cached user.
        self._account = principal.account
        return self.renderOpenIDResponse(self.createPositiveResponse())


class PersistentIdentityView(
        TestOpenIDXRDSContentNegotiationMixin, LaunchpadView):
    """Render the OpenID identity page."""

    xrds_template = ViewPageTemplateFile(
        "../templates/persistentidentity-xrds.pt")
