# Copyright 2011 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Interfaces for access policy service."""


__metaclass__ = type

__all__ = [
    'IAccessPolicyService',
    ]

from zope.schema import Choice

from lazr.restful.declarations import (
    call_with,
    export_as_webservice_entry,
    export_read_operation,
    export_write_operation,
    operation_for_version,
    operation_parameters,
    REQUEST_USER,
    )
from lazr.restful.fields import Reference

from lp import _
from lp.app.interfaces.services import IService
from lp.registry.enums import (
    AccessPolicyType,
    SharingPermission,
    )
from lp.registry.interfaces.person import IPerson
from lp.registry.interfaces.pillar import IPillar


class IAccessPolicyService(IService):

    # XXX 2012-02-24 wallyworld bug 939910
    # Need to export for version 'beta' even though we only want to use it in
    # version 'devel'
    export_as_webservice_entry(publish_web_link=False, as_of='beta')

    def getAccessPolicies():
        """Return the access policy types."""

    def getSharingPermissions():
        """Return the access policy sharing permissions."""

    @export_read_operation()
    @operation_parameters(
        pillar=Reference(IPillar, title=_('Pillar'), required=True))
    @operation_for_version('devel')
    def getPillarObservers(pillar):
        """Return people/teams who can see pillar artifacts."""

    @export_write_operation()
    @call_with(user=REQUEST_USER)
    @operation_parameters(
        pillar=Reference(IPillar, title=_('Pillar'), required=True),
        observer=Reference(IPerson, title=_('Observer'), required=True),
        access_policy=Choice(vocabulary=AccessPolicyType))
    @operation_for_version('devel')
    def addPillarObserver(pillar, observer, access_policy, user):
        """Add an observer with the access policy to a pillar."""

    @export_write_operation()
    @operation_parameters(
        pillar=Reference(IPillar, title=_('Pillar'), required=True),
        observer=Reference(IPerson, title=_('Observer'), required=True),
        access_policy=Choice(vocabulary=AccessPolicyType))
    @operation_for_version('devel')
    def deletePillarObserver(pillar, observer, access_policy):
        """Remove an observer from a pillar.

        :param pillar: the pillar from which to remove access
        :param observer: the person or team to remove
        :param access_policy: if None, remove all access, otherwise just remove
                              the specified access_policy
        """
