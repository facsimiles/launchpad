# Copyright 2006 Canonical Ltd.  All rights reserved.

__metaclass__ = type

import re
import unittest

from zope.interface import providedBy
from zope.testing.doctestunit import DocTestSuite

from lazr.lifecycle.snapshot import Snapshot

from canonical.launchpad.ftests import login
from canonical.launchpad.searchbuilder import all, any
from canonical.testing import LaunchpadFunctionalLayer

from lp.bugs.interfaces.bugtask import BugTaskImportance, BugTaskStatus
from lp.bugs.model.bugtask import build_tag_search_clauses
from lp.testing import TestCase
from lp.testing.factory import LaunchpadObjectFactory


class TestBugTaskDelta(unittest.TestCase):

    layer = LaunchpadFunctionalLayer

    def setUp(self):
        login('foo.bar@canonical.com')
        self.factory = LaunchpadObjectFactory()

    def test_get_empty_delta(self):
        # getDelta() should return None when no change has been made.
        bug_task = self.factory.makeBugTask()
        self.assertEqual(bug_task.getDelta(bug_task), None)

    def test_get_mismatched_delta(self):
        # getDelta() should raise TypeError when different types of
        # bug tasks are passed in.
        product = self.factory.makeProduct()
        product_bug_task = self.factory.makeBugTask(target=product)
        distro_source_package = self.factory.makeDistributionSourcePackage()
        distro_source_package_bug_task = self.factory.makeBugTask(
            target=distro_source_package)
        self.assertRaises(
            TypeError, product_bug_task.getDelta,
            distro_source_package_bug_task)

    def check_delta(self, bug_task_before, bug_task_after, **expected_delta):
        # Get a delta between one bug task and another, then compare
        # the contents of the delta with expected_delta (a dict, or
        # something that can be dictified). Anything not mentioned in
        # expected_delta is assumed to be None in the delta.
        delta = bug_task_after.getDelta(bug_task_before)
        expected_delta.setdefault('bugtask', bug_task_after)
        names = set(
            name for interface in providedBy(delta) for name in interface)
        for name in names:
            self.assertEquals(
                getattr(delta, name), expected_delta.get(name))

    def test_get_bugwatch_delta(self):
        # Exercise getDelta() with a change to bugwatch.
        user = self.factory.makePerson()
        bug_task = self.factory.makeBugTask()
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        bug_watch = self.factory.makeBugWatch(bug=bug_task.bug)
        bug_task.bugwatch = bug_watch

        self.check_delta(
            bug_task_before_modification, bug_task,
            bugwatch=dict(old=None, new=bug_watch))

    def test_get_target_delta(self):
        # Exercise getDelta() with a change to target.
        user = self.factory.makePerson()
        product = self.factory.makeProduct(owner=user)
        bug_task = self.factory.makeBugTask(target=product)
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        new_product = self.factory.makeProduct(owner=user)
        bug_task.transitionToTarget(new_product)

        self.check_delta(
            bug_task_before_modification, bug_task,
            target=dict(old=product, new=new_product))

    def test_get_milestone_delta(self):
        # Exercise getDelta() with a change to milestone.
        user = self.factory.makePerson()
        product = self.factory.makeProduct(owner=user)
        bug_task = self.factory.makeBugTask(target=product)
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        milestone = self.factory.makeMilestone(product=product)
        bug_task.milestone = milestone

        self.check_delta(
            bug_task_before_modification, bug_task,
            milestone=dict(old=None, new=milestone))

    def test_get_assignee_delta(self):
        # Exercise getDelta() with a change to assignee.
        user = self.factory.makePerson()
        product = self.factory.makeProduct(owner=user)
        bug_task = self.factory.makeBugTask(target=product)
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        bug_task.transitionToAssignee(user)

        self.check_delta(
            bug_task_before_modification, bug_task,
            assignee=dict(old=None, new=user))

    def test_get_status_delta(self):
        # Exercise getDelta() with a change to status.
        user = self.factory.makePerson()
        product = self.factory.makeProduct(owner=user)
        bug_task = self.factory.makeBugTask(target=product)
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        bug_task.transitionToStatus(BugTaskStatus.FIXRELEASED, user)

        self.check_delta(
            bug_task_before_modification, bug_task,
            status=dict(old=bug_task_before_modification.status,
                        new=bug_task.status))

    def test_get_importance_delta(self):
        # Exercise getDelta() with a change to importance.
        user = self.factory.makePerson()
        product = self.factory.makeProduct(owner=user)
        bug_task = self.factory.makeBugTask(target=product)
        bug_task_before_modification = Snapshot(
            bug_task, providing=providedBy(bug_task))

        bug_task.transitionToImportance(BugTaskImportance.HIGH, user)

        self.check_delta(
            bug_task_before_modification, bug_task,
            importance=dict(old=bug_task_before_modification.importance,
                            new=bug_task.importance))


