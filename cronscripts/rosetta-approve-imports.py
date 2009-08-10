#! /usr/bin/python2.4
#
# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=C0103,W0403

"""Perform auto-approvals and auto-blocks on translation import queue"""

import _pythonpath

from canonical.config import config
from canonical.database.sqlbase import ISOLATION_LEVEL_READ_COMMITTED
from lp.translations.scripts.po_import import AutoApproveProcess
from lp.services.scripts.base import LaunchpadCronScript


class RosettaImportApprover(LaunchpadCronScript):
    def main(self):
        self.txn.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
        process = AutoApproveProcess(self.txn, self.logger)
        self.logger.debug('Starting auto-approval of translation imports')
        process.run()
        self.logger.debug('Completed auto-approval of translation imports')


if __name__ == '__main__':
    script = RosettaImportApprover('rosetta-approve-imports',
        dbuser='poimportapprover')
    script.lock_or_quit()
    try:
        script.run()
    finally:
        script.unlock()

