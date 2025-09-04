#  Copyright 2025 Canonical Ltd.  This software is licensed under the
#  GNU Affero General Public License version 3 (see the file LICENSE).

"""A SOSS (SOSS CVE Tracker) bug exporter"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from lp.app.enums import InformationType
from lp.bugs.model.bug import Bug as BugModel
from lp.bugs.model.bugtask import BugTask
from lp.bugs.model.cve import Cve as CveModel
from lp.bugs.model.vulnerability import Vulnerability
from lp.bugs.scripts.soss.models import SOSSRecord
from lp.bugs.scripts.soss.sossimport import (
    PACKAGE_STATUS_MAP,
    PACKAGE_TYPE_MAP,
    PRIORITY_ENUM_MAP,
)
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
        information_type: InformationType = InformationType.PROPRIETARY,
    ) -> None:
        self.information_type = information_type

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

    def to_record(
        self,
        lp_cve: CveModel,
        distribution: Distribution,
        bug: BugModel,
        vulnerability: Vulnerability,
    ) -> SOSSRecord:
        """Return a SOSSRecord exporting Launchpad data for the specified
        cve_sequence.
        """
        self._validate_to_record_args(lp_cve, distribution, bug, vulnerability)

        # Parse bug
        desc_parts = bug.description.rsplit("\n\nReferences:\n", maxsplit=1)
        references = desc_parts[1].split("\n") if len(desc_parts) > 1 else []

        # Parse bug.bugtasks
        packages = self._get_packages(bug.bugtasks)
        assigned_to = (
            bug.bugtasks[0].assignee.name if bug.bugtasks[0].assignee else ""
        )

        # Parse vulnerability
        public_date = self._normalize_date_without_timezone(
            vulnerability.date_made_public
        )
        notes = vulnerability.notes.split("\n") if vulnerability.notes else []
        priority = SOSSRecord.PriorityEnum(
            PRIORITY_ENUM_MAP_REVERSE[vulnerability.importance]
        )

        return SOSSRecord(
            references=references,
            notes=notes,
            priority=priority,
            priority_reason=vulnerability.importance_explanation,
            assigned_to=assigned_to,
            packages=packages,
            candidate=f"CVE-{lp_cve.sequence}",
            description=vulnerability.description,
            cvss=self._get_cvss(vulnerability.cvss),
            public_date=public_date,
        )

    def _validate_to_record_args(
        self,
        lp_cve: CveModel,
        distribution: Distribution,
        bug: BugModel,
        vulnerability: Vulnerability,
    ):
        required_args = {
            "Cve": lp_cve,
            "Bug": bug,
            "Vulnerability": vulnerability,
            "Distribution": distribution,
        }

        for name, value in required_args.items():
            if value is None:
                logger.error(f"[SOSSExporter] {name} can't be None")
                raise ValueError(f"{name} can't be None")

    def _normalize_date_without_timezone(
        self, date_obj: datetime
    ) -> Optional[datetime]:
        """Normalize date to no timezone if needed."""
        if date_obj and date_obj.tzinfo is not None:
            return date_obj.replace(tzinfo=None)
        return date_obj
