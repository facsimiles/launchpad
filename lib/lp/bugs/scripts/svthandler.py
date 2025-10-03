#  Copyright 2025 Canonical Ltd.  This software is licensed under the
#  GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = [
    "SVTRecord",
    "SVTImporter",
    "SVTExporter",
]

from dataclasses import dataclass

from lp.bugs.interfaces.bug import IBug
from lp.bugs.interfaces.vulnerability import IVulnerability


@dataclass
class SVTRecord:
    """A dataclass that contains the exact same info as a cve file."""

    @classmethod
    def from_str(cls, string: str) -> "SVTRecord":
        """Parse a string and return a SVTRecord."""
        raise NotImplementedError()

    def to_str(self) -> str:
        """Convert the SVTRecord to a string."""
        raise NotImplementedError()


class SVTImporter:

    def from_record(
        self, record: SVTRecord, cve_sequence: str
    ) -> (IBug, IVulnerability):
        """Import a SVTRecord creating a bug and a vulnerability."""
        raise NotImplementedError()

    def checkUserPermissions(self, user):
        """Checks if the user has permissions to use this handler."""
        raise NotImplementedError()


class SVTExporter:

    def to_record(
        bug: IBug,
        vulnerability: IVulnerability,
    ) -> SVTRecord:
        """Export the bug and vulnerability related to a cve in a distribution
        and return a SVTRecord."""
        raise NotImplementedError()

    def checkUserPermissions(self, user):
        """Checks if the user has permissions to use this handler."""
        raise NotImplementedError()
