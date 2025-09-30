#  Copyright 2025 Canonical Ltd.  This software is licensed under the
#  GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "SVTRecord",
    "SVTImporter",
    "SVTExporter",
]

from lp.bugs.interfaces.bug import IBug
from lp.bugs.interfaces.cve import ICve
from lp.bugs.interfaces.vulnerability import IVulnerability
from lp.registry.interfaces.distribution import IDistribution


class SVTRecord:
    """A dataclass that contains the exact same info as a cve file."""

    def from_str(string: str) -> "SVTRecord":
        """Parse a string and return a SVTRecord."""
        raise NotImplementedError()


class SVTImporter:
    def from_record(
        record: SVTRecord, cve_sequence: str
    ) -> (IBug, IVulnerability):
        """Import a SVTRecord creating a bug and a vulnerability."""
        raise NotImplementedError()

    def checkUserPermissions(user):
        """Checks if the user has permissions to use this handler."""
        raise NotImplementedError()


class SVTExporter:
    def to_record(
        lp_cve: ICve,
        distribution: IDistribution,
        bug: IBug,
        vulnerability: IVulnerability,
    ) -> SVTRecord:
        """Export the bug and vulnerability related to a cve in a distribution
        and return a SVTRecord."""
        raise NotImplementedError()
