# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Module docstring goes here."""

__metaclass__ = type

import datetime
from StringIO import StringIO
import time

from zope.component import getUtility
from zope.interface import Interface
from zope.schema.interfaces import TooShort

from lp.app.validators import LaunchpadValidationError
from lp.blueprints.enums import SpecificationWorkItemStatus
from lp.registry.interfaces.nameblacklist import INameBlacklistSet
from lp.registry.interfaces.person import (
    CLOSED_TEAM_POLICY,
    OPEN_TEAM_POLICY,
    )
from lp.services.database.lpstorm import IStore
from lp.services.fields import (
    BaseImageUpload,
    BlacklistableContentNameField,
    FormattableDate,
    is_public_person_or_closed_team,
    StrippableText,
    WorkItemsText,
    )
from lp.testing import (
    login_person,
    TestCase,
    TestCaseWithFactory,
    )
from lp.testing.layers import DatabaseFunctionalLayer


def make_target():
    """Make a trivial object to be a target of the field setting."""

    class Simple:
        """A simple class to test setting fields on."""

    return Simple()


class TestFormattableDate(TestCase):

    def test_validation_fails_on_bad_data(self):
        field = FormattableDate()
        date_value = datetime.date(
            *(time.strptime('1000-01-01', '%Y-%m-%d'))[:3])
        self.assertRaises(
            LaunchpadValidationError, field.validate, date_value)

    def test_validation_passes_good_data(self):
        field = FormattableDate()
        date_value = datetime.date(
            *(time.strptime('2010-01-01', '%Y-%m-%d'))[:3])
        self.assertIs(None, field.validate(date_value))


class TestStrippableText(TestCase):

    def test_strips_text(self):
        # The set method should strip the string before setting the field.
        target = make_target()
        field = StrippableText(__name__='test', strip_text=True)
        self.assertTrue(field.strip_text)
        field.set(target, '  testing  ')
        self.assertEqual('testing', target.test)

    def test_strips_text_trailing_only(self):
        # The set method strips the trailing whitespace.
        target = make_target()
        field = StrippableText(
            __name__='test', strip_text=True, trailing_only=True)
        self.assertTrue(field.trailing_only)
        field.set(target, '  testing  ')
        self.assertEqual('  testing', target.test)

    def test_default_constructor(self):
        # If strip_text is not set, or set to false, then the text is not
        # stripped when set.
        target = make_target()
        field = StrippableText(__name__='test')
        self.assertFalse(field.strip_text)
        field.set(target, '  testing  ')
        self.assertEqual('  testing  ', target.test)

    def test_setting_with_none(self):
        # The set method is given None, the attribute is set to None
        target = make_target()
        field = StrippableText(__name__='test', strip_text=True)
        field.set(target, None)
        self.assertIs(None, target.test)

    def test_validate_min_contraints(self):
        # The minimum length constraint tests the stripped string.
        field = StrippableText(
            __name__='test', strip_text=True, min_length=1)
        self.assertRaises(TooShort, field.validate, u'  ')

    def test_validate_max_contraints(self):
        # The minimum length constraint tests the stripped string.
        field = StrippableText(
            __name__='test', strip_text=True, max_length=2)
        self.assertEqual(None, field.validate(u'  a  '))


