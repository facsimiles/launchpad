# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type


from canonical.database.sqlbase import block_implicit_flushes
from lp.registry.interfaces.person import IPerson
from lp.blueprints.interfaces.specification import (
    SpecificationGoalStatus)


@block_implicit_flushes
def specification_goalstatus(spec, event):
    """Update goalstatus if productseries or distroseries is changed."""
    delta = spec.getDelta(
        event.object_before_modification, IPerson(event.user))
    if delta is None:
        return
    if delta.productseries is not None or delta.distroseries is not None:
        spec.goalstatus = SpecificationGoalStatus.PROPOSED
