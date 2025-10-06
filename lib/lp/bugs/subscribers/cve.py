# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from zope.security.proxy import removeSecurityProxy

from lp.services.database.constants import UTC_NOW


def cve_modified(cve, object_modified_event):
    cve = removeSecurityProxy(cve)
    cve.datemodified = UTC_NOW