def normalize_whitespace(string):
    """Replace all sequences of whitespace with a single space."""
    return re.sub(r'\s+', ' ', string)


class TestBugTaskTagSearchClauses(TestCase):

    def searchClause(self, tag_spec):
        return " ".join(build_tag_search_clauses(tag_spec))

    def assertEqualIgnoringWhitespace(self, expected, observed):
        return self.assertEqual(
            normalize_whitespace(expected),
            normalize_whitespace(observed))

    def test_single_tag_presence(self):
        # The WHERE clause to test for the presence of a single tag.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'fred')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_single_tag_absence(self):
        # The WHERE clause to test for the absence of a single tag.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'-fred')),
            """BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_any_tag_presence(self):
        # The WHERE clause to test for the presence of any tag.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'*')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag)""")

    def test_any_tag_absence(self):
        # The WHERE clause to test for the absence of any tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'-*')),
            """BugTask.bug NOT IN
                 (SELECT bug FROM BugTag)""")

    def test_multiple_tag_presence(self):
        # The WHERE clause to test for the presence of any of several
        # tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'fred', u'bob')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  UNION
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_multiple_tag_absence(self):
        # The WHERE clause to test for the absence of any of several
        # tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'-fred', u'-bob')),
            """BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  INTERSECT
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_multiple_tag_presence_all(self):
        # The WHERE clause to test for the presence of all specified
        # tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(all(u'fred', u'bob')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  INTERSECT
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_multiple_tag_absence_all(self):
        # The WHERE clause to test for the absence of all specified
        # tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(all(u'-fred', u'-bob')),
            """BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  UNION
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')""")

    def test_mixed_tags(self):
        # The WHERE clause to test for the presence of one or more
        # tags or the absence of one or more other tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'fred', u'-bob')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'fred')
               OR BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob')""")
        self.assertEqualIgnoringWhitespace(
            self.searchClause(any(u'fred', u'-bob', u'eric', u'-harry')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'eric'
                  UNION
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')
               OR BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  INTERSECT
                  SELECT bug FROM BugTag
                   WHERE tag = 'harry')""")

    def test_mixed_tags_all(self):
        # The WHERE clause to test for the presence of one or more
        # tags and the absence of one or more other tags.
        self.assertEqualIgnoringWhitespace(
            self.searchClause(all(u'fred', u'-bob')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                    WHERE tag = 'fred')
               AND BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob')""")
        self.assertEqualIgnoringWhitespace(
            self.searchClause(all(u'fred', u'-bob', u'eric', u'-harry')),
            """BugTask.bug IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'eric'
                  INTERSECT
                  SELECT bug FROM BugTag
                   WHERE tag = 'fred')
               AND BugTask.bug NOT IN
                 (SELECT bug FROM BugTag
                   WHERE tag = 'bob'
                  UNION
                  SELECT bug FROM BugTag
                   WHERE tag = 'harry')""")





def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBugTaskDelta))
    suite.addTest(unittest.makeSuite(TestBugTaskTagSearchClauses))
    suite.addTest(DocTestSuite('lp.bugs.model.bugtask'))
    return suite
