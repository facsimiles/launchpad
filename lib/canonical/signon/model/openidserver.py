# Copyright 2007-2009 Canonical Ltd.  All rights reserved.
# pylint: disable-msg=E0611,W0212

"""OpenID related database classes."""

__metaclass__ = type
__all__ = [
    'OpenIDAuthorization',
    'OpenIDAuthorizationSet',
    'OpenIDRPSummary',
    'OpenIDRPSummarySet',
    ]


from datetime import datetime
import pytz

from sqlobject import ForeignKey, IntCol, StringCol
from storm.expr import Desc, Or
from zope.component import getUtility
from zope.interface import implements

from canonical.database.constants import DEFAULT, UTC_NOW, NEVER_EXPIRES
from canonical.database.datetimecol import UtcDateTimeCol
from canonical.database.sqlbase import SQLBase, sqlvalues
from canonical.launchpad.interfaces import IMasterStore, IStore
from canonical.launchpad.interfaces.account import AccountStatus
from canonical.launchpad.webapp.interfaces import (
    AUTH_STORE, IStoreSelector, MASTER_FLAVOR)
from canonical.launchpad.webapp.url import urlparse
from canonical.launchpad.webapp.vhosts import allvhosts
from canonical.signon.interfaces.openidserver import (
    IOpenIDAuthorization, IOpenIDAuthorizationSet,
    IOpenIDPersistentIdentity, IOpenIDRPSummary, IOpenIDRPSummarySet)


class OpenIDAuthorization(SQLBase):
    implements(IOpenIDAuthorization)

    _table = 'OpenIDAuthorization'

    @staticmethod
    def _get_store():
        """See `SQLBase`.

        The authorization check should always use the master flavor,
        principally because +rp-preauthorize will create them on GET requests.
        """
        return getUtility(IStoreSelector).get(AUTH_STORE, MASTER_FLAVOR)

    account = ForeignKey(dbName='account', foreignKey='Account', notNull=True)
    client_id = StringCol()
    date_created = UtcDateTimeCol(notNull=True, default=DEFAULT)
    date_expires = UtcDateTimeCol(notNull=True)
    trust_root = StringCol(notNull=True)


class OpenIDAuthorizationSet:
    implements(IOpenIDAuthorizationSet)

    def isAuthorized(self, account, trust_root, client_id):
        """See IOpenIDAuthorizationSet.
        
        The use of the master Store is forced to avoid replication
        race conditions.
        """
        return IMasterStore(OpenIDAuthorization).find(
            OpenIDAuthorization,
            # Use account.id here just incase it is from a different Store.
            OpenIDAuthorization.accountID == account.id,
            OpenIDAuthorization.trust_root == trust_root,
            OpenIDAuthorization.date_expires >= UTC_NOW,
            Or(
                OpenIDAuthorization.client_id == None,
                OpenIDAuthorization.client_id == client_id)).count() > 0

    def authorize(self, account, trust_root, expires, client_id=None):
        """See IOpenIDAuthorizationSet."""
        if expires is None:
            expires = NEVER_EXPIRES

        # It's likely that the account can come from the slave.
        # That's why we are using the ID to create the reference.
        existing = IMasterStore(OpenIDAuthorization).find(
            OpenIDAuthorization,
            accountID=account.id,
            trust_root=trust_root,
            client_id=client_id).one()

        if existing is not None:
            existing.date_created = UTC_NOW
            existing.date_expires = expires
        else:
            OpenIDAuthorization(
                accountID=account.id, trust_root=trust_root,
                date_expires=expires, client_id=client_id
                )

    def getByAccount(self, account):
        """See `IOpenIDAuthorizationSet`."""
        store = IStore(OpenIDAuthorization)
        result = store.find(OpenIDAuthorization, accountID=account.id)
        result.order_by(Desc(OpenIDAuthorization.date_created))
        return result


class OpenIDRPSummary(SQLBase):
    """A summary of the interaction between a `IAccount` and an OpenID RP."""
    implements(IOpenIDRPSummary)
    _table = 'OpenIDRPSummary'

    account = ForeignKey(dbName='account', foreignKey='Account', notNull=True)
    openid_identifier = StringCol(notNull=True)
    trust_root = StringCol(notNull=True)
    date_created = UtcDateTimeCol(notNull=True, default=DEFAULT)
    date_last_used = UtcDateTimeCol(notNull=True, default=DEFAULT)
    total_logins = IntCol(notNull=True, default=1)

    def increment(self, date_used=None):
        """See `IOpenIDRPSummary`.

        :param date_used: an optional datetime the login happened. The current
            datetime is used if date_used is None.
        """
        self.total_logins = self.total_logins + 1
        if date_used is None:
            date_used = datetime.now(pytz.UTC)
        self.date_last_used = date_used


class OpenIDRPSummarySet:
    """A set of OpenID RP Summaries."""
    implements(IOpenIDRPSummarySet)

    def getByIdentifier(self, identifier, only_unknown_trust_roots=False):
        """See `IOpenIDRPSummarySet`."""
        # XXX: flacoste 2008-11-17 bug=274774: Normalize the trust_root
        # in OpenIDRPSummary.
        if only_unknown_trust_roots:
            result = OpenIDRPSummary.select("""
            CASE
                WHEN OpenIDRPSummary.trust_root LIKE '%%/'
                THEN OpenIDRPSummary.trust_root
                ELSE OpenIDRPSummary.trust_root || '/'
            END NOT IN (SELECT trust_root FROM OpenIdRPConfig)
            AND openid_identifier = %s
                """ % sqlvalues(identifier))
        else:
            result = OpenIDRPSummary.selectBy(openid_identifier=identifier)
        return result.orderBy('id')

    def _assert_identifier_is_not_reused(self, account, identifier):
        """Assert no other account in the summaries has the identifier."""
        summaries = OpenIDRPSummary.select("""
            account != %s
            AND openid_identifier = %s
            """ % sqlvalues(account, identifier))
        if summaries.count() > 0:
            raise AssertionError(
                'More than 1 account has the OpenID identifier of %s.' %
                identifier)

    def record(self, account, trust_root, date_used=None):
        """See `IOpenIDRPSummarySet`.

        :param date_used: an optional datetime the login happened. The current
            datetime is used if date_used is None.
        :raise AssertionError: If the account is not ACTIVE.
        :return: An `IOpenIDRPSummary` or None if the trust_root is
            Launchpad or one of its vhosts.
        """
        trust_site = urlparse(trust_root)[1]
        launchpad_site = allvhosts.configs['mainsite'].hostname
        if trust_site.endswith(launchpad_site):
            return None
        if account.status != AccountStatus.ACTIVE:
            raise AssertionError(
                'Account %d is not ACTIVE account.' % account.id)
        identifier = IOpenIDPersistentIdentity(account).openid_identity_url
        self._assert_identifier_is_not_reused(account, identifier)
        if date_used is None:
            date_used = datetime.now(pytz.UTC)
        summary = OpenIDRPSummary.selectOneBy(
            account=account, openid_identifier=identifier,
            trust_root=trust_root)
        if summary is not None:
            # Update the existing summary.
            summary.increment(date_used=date_used)
        else:
            # create a new summary.
            summary = OpenIDRPSummary(
                account=account, openid_identifier=identifier,
                trust_root=trust_root, date_created=date_used,
                date_last_used=date_used, total_logins=1)
        return summary
