# Copyright 2006 Canonical Ltd.  All rights reserved.

"""XML-RPC APIs for Malone."""

__metaclass__ = type
__all__ = ["FileBugAPI", "ExternalBugTrackerTokenAPI"]

from zope.component import getUtility
from zope.event import notify
from zope.interface import implements

from canonical.launchpad.event import SQLObjectCreatedEvent
from canonical.launchpad.interfaces import (
    IExternalBugTrackerTokenAPI, ILoginTokenSet, IProductSet,
    IPersonSet, IDistributionSet, LoginTokenType, CreateBugParams,
    NotFoundError)
from canonical.launchpad.webapp import canonical_url, LaunchpadXMLRPCView
from canonical.launchpad.xmlrpc import faults

class FileBugAPI(LaunchpadXMLRPCView):
    """The XML-RPC API for filing bugs in Malone."""

    def filebug(self, params):
        """Report a bug in a distribution or product.

        :params: A dict containing the following keys:

        REQUIRED:
          summary: A string
          comment: A string

        OPTIONAL:
          product: The product name, as a string. Default None.
          distro: The distro name, as a string. Default None.
          package: A string, allowed only if distro is specified.
                   Default None.
          security_related: Is this a security vulnerability?
                            Default False.
          subscribers: A list of email addresses. Default None.

        Either product or distro must be provided.
        """
        product = params.get('product')
        distro = params.get('distro')
        package = params.get('package')
        summary = params.get('summary')
        comment = params.get('comment')
        security_related = params.get('security_related')
        subscribers = params.get('subscribers')

        if product and distro:
            return faults.FileBugGotProductAndDistro()

        if product:
            target = getUtility(IProductSet).getByName(product)
            if target is None:
                return faults.NoSuchProduct(product)
        elif distro:
            distro_object = getUtility(IDistributionSet).getByName(distro)

            if distro_object is None:
                return faults.NoSuchDistribution(distro)

            if package:
                try:
                    spname, bpname = distro_object.guessPackageNames(package)
                except NotFoundError:
                    return faults.NoSuchPackage(package)

                target = distro_object.getSourcePackage(spname)
            else:
                target = distro_object
        else:
            return faults.FileBugMissingProductOrDistribution()

        if not summary:
            return faults.RequiredParameterMissing('summary')

        if not comment:
            return faults.RequiredParameterMissing('comment')

        # Convert arguments into values that IBugTarget.createBug
        # understands.
        personset = getUtility(IPersonSet)
        subscriber_list = []
        if subscribers:
            for subscriber_email in subscribers:
                subscriber = personset.getByEmail(subscriber_email)
                if not subscriber:
                    return faults.NoSuchPerson(
                        type="subscriber", email_address=subscriber_email)
                else:
                    subscriber_list.append(subscriber)

        security_related = bool(security_related)

        # Privacy is always set the same as security, by default.
        private = security_related

        params = CreateBugParams(
            owner=self.user, title=summary, comment=comment,
            security_related=security_related, private=private,
            subscribers=subscriber_list)

        bug = target.createBug(params)
        notify(SQLObjectCreatedEvent(bug))

        return canonical_url(bug)


class ExternalBugTrackerTokenAPI(LaunchpadXMLRPCView):
    """The private XML-RPC API for generating bug tracker login tokens."""

    implements(IExternalBugTrackerTokenAPI)

    def newBugTrackerToken(self):
        """Generate a new `LoginToken` for a bug tracker and return it.

        The `LoginToken` will be of `LoginTokenType` BUGTRACKER.
        """
        login_token = getUtility(ILoginTokenSet).new(
            None, None, 'externalbugtrackers@launchpad.net',
            LoginTokenType.BUGTRACKER)

        return login_token.token
