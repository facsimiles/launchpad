#!/usr/bin/python -S
import _pythonpath

import os
from shutil import rmtree
from tempfile import mkdtemp

from bzrlib.transport import get_transport_from_path
from bzrlib.upgrade import upgrade

from canonical.launchpad.interfaces.lpstorm import IStore
from lp.code.bzr import RepositoryFormat
from lp.code.model.branch import Branch
from lp.codehosting.vfs import get_rw_server
from lp.services.scripts.base import (
    LaunchpadScript,
    LaunchpadScriptFailure,
    )

class AlreadyUpgraded(Exception):
    pass

class UpgradeAllBranches(LaunchpadScript):

    def main(self):
        if len(self.args) < 1:
            raise LaunchpadScriptFailure('Please specify a target directory.')
        if len(self.args) > 1:
            raise LaunchpadScriptFailure('Too many arguments.')
        target_dir = self.args[0]
        store = IStore(Branch)
        branches = store.find(
            Branch, Branch.repository_format != RepositoryFormat.BZR_CHK_2A)
        branches.order_by(Branch.unique_name)
        server = get_rw_server()
        server.start_server()
        try:
            self.upgrade_branches(branches, target_dir)
        finally:
            server.stop_server()

    def upgrade_branches(self, branches, target_dir):
        skipped = 0
        for branch in branches:
            try:
                self.upgrade(branch, target_dir)
            except AlreadyUpgraded:
                skipped +=1
        self.logger.info('Skipped %d already-upgraded branches.', skipped)

    def upgrade(self, branch, target_dir):
        temp_location = os.path.join(target_dir, str(branch.id))
        if os.path.exists(temp_location):
            raise AlreadyUpgraded
        self.logger.info(
            'Upgrading branch %s (%s)', branch.unique_name, branch.id)
        bzr_branch = branch.getBzrBranch()
        upgrade_dir = mkdtemp(dir=target_dir)
        try:
            t = get_transport_from_path(upgrade_dir)
            bzr_branch.bzrdir.root_transport.copy_tree_to_transport(t)
            upgrade(t.base)
        except:
            rmtree(upgrade_dir)
            raise
        else:
            os.rename(upgrade_dir, temp_location)


if __name__ == "__main__":
    script = UpgradeAllBranches(
        "upgrade-all-branches", dbuser='upgrade-branches')
    script.lock_and_run()
