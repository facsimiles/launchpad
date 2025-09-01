#  Copyright 2025 Canonical Ltd.  This software is licensed under the
#  GNU Affero General Public License version 3 (see the file LICENSE).

"""A SOSS (SOSS CVE Tracker) bug exporter"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from lp.app.enums import InformationType
from lp.app.errors import NotFoundError
from lp.bugs.interfaces.cve import ICveSet
from lp.bugs.model.bug import Bug as BugModel
from lp.bugs.model.bugtask import BugTask
from lp.bugs.model.cve import Cve as CveModel
from lp.bugs.model.vulnerability import Vulnerability
from lp.bugs.scripts.soss.models import SOSSRecord
from lp.bugs.scripts.soss.sossimport import (
    DISTRIBUTION_NAME,
    PACKAGE_STATUS_MAP,
    PACKAGE_TYPE_MAP,
    PRIORITY_ENUM_MAP,
)
from lp.registry.interfaces.distribution import IDistributionSet
from lp.registry.model.distribution import Distribution

__all__ = [
    "SOSSExporter",
]

logger = logging.getLogger(__name__)

# Constants moved to module level with proper naming
PRIORITY_ENUM_MAP_REVERSE = {v: k for k, v in PRIORITY_ENUM_MAP.items()}

PACKAGE_TYPE_MAP_REVERSE = {v: k for k, v in PACKAGE_TYPE_MAP.items()}

PACKAGE_STATUS_MAP_REVERSE = {v: k for k, v in PACKAGE_STATUS_MAP.items()}


class SOSSExporter:
    """
    SOSSExporter is used to export Launchpad Vulnerability data to SOSS CVE
    files.
    """

    def __init__(
        self,
        information_type: InformationType = InformationType.PRIVATESECURITY,
        dry_run: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.cve_set = getUtility(ICveSet)
        self.soss = getUtility(IDistributionSet).getByName(DISTRIBUTION_NAME)

        if self.soss is None:
            logger.error("[SOSSExporter] SOSS distribution not found")
            raise NotFoundError("SOSS distribution not found")

    def _get_packages(
        self, bugtasks: List[BugTask]
    ) -> Dict[SOSSRecord.PackageTypeEnum, SOSSRecord.Package]:
        """Get a dict of SOSSRecord.PackageTypeEnum: SOSSRecord.Package from a
        bugtask list.
        """
        packages = defaultdict(list)
        for bugtask in bugtasks:
            pkg = SOSSRecord.Package(
                name=bugtask.target.name,
                channel=SOSSRecord.Channel(
                    value="/".join(s for s in bugtask.channel if s is not None)
                ),
                repositories=bugtask.metadata.get("repositories"),
                status=SOSSRecord.PackageStatusEnum(
                    PACKAGE_STATUS_MAP_REVERSE[bugtask.status]
                ),
                note=bugtask.status_explanation or "",
            )
            packages[PACKAGE_TYPE_MAP_REVERSE[bugtask.packagetype]].append(pkg)

        ordered_packages = {
            k: sorted(packages[k])
            for k in PACKAGE_TYPE_MAP_REVERSE.values()
            if packages[k]
        }

        return ordered_packages

    def _get_cvss(self, cvss: Dict) -> List[SOSSRecord.CVSS]:
        """Get a list of SOSSRecord.CVSS from a cvss dict"""
        cvss_list = []
        for authority in cvss.keys():
            for c in cvss[authority]:
                cvss_list.append(
                    SOSSRecord.CVSS(
                        c.get("source"),
                        c.get("vector"),
                        c.get("baseScore"),
                        c.get("baseSeverity"),
                    )
                )
        return cvss_list

    def to_record(self, cve_sequence: str) -> SOSSRecord:
        """Return a SOSSRecord exporting Launchpad data for the specified
        cve_sequence.
        """
        lp_cve = self._get_launchpad_cve(cve_sequence)
        if lp_cve is None:
            logger.error(f"[SOSSExporter] {cve_sequence} not found")
            return None

        bug = self._find_existing_bug(cve_sequence, lp_cve, self.soss)
        if bug is None:
            logger.error(f"[SOSSExporter] No bug found for {cve_sequence}")
            return None

        vulnerability = self._find_existing_vulnerability(lp_cve, self.soss)
        if vulnerability is None:
            logger.error(
                f"[SOSSExporter] No vulnerability found for {cve_sequence}"
            )
            return None

        # Export bug
        desc_parts = bug.description.rsplit("\n\nReferences:\n")
        references = desc_parts[1].split("\n") if len(desc_parts) > 1 else []

        # Export bug.bugtasks
        packages = self._get_packages(bug.bugtasks)
        assigned_to = (
            bug.bugtasks[0].assignee.name if bug.bugtasks[0].assignee else ""
        )

        # Export vulnerability
        description = vulnerability.description
        public_date = vulnerability.date_made_public
        notes = vulnerability.notes.split("\n") if vulnerability.notes else []
        priority = SOSSRecord.PriorityEnum(
            PRIORITY_ENUM_MAP_REVERSE[vulnerability.importance]
        )
        priority_reason = vulnerability.importance_explanation

        # Export vulnerability.cvss
        cvss = self._get_cvss(vulnerability.cvss)

        candidate = f"CVE-{lp_cve.sequence}"

        return SOSSRecord(
            references=references,
            notes=notes,
            priority=priority,
            priority_reason=priority_reason,
            assigned_to=assigned_to,
            packages=packages,
            candidate=candidate,
            description=description,
            cvss=cvss,
            public_date=self._normalize_date_without_timezone(public_date),
        )

    def _find_existing_bug(
        self,
        cve_sequence: str,
        lp_cve: CveModel,
        distribution: Distribution,
    ) -> Optional[BugModel]:
        """Find existing bug for the given CVE."""
        for vulnerability in lp_cve.vulnerabilities:
            if vulnerability.distribution == distribution:
                bugs = vulnerability.bugs
                if len(bugs) > 1:
                    raise ValueError(
                        "Multiple existing bugs found for CVE ",
                        cve_sequence,
                    )
                if bugs:
                    return bugs[0]
        return None

    def _find_existing_vulnerability(
        self, lp_cve: CveModel, distribution: Distribution
    ) -> Optional[Vulnerability]:
        """Find existing vulnerability for the current distribution"""
        if not lp_cve:
            return None

        vulnerability = next(
            (
                v
                for v in lp_cve.vulnerabilities
                if v.distribution == distribution
            ),
            None,
        )
        return vulnerability

    def _get_launchpad_cve(self, cve_sequence: str) -> Optional[CveModel]:
        """Get CVE from Launchpad."""
        return removeSecurityProxy(self.cve_set[cve_sequence])

    def _normalize_date_without_timezone(
        self, date_obj: datetime
    ) -> Optional[datetime]:
        """Normalize date to no timezone if needed."""
        if date_obj and date_obj.tzinfo is not None:
            return date_obj.replace(tzinfo=None)
        return date_obj
