# Copyright 2011-2021 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type
__all__ = [
    'StormBase',
    ]

from storm.info import get_obj_info
from storm.locals import (
    Store,
    Storm,
    )
from zope.security.proxy import removeSecurityProxy

from lp.services.propertycache import clear_property_cache


class StormBase(Storm):
    """A safe version of storm.base.Storm to use in launchpad.

    This class adds storm cache management functions to base.Storm.
    """

    def __eq__(self, other):
        """Equality operator.

        Objects compare equal if they have the same class and id, and the id
        is not None.

        This rule allows objects retrieved from different stores to compare
        equal.  Newly-created objects may not yet have an id; in such cases
        we flush the store so that we can find out their id.
        """
        other = removeSecurityProxy(other)
        if self.__class__ != other.__class__:
            return False
        self_obj_info = get_obj_info(self)
        other_obj_info = get_obj_info(other)
        if "primary_vars" not in self_obj_info:
            Store.of(self).flush()
        if "primary_vars" not in other_obj_info:
            Store.of(other).flush()
        self_primary = [var.get() for var in self_obj_info["primary_vars"]]
        other_primary = [var.get() for var in other_obj_info["primary_vars"]]
        return self_primary == other_primary

    def __ne__(self, other):
        """Inverse of __eq__."""
        return not (self == other)

    def __hash__(self):
        """Hash operator.

        We must define __hash__ since we define __eq__ (Python 3 requires
        this), but we need to take care to preserve the invariant that
        objects that compare equal have the same hash value.  Newly-created
        objects may not yet have an id; in such cases we flush the store so
        that we can find out their id.
        """
        obj_info = get_obj_info(self)
        if "primary_vars" not in obj_info:
            Store.of(self).flush()
        primary = [var.get() for var in obj_info["primary_vars"]]
        return hash((self.__class__,) + tuple(primary))

    # XXX: jcsackett 2011-01-20 bug=622648: Much as with the SQLBase,
    # this is not tested.
    def __storm_invalidated__(self):
        """Flush cached properties."""
        clear_property_cache(self)
