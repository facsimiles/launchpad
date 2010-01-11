# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""The innards of the Bug Heat cronscript."""

__metaclass__ = type
__all__ = []


from zope.component import getUtility
from zope.interface import implements

from canonical.launchpad.interfaces.looptuner import ITunableLoop
from canonical.launchpad.utilities.looptuner import LoopTuner

from lp.bugs.interfaces.bug import IBugSet

class BugHeatCalculator:
    """A class to calculate the heat for a bug."""

    def __init__(self, bug):
        self.bug = bug

    def _getHeatFromPrivacy(self):
        """Return the heat generated by the bug's `private` attribute."""
        if self.bug.private:
            return 150
        else:
            return 0

    def _getHeatFromSecurity(self):
        """Return the heat generated if the bug is security related."""
        if self.bug.security_related:
            return 250
        else:
            return 0

    def _getHeatFromDuplicates(self):
        """Return the heat generated by the bug's duplicates."""
        return self.bug.duplicates.count() * 6

    def _getHeatFromAffectedUsers(self):
        """Return the heat generated by the bug's affected users."""
        return self.bug.users_affected.count() * 4

    def _getHeatFromSubscribers(self):
        """Return the heat generated by the bug's subscribers."""
        direct_subscribers = self.bug.getDirectSubscribers()
        subscribers_from_dupes = self.bug.getSubscribersFromDuplicates()

        return (
            (len(direct_subscribers) + len(subscribers_from_dupes)) * 2)

    def getBugHeat(self):
        """Return the total heat for the current bug."""
        heat_counts = [
            self._getHeatFromAffectedUsers(),
            self._getHeatFromDuplicates(),
            self._getHeatFromPrivacy(),
            self._getHeatFromSecurity(),
            self._getHeatFromSubscribers(),
            ]

        total_heat = 0
        for count in heat_counts:
            total_heat += count

        return total_heat


class BugHeatTunableLoop:
    """An `ITunableLoop` implementation for bug heat calculations."""

    implements(ITunableLoop)

    total_updated = 0

    def __init__(self, transaction, logger, offset=0):
        self.transaction = transaction
        self.logger = logger
        self.offset = offset
        self.total_updated = 0

    def isDone(self):
        """See `ITunableLoop`."""
        # When the main loop has no more Bugs to process it sets
        # offset to None. Until then, it always has a numerical
        # value.
        return self.offset is None

    def __call__(self, chunk_size):
        """Retrieve a batch of Bugs and update their heat.

        See `ITunableLoop`.
        """
        # XXX 2010-01-08 gmb bug=198767:
        #     We cast chunk_size to an integer to ensure that we're not
        #     trying to slice using floats or anything similarly
        #     foolish. We shouldn't have to do this.
        chunk_size = int(chunk_size)

        start = self.offset
        end = self.offset + chunk_size

        self.transaction.begin()
        # XXX 2010-01-08 gmb bug=505850:
        #     This method call should be taken out and shot as soon as
        #     we have a proper permissions system for scripts.
        bugs = list(getUtility(IBugSet).dangerousGetAllBugs()[start:end])

        self.offset = None
        if bugs:
            starting_id = bugs[0].id
            self.logger.info("Updating %i Bugs (starting id: %i)" %
                (len(bugs), starting_id))

        for bug in bugs:
            # We set the starting point of the next batch to the Bug
            # id after the one we're looking at now. If there aren't any
            # bugs this loop will run for 0 iterations and start_id
            # will remain set to None.
            start += 1
            self.offset = start
            self.logger.debug("Updating heat for bug %s" % bug.id)
            bug_heat_calculator = BugHeatCalculator(bug)
            heat = bug_heat_calculator.getBugHeat()
            bug.setHeat(heat)
            self.total_updated += 1

        self.transaction.commit()


class BugHeatUpdater:
    """Takes responsibility for updating bug heat."""

    def __init__(self, transaction, logger):
        self.transaction = transaction
        self.logger = logger

    def updateBugHeat(self):
        """Update the heat scores for all bugs."""
        self.logger.info("Updating heat scores for all bugs")

        loop = BugHeatTunableLoop(self.transaction, self.logger)

        # We use the LoopTuner class to try and get an ideal number of
        # bugs updated for each iteration of the loop (see the LoopTuner
        # documentation for more details).
        loop_tuner = LoopTuner(loop, 2)
        loop_tuner.run()

        self.logger.info(
            "Done updating heat for %s bugs" % loop.total_updated)