class TestWorkItemsTextAssigneeAndMilestone(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestWorkItemsTextAssigneeAndMilestone, self).setUp()
        self.field = WorkItemsText(__name__='test')

    def test_unknown_assignee_is_rejected(self):
        person_name = 'test-person'
        self.assertRaises(
            LaunchpadValidationError, self.field.getAssignee, person_name)

    def test_validate_valid_assignee(self):
        assignee = self.factory.makePerson()
        self.assertEqual(assignee, self.field.getAssignee(assignee.name))

    def test_validate_unset_assignee(self):
        self.assertIs(None, self.field.getAssignee(None))

    def test_validate_unset_milestone(self):
        self.assertIs(None, self.field.getMilestone(None))

    def test_validate_unknown_milestone(self):
        specification = self.factory.makeSpecification()
        field = self.field.bind(specification)
        self.assertRaises(
            LaunchpadValidationError, field.getMilestone, 'does-not-exist')

    def test_validate_valid_product_milestone(self):
        milestone = self.factory.makeMilestone()
        specification = self.factory.makeSpecification(
            product=milestone.product)
        field = self.field.bind(specification)
        self.assertEqual(milestone, field.getMilestone(milestone.name))

    def test_validate_valid_distro_milestone(self):
        distro = self.factory.makeDistribution()
        milestone = self.factory.makeMilestone(distribution=distro)
        specification = self.factory.makeSpecification(
            distribution=milestone.distribution)
        field = self.field.bind(specification)
        self.assertEqual(milestone, field.getMilestone(milestone.name))

    def test_validate_invalid_milestone(self):
        milestone_name = 'test-milestone'
        self.factory.makeMilestone(name=milestone_name)
        # Milestone exists but is not a target for this spec.
        specification = self.factory.makeSpecification(product=None)
        field = self.field.bind(specification)
        self.assertRaises(
            LaunchpadValidationError, field.getMilestone, milestone_name)


