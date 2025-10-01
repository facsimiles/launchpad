# Copyright 2012-2020 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""CVE related tests."""

from datetime import datetime, timezone

from testtools.matchers import MatchesStructure
from testtools.testcase import ExpectedException
from zope.component import getUtility
from zope.security.interfaces import ForbiddenAttribute, Unauthorized
from zope.security.management import checkPermission
from zope.security.proxy import removeSecurityProxy

from lp.app.enums import InformationType
from lp.bugs.interfaces.bugtasksearch import BugTaskSearchParams
from lp.bugs.interfaces.cve import CveStatus, ICveSet
from lp.testing import (
    TestCaseWithFactory,
    admin_logged_in,
    login_person,
    person_logged_in,
    verifyObject,
)
from lp.testing.layers import DatabaseFunctionalLayer


class TestCveSet(TestCaseWithFactory):
    """Tests for CveSet."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        """Create a few bugtasks and CVEs."""
        super().setUp()
        self.distroseries = self.factory.makeDistroSeries()
        self.bugs = []
        self.cves = []
        self.cve_index = 0
        with person_logged_in(self.distroseries.owner):
            for _ in range(4):
                task = self.factory.makeBugTask(target=self.distroseries)
                bug = task.bug
                self.bugs.append(bug)
                cve = self.makeCVE()
                self.cves.append(cve)
                bug.linkCVE(cve, self.distroseries.owner)

    def makeCVE(self):
        """Create a CVE."""
        self.cve_index += 1
        return self.factory.makeCVE("2000-%04i" % self.cve_index)

    def test_CveSet_implements_ICveSet(self):
        cveset = getUtility(ICveSet)
        self.assertTrue(verifyObject(ICveSet, cveset))

    def test_getBugCvesForBugTasks(self):
        # ICveSet.getBugCvesForBugTasks() returns tuples (bug, cve)
        # for the given bugtasks.
        bugtasks = self.distroseries.searchTasks(
            BugTaskSearchParams(self.distroseries.owner, has_cve=True)
        )
        bug_cves = getUtility(ICveSet).getBugCvesForBugTasks(bugtasks)
        found_bugs = [bug for bug, cve in bug_cves]
        found_cves = [cve for bug, cve in bug_cves]
        self.assertEqual(self.bugs, found_bugs)
        self.assertEqual(self.cves, found_cves)

    def test_getBugCvesForBugTasks_with_mapper(self):
        # ICveSet.getBugCvesForBugTasks() takes a function f as an
        # optional argeument. This function is applied to each CVE
        # related to the given bugs; the method return a sequence of
        # tuples (bug, f(cve)).
        def cve_name(cve):
            return cve.displayname

        bugtasks = self.distroseries.searchTasks(
            BugTaskSearchParams(self.distroseries.owner, has_cve=True)
        )
        bug_cves = getUtility(ICveSet).getBugCvesForBugTasks(
            bugtasks, cve_name
        )
        found_bugs = [bug for bug, cve in bug_cves]
        cve_data = [cve for bug, cve in bug_cves]
        self.assertEqual(self.bugs, found_bugs)
        expected = [
            "CVE-2000-0001",
            "CVE-2000-0002",
            "CVE-2000-0003",
            "CVE-2000-0004",
        ]
        self.assertEqual(expected, cve_data)

    def test_getBugCveCount(self):
        login_person(self.factory.makePerson())

        base = getUtility(ICveSet).getBugCveCount()
        bug1 = self.factory.makeBug()
        bug2 = self.factory.makeBug()
        cve1 = self.factory.makeCVE(sequence="2099-1234")
        cve2 = self.factory.makeCVE(sequence="2099-2468")
        self.assertEqual(base, getUtility(ICveSet).getBugCveCount())
        cve1.linkBug(bug1)
        self.assertEqual(base + 1, getUtility(ICveSet).getBugCveCount())
        cve1.linkBug(bug2)
        self.assertEqual(base + 2, getUtility(ICveSet).getBugCveCount())
        cve2.linkBug(bug1)
        self.assertEqual(base + 3, getUtility(ICveSet).getBugCveCount())
        cve1.unlinkBug(bug1)
        cve1.unlinkBug(bug2)
        cve2.unlinkBug(bug1)
        self.assertEqual(base, getUtility(ICveSet).getBugCveCount())


class TestBugLinks(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_link_and_unlink(self):
        login_person(self.factory.makePerson())

        bug1 = self.factory.makeBug()
        bug2 = self.factory.makeBug()
        cve1 = self.factory.makeCVE(sequence="2099-1234")
        cve2 = self.factory.makeCVE(sequence="2099-2468")
        self.assertContentEqual([], bug1.cves)
        self.assertContentEqual([], bug2.cves)
        self.assertContentEqual([], cve1.bugs)
        self.assertContentEqual([], cve2.bugs)

        cve1.linkBug(bug1)
        cve2.linkBug(bug1)
        cve1.linkBug(bug2)
        self.assertContentEqual([bug1, bug2], cve1.bugs)
        self.assertContentEqual([bug1], cve2.bugs)
        self.assertContentEqual([cve1, cve2], bug1.cves)
        self.assertContentEqual([cve1], bug2.cves)

        cve1.unlinkBug(bug1)
        self.assertContentEqual([bug2], cve1.bugs)
        self.assertContentEqual([bug1], cve2.bugs)
        self.assertContentEqual([cve2], bug1.cves)
        self.assertContentEqual([cve1], bug2.cves)

        cve1.unlinkBug(bug2)
        self.assertContentEqual([], cve1.bugs)
        self.assertContentEqual([bug1], cve2.bugs)
        self.assertContentEqual([cve2], bug1.cves)
        self.assertContentEqual([], bug2.cves)


class TestCve(TestCaseWithFactory):
    """Tests for Cve fields and methods."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super().setUp()
        self.cve = self.factory.makeCVE("2025-9999")

    def test_cveset_new_method_optional_parameters(self):
        cve = getUtility(ICveSet).new(
            sequence="2099-1234",
            description="A critical vulnerability",
            status=CveStatus.CANDIDATE,
        )
        self.assertThat(
            cve,
            MatchesStructure.byEquality(
                sequence="2099-1234",
                status=CveStatus.CANDIDATE,
                description="A critical vulnerability",
                date_made_public=None,
                discovered_by=None,
                cvss={},
            ),
        )

    def test_cveset_new_method_parameters(self):
        today = datetime.now(tz=timezone.utc)
        cvss = {"nvd": ["CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"]}
        cve = getUtility(ICveSet).new(
            sequence="2099-1234",
            description="A critical vulnerability",
            status=CveStatus.CANDIDATE,
            date_made_public=today,
            discovered_by="A person",
            cvss=cvss,
        )
        self.assertThat(
            cve,
            MatchesStructure.byEquality(
                sequence="2099-1234",
                status=CveStatus.CANDIDATE,
                description="A critical vulnerability",
                date_made_public=today,
                discovered_by="A person",
                cvss=cvss,
            ),
        )

    def test_cve_date_made_public_invalid_values(self):
        invalid_values = [
            "",
            "abcd",
            {"a": 1},
            [1, "a", "2", "b"],
            "2022-01-01",
        ]
        cve = self.factory.makeCVE(
            sequence="2099-1234",
            description="A critical vulnerability",
            cvestate=CveStatus.CANDIDATE,
        )
        for invalid_value in invalid_values:
            with ExpectedException(TypeError, "Expected datetime,.*"):
                removeSecurityProxy(cve).date_made_public = invalid_value

    def test_cve_cvss_invalid_values(self):
        invalid_values = ["", "abcd", "2022-01-01", datetime.now()]
        cve = self.factory.makeCVE(
            sequence="2099-1234",
            description="A critical vulnerability",
            cvestate=CveStatus.CANDIDATE,
        )
        for invalid_value in invalid_values:
            with ExpectedException(AssertionError):
                removeSecurityProxy(cve).cvss = invalid_value

    def test_cvss_value_returned_when_null(self):
        cve = self.factory.makeCVE(
            sequence="2099-1234",
            description="A critical vulnerability",
            cvestate=CveStatus.CANDIDATE,
        )
        cve = removeSecurityProxy(cve)
        self.assertIsNone(cve._cvss)
        self.assertEqual({}, cve.cvss)

    def test_getDistributionVulnerability(self):
        cve = self.factory.makeCVE(sequence="2099-1234")
        distribution = self.factory.makeDistribution(
            information_type=InformationType.PROPRIETARY
        )
        vulnerability = self.factory.makeVulnerability(
            distribution=distribution,
            cve=cve,
            information_type=InformationType.PROPRIETARY,
        )

        # getDistributionVulnerability returns the vulnerability although we
        # are not logged in
        self.assertEqual(
            vulnerability, cve.getDistributionVulnerability(distribution)
        )

        # As we are not logged as an user, cve.vulnerabilities is empty
        self.assertEqual(len(list(cve.vulnerabilities)), 0)

        # Admin can see the PROPRIETARY vulnerability
        with admin_logged_in():
            self.assertEqual(vulnerability, cve.vulnerabilities[0])

    def test_cve_permissions_anonymous(self):
        """Test that anonymous user cannot view, edit or delete."""
        self.assertFalse(checkPermission("launchpad.View", self.cve))
        self.assertFalse(checkPermission("launchpad.Edit", self.cve))
        self.assertFalse(checkPermission("launchpad.Delete", self.cve))

    def test_cve_permissions_authenticated(self):
        """Test that logged in user can view but not edit or delete."""
        with person_logged_in(self.factory.makePerson()):
            self.assertTrue(checkPermission("launchpad.View", self.cve))
            self.assertFalse(checkPermission("launchpad.Edit", self.cve))
            self.assertFalse(checkPermission("launchpad.Delete", self.cve))

    def test_cve_permissions_admin(self):
        """Test that admin can view but not edit or delete."""
        with admin_logged_in():
            self.assertTrue(checkPermission("launchpad.View", self.cve))
            self.assertFalse(checkPermission("launchpad.Edit", self.cve))
            self.assertFalse(checkPermission("launchpad.Delete", self.cve))

    def test_cve_readonly(self):
        """Test that app code cannot update Cve attributes, but
        InternalScripts can."""
        failure_regex = ".*InternalScriptsOnly"

        with ExpectedException(Unauthorized, failure_regex):
            self.cve.sequence = "2099-9876"
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.status = CveStatus.DEPRECATED
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.description = "example"
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.datecreated = datetime.utcnow()
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.datemodified = datetime.utcnow()
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.references = []
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.date_made_public = datetime.utcnow()
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.discovered_by = "example person"
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.cvss = {"example authority": ["example score"]}
        with ExpectedException(Unauthorized, failure_regex):
            self.cve.metadata = {"meta": "data"}

        # It is forbidden to use cve._cvss
        with ExpectedException(ForbiddenAttribute):
            self.cve._cvss = {"example authority": ["example score"]}
