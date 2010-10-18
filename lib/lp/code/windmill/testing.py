# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Code-specific testing infrastructure for Windmill."""

__metaclass__ = type
__all__ = [
    'CodeWindmillLayer',
    ]


from canonical.testing.layers import BaseWindmillLayer


class CodeWindmillLayer(BaseWindmillLayer):
    """Layer for Code Windmill tests."""

    from canonical.testing import getRootLaunchpadUrl
    base_url = getRootLaunchpadUrl('code')