class TestWorkItemsText(TestCase):

    def setUp(self):
        super(TestWorkItemsText, self).setUp()
        self.field = WorkItemsText(__name__='test')

    def test_validate_raises_LaunchpadValidationError(self):
        self.assertRaises(
            LaunchpadValidationError, self.field.validate,
            'This is not a valid work item.')

    def test_single_line_parsing(self):
        work_items_title = 'Test this work item'
        parsed = self.field.parse_line('%s: TODO' % (work_items_title))
        self.assertEqual(parsed['title'], work_items_title)
        self.assertEqual(parsed['status'], SpecificationWorkItemStatus.TODO)

    def test_url_and_colon_in_title(self):
        work_items_title = 'Test this: which is a url: http://www.linaro.org/'
        parsed = self.field.parse_line('%s: TODO' % (work_items_title))
        self.assertEqual(parsed['title'], work_items_title)

    def test_silly_caps_status_parsing(self):
        parsed_upper = self.field.parse_line('Test this work item: TODO    ')
        self.assertEqual(parsed_upper['status'],
                         SpecificationWorkItemStatus.TODO)
        parsed_lower = self.field.parse_line('Test this work item:     todo')
        self.assertEqual(parsed_lower['status'],
                         SpecificationWorkItemStatus.TODO)
        parsed_camel = self.field.parse_line('Test this work item: ToDo')
        self.assertEqual(parsed_camel['status'],
                         SpecificationWorkItemStatus.TODO)

    def test_parse_line_without_status_fails(self):
        # We should require an explicit status to avoid the problem of work
        # items with a url but no status.
        self.assertRaises(
            LaunchpadValidationError, self.field.parse_line,
            'Missing status')

    def test_parse_line_without_title_fails(self):
        self.assertRaises(
            LaunchpadValidationError, self.field.parse_line,
            ':TODO')

    def test_parse_line_without_title_with_assignee_fails(self):
        self.assertRaises(
            LaunchpadValidationError, self.field.parse_line,
            '[test-person] :TODO')

    def test_multi_line_parsing(self):
        title_1 = 'Work item 1'
        title_2 = 'Work item 2'
        work_items_text = "%s: TODO\n%s: POSTPONED" % (title_1, title_2)
        parsed = self.field.parse(work_items_text)
        self.assertEqual(
            parsed, [{'title': title_1,
                      'status': SpecificationWorkItemStatus.TODO,
                      'assignee': None, 'milestone': None, 'sequence': 0},
                     {'title': title_2,
                      'status': SpecificationWorkItemStatus.POSTPONED,
                      'assignee': None, 'milestone': None, 'sequence': 1}])

    def test_parse_assignee(self):
        title = 'Work item 1'
        assignee = 'test-person'
        work_items_text = "[%s]%s: TODO" % (assignee, title)
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['assignee'], assignee)

    def test_parse_assignee_with_space(self):
        title = 'Work item 1'
        assignee = 'test-person'
        work_items_text = "[%s] %s: TODO" % (assignee, title)
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['assignee'], assignee)

    def test_parse_line_with_missing_closing_bracket_for_assignee(self):
        self.assertRaises(
            LaunchpadValidationError, self.field.parse_line,
            "[test-person A single work item: TODO")

    def test_parse_line_with_invalid_status(self):
        self.assertRaises(
            LaunchpadValidationError, self.field.parse_line,
            'Invalid status: FOO')

    def test_parse_line_todo_status(self):
        status = SpecificationWorkItemStatus.TODO.name
        work_items_text = "Just a work item: %s" % status
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['status'].name, status)

    def test_parse_line_done_status(self):
        status = SpecificationWorkItemStatus.DONE.name
        work_items_text = "Just a work item: %s" % status
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['status'].name, status)

    def test_parse_line_postponed_status(self):
        status = SpecificationWorkItemStatus.POSTPONED.name
        work_items_text = "Just a work item: %s" % status
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['status'].name, status)

    def test_parse_line_inprogress_status(self):
        status = SpecificationWorkItemStatus.INPROGRESS.name
        work_items_text = "Just a work item: %s" % status
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['status'].name, status)

    def test_parse_line_blocked_status(self):
        status = SpecificationWorkItemStatus.BLOCKED.name
        work_items_text = "Just a work item: %s" % status
        parsed = self.field.parse_line(work_items_text)
        self.assertEqual(parsed['status'].name, status)

    def test_parse_empty_line_raises(self):
        self.assertRaises(
            AssertionError, self.field.parse_line, "  \t \t ")

    def test_parse_empty_lines_have_no_meaning(self):
        parsed = self.field.parse("\n\n\n\n\n\n\n\n")
        self.assertEqual(parsed, [])

    def test_parse_milestone(self):
        milestone = '2012.02'
        title = "Work item for a milestone"
        work_items_text = "Work items for %s:\n%s: TODO" % (milestone, title)
        parsed = self.field.parse(work_items_text)
        self.assertEqual(parsed, [{'title': title,
                      'status': SpecificationWorkItemStatus.TODO,
                      'assignee': None, 'milestone': milestone, 'sequence': 0}])
        
    def test_parse_multi_milestones(self):
        milestone_1 = '2012.02'
        milestone_2 = '2012.03'
        title_1 = "Work item for a milestone"
        title_2 = "Work item for a later milestone"
        work_items_text = ("Work items for %s:\n%s: POSTPONED\n\nWork items "
                           "for %s:\n%s: TODO" % (milestone_1, title_1,
                                                  milestone_2, title_2))
        parsed = self.field.parse(work_items_text)
        self.assertEqual(parsed,
                         [{'title': title_1,
                           'status': SpecificationWorkItemStatus.POSTPONED,
                           'assignee': None, 'milestone': milestone_1,
                           'sequence': 0},
                          {'title': title_2,
                           'status': SpecificationWorkItemStatus.TODO,
                           'assignee': None, 'milestone': milestone_2,
                           'sequence': 1}])

    def test_parse_orphaned_work_items(self):
        # Work items not in a milestone block belong to the latest specified 
        # milestone.
        milestone_1 = '2012.02'
        milestone_2 = '2012.03'
        title_1 = "Work item for a milestone"
        title_2 = "Work item for a later milestone"
        title_3 = "A work item preceeded by a blank line"
        work_items_text = (
            "Work items for %s:\n%s: POSTPONED\n\nWork items for %s:\n%s: "
            "TODO\n\n%s: TODO" % (milestone_1, title_1, milestone_2, title_2,
                                  title_3))
        parsed = self.field.parse(work_items_text)
        self.assertEqual(parsed, 
                         [{'title': title_1,
                           'status': SpecificationWorkItemStatus.POSTPONED,
                           'assignee': None, 'milestone': milestone_1,
                           'sequence': 0},
                          {'title': title_2,
                           'status': SpecificationWorkItemStatus.TODO,
                           'assignee': None, 'milestone': milestone_2,
                           'sequence': 1},
                          {'title': title_3,
                           'status': SpecificationWorkItemStatus.TODO,
                           'assignee': None, 'milestone': milestone_2,
                           'sequence': 2}])

    def test_sequence_single_workitem(self):
        parsed = self.field.parse("A single work item: TODO")
        self.assertEqual(0, parsed[0]['sequence'])

    def test_only_workitems_get_sequence(self):
        parsed = self.field.parse("A single work item: TODO\n"
                             "A second work item: TODO\n"
                             "\n"
                             "Work items for 2012.02:\n"
                             "Work item for a milestone: TODO\n")
        self.assertEqual([(wi['title'], wi['sequence']) for wi in parsed], 
                         [("A single work item", 0), ("A second work item", 1),
                          ("Work item for a milestone", 2)])
         


