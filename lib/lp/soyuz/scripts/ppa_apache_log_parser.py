# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = ['DBUSER', 'get_ppa_file_key']

import re

from lp.archiveuploader.utils import re_isadeb


DBUSER = 'ppalogparser'


def get_ppa_file_key(path):
    split_path = path.split('/')
    if len(split_path) != 9:
        return None

    if re_isadeb.match(split_path[8]) is None:
        return None

    return split_path[1:4] + [split_path[8]]
