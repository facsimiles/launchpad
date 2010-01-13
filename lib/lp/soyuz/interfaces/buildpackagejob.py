# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=E0211,E0213

"""BuildPackageJob interfaces."""

__metaclass__ = type

__all__ = [
    'IBuildPackageJob',
    ]

from zope.schema import Int

from canonical.launchpad import _
from lazr.restful.fields import Reference
from lp.buildmaster.interfaces.buildfarmjob import IBuildFarmJob
from lp.services.job.interfaces.job import IJob
from lp.soyuz.interfaces.build import IBuild


class IBuildPackageJob(IBuildFarmJob):
    """A read-only interface for build package jobs."""
    id = Int(title=_('ID'), required=True, readonly=True)

    job = Reference(
        IJob, title=_("Job"), required=True, readonly=True,
        description=_("Data common to all job types."))