class TestBlacklistableContentNameField(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestBlacklistableContentNameField, self).setUp()
        name_blacklist_set = getUtility(INameBlacklistSet)
        self.team = self.factory.makeTeam()
        admin_exp = name_blacklist_set.create(u'fnord', admin=self.team)
        IStore(admin_exp).flush()

    def makeTestField(self):
        """Return testible subclass."""

        class ITestInterface(Interface):
            pass

        class TestField(BlacklistableContentNameField):
            _content_iface = ITestInterface

            def _getByName(self, name):
                return None

        return TestField(__name__='test')

    def test_validate_fails_with_blacklisted_name_anonymous(self):
        # Anonymous users, processes, cannot create a name that matches
        # a blacklisted name.
        field = self.makeTestField()
        date_value = u'fnord'
        self.assertRaises(
            LaunchpadValidationError, field.validate, date_value)

    def test_validate_fails_with_blacklisted_name_not_admin(self):
        # Users who do not adminster a blacklisted name cannot create
        # a matching name.
        field = self.makeTestField()
        date_value = u'fnord'
        login_person(self.factory.makePerson())
        self.assertRaises(
            LaunchpadValidationError, field.validate, date_value)

    def test_validate_passes_for_admin(self):
        # Users in the team that adminsters a blacklisted name may create
        # matching names.
        field = self.makeTestField()
        date_value = u'fnord'
        login_person(self.team.teamowner)
        self.assertEqual(None, field.validate(date_value))


class TestBaseImageUpload(TestCase):
    """Test for the BaseImageUpload field."""

    class ExampleImageUpload(BaseImageUpload):
        dimensions = (192, 192)
        max_size = 100 * 1024

    def test_validation_corrupt_image(self):
        # ValueErrors raised by PIL become LaunchpadValidationErrors.
        field = self.ExampleImageUpload(default_image_resource='dummy')
        image = StringIO(
            '/* XPM */\n'
            'static char *pixmap[] = {\n'
            '"32 32 253 2",\n'
            '  "00 c #01CAA3",\n'
            '  ".. s None c None",\n'
            '};')
        image.filename = 'foo.xpm'
        self.assertRaises(
            LaunchpadValidationError, field.validate, image)

    def test_validation_non_image(self):
        # IOError raised by PIL become LaunchpadValidationErrors.
        field = self.ExampleImageUpload(default_image_resource='dummy')
        image = StringIO('foo bar bz')
        image.filename = 'foo.jpg'
        self.assertRaises(
            LaunchpadValidationError, field.validate, image)


class Test_is_person_or_closed_team(TestCaseWithFactory):
    """ Tests for is_person_or_closed_team()."""

    layer = DatabaseFunctionalLayer

    def test_non_person(self):
        self.assertFalse(is_public_person_or_closed_team(0))

    def test_person(self):
        person = self.factory.makePerson()
        self.assertTrue(is_public_person_or_closed_team(person))

    def test_open_team(self):
        for policy in OPEN_TEAM_POLICY:
            open_team = self.factory.makeTeam(subscription_policy=policy)
            self.assertFalse(
                is_public_person_or_closed_team(open_team),
                "%s is not open" % policy)

    def test_closed_team(self):
        for policy in CLOSED_TEAM_POLICY:
            closed_team = self.factory.makeTeam(subscription_policy=policy)
            self.assertTrue(
                is_public_person_or_closed_team(closed_team),
                "%s is not closed" % policy)
