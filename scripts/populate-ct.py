#!/usr/bin/python3 -S
#
# Copyright 2026 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

import _pythonpath  # noqa: F401

from lp.archivepublisher.scripts.ctpopulator import CTPopulator

if __name__ == "__main__":
    script = CTPopulator("populate-ct", dbuser="ct-delivery-job")
    script.lock_and_run()
