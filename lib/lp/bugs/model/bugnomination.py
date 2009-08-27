# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=E0611,W0212

"""Database classes related to bug nomination.

A bug nomination is a suggestion from a user that a bug be fixed in a
particular distro series or product series. A bug may have zero, one,
or more nominations.
"""

__metaclass__ = type
__all__ = [
    'BugNomination',
    'BugNominationSet']

from datetime import datetime

import pytz

from zope.component import getUtility
from zope.interface import implements

from sqlobject import ForeignKey, SQLObjectNotFound

from canonical.database.constants import UTC_NOW
from canonical.database.datetimecol import UtcDateTimeCol
from canonical.database.sqlbase import SQLBase
from canonical.database.enumcol import EnumCol

from lp.bugs.adapters.bugchange import BugTaskAdded
from canonical.launchpad.interfaces.launchpad import ILaunchpadCelebrities
from canonical.launchpad.webapp.interfaces import NotFoundError
from lp.bugs.interfaces.bugnomination import (
    BugNominationStatus, BugNominationStatusError, IBugNomination,
    IBugNominationSet)
from lp.registry.interfaces.person import validate_public_person

class BugNomination(SQLBase):
    implements(IBugNomination)
    _table = "BugNomination"

    owner = ForeignKey(
        dbName='owner', foreignKey='Person',
        storm_validator=validate_public_person, notNull=True)
    decider = ForeignKey(
        dbName='decider', foreignKey='Person',
        storm_validator=validate_public_person, notNull=False, default=None)
    date_created = UtcDateTimeCol(notNull=True, default=UTC_NOW)
    date_decided = UtcDateTimeCol(notNull=False, default=None)
    distroseries = ForeignKey(
        dbName='distroseries', foreignKey='DistroSeries',
        notNull=False, default=None)
    productseries = ForeignKey(
        dbName='productseries', foreignKey='ProductSeries',
        notNull=False, default=None)
    bug = ForeignKey(dbName='bug', foreignKey='Bug', notNull=True)
    status = EnumCol(
        dbName='status', notNull=True, schema=BugNominationStatus,
        default=BugNominationStatus.PROPOSED)

    @property
    def target(self):
        """See IBugNomination."""
        return self.distroseries or self.productseries

    def approve(self, approver):
        """See IBugNomination."""
        if self.isApproved():
            # Approving an approved nomination is a no-op.
            return
        self.status = BugNominationStatus.APPROVED
        self.decider = approver
        self.date_decided = datetime.now(pytz.timezone('UTC'))
        targets = []
        if self.distroseries:
            # Figure out which packages are affected in this distro for
            # this bug.
            distribution = self.distroseries.distribution
            distroseries = self.distroseries
            for task in self.bug.bugtasks:
                if not task.distribution == distribution:
                    continue
                if task.sourcepackagename is not None:
                    targets.append(distroseries.getSourcePackage(
                        task.sourcepackagename))
                else:
                    targets.append(distroseries)
        else:
            targets.append(self.productseries)
        for target in targets:
            bug_task = self.bug.addTask(approver, target)
            self.bug.addChange(BugTaskAdded(UTC_NOW, approver, bug_task))

    def decline(self, decliner):
        """See IBugNomination."""
        if self.isApproved():
            raise BugNominationStatusError(
                "Cannot decline an approved nomination.")
        self.status = BugNominationStatus.DECLINED
        self.decider = decliner
        self.date_decided = datetime.now(pytz.timezone('UTC'))

    def isProposed(self):
        """See IBugNomination."""
        return self.status == BugNominationStatus.PROPOSED

    def isDeclined(self):
        """See IBugNomination."""
        return self.status == BugNominationStatus.DECLINED

    def isApproved(self):
        """See IBugNomination."""
        return self.status == BugNominationStatus.APPROVED

    def canApprove(self, person):
        """See IBugNomination."""
        if person.inTeam(getUtility(ILaunchpadCelebrities).admin):
            return True
        for driver in self.target.drivers:
            if person.inTeam(driver):
                return True

        if self.distroseries is not None:
            # For distributions anyone that can upload to the
            # distribution may approve nominations.
            bug_packagenames_and_components = set()
            distribution = self.distroseries.distribution
            for bugtask in self.bug.bugtasks:
                if (bugtask.distribution == distribution
                    and bugtask.sourcepackagename is not None):
                    source_package = self.distroseries.getSourcePackage(
                        bugtask.sourcepackagename)
                    bug_packagenames_and_components.add(
                        bugtask.sourcepackagename)
                    if source_package.latest_published_component is not None:
                        bug_packagenames_and_components.add(
                            source_package.latest_published_component)
            if len(bug_packagenames_and_components) == 0:
                # If the bug isn't targeted to a source package, allow
                # any uploader to approve the nomination.
                bug_packagenames_and_components = set(
                    upload_component.component
                    for upload_component in distribution.uploaders)
            for packagename_or_component in bug_packagenames_and_components:
                if distribution.main_archive.canUpload(
                    person, packagename_or_component):
                    return True

        return False

class BugNominationSet:
    """See IBugNominationSet."""
    implements(IBugNominationSet)

    def get(self, id):
        """See IBugNominationSet."""
        try:
            return BugNomination.get(id)
        except SQLObjectNotFound:
            raise NotFoundError(id)
