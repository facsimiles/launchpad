#!/usr/bin/python2.4
# Copyright 2008 Canonical Ltd.  All rights reserved.

"""Process a code import described by the command line arguments.

By 'processing a code import' we mean importing or updating code from a
remote, non-Bazaar, repository.

This script is usually run by the code-import-worker-db.py script that
communicates progress and results to the database.
"""

__metaclass__ = type


# pylint: disable-msg=W0403
import _pythonpath

from optparse import OptionParser

from canonical.codehosting.codeimport.worker import (
    CodeImportSourceDetails, CSCVSImportWorker,
    get_default_bazaar_branch_store, get_default_foreign_tree_store)
from canonical.launchpad import scripts



class CodeImportWorker:

    def __init__(self):
        parser = OptionParser()
        scripts.logger_options(parser)
        options, self.args = parser.parse_args()
        self.logger = scripts.logger(options, 'code-import-worker')

    def main(self):
        source_details = CodeImportSourceDetails.fromArguments(self.args)
        import_worker = CSCVSImportWorker(
            source_details, get_default_foreign_tree_store(),
            get_default_bazaar_branch_store(), self.logger)
        import_worker.run()


if __name__ == '__main__':
    script = CodeImportWorker()
    script.main()
