# Copyright 2010-2012 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type


from BeautifulSoup import BeautifulSoup
from zope.component import getUtility
from zope.schema.interfaces import (
    TooLong,
    TooShort,
    )
from zope.security.proxy import removeSecurityProxy

from lp.bugs.browser.bugtarget import (
    FileBugViewBase,
    )
from lp.bugs.interfaces.bug import (
    IBugAddForm,
    IBugSet,
    )
from lp.bugs.publisher import BugsLayer
from lp.registry.enums import InformationType
from lp.services.features.testing import FeatureFixture
from lp.services.webapp.servers import LaunchpadTestRequest
from lp.testing import (
    login,
    login_person,
    person_logged_in,
    TestCaseWithFactory,
    )
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.pages import (
    find_main_content,
    find_tag_by_id,
    )
from lp.testing.views import create_initialized_view


class TestBugTargetFileBugConfirmationMessage(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestBugTargetFileBugConfirmationMessage, self).setUp()
        login('foo.bar@canonical.com')
        self.product = self.factory.makeProduct()

    def test_getAcknowledgementMessage_product(self):
        # If there is not customized confirmation message, a default
        # message is displayed.
        product = self.factory.makeProduct()
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(product))

        # If a product contains a customized bug filing confirmation
        # message, it is retrieved by
        # FilebugViewBase.bug_reported_acknowledgement
        product.bug_reported_acknowledgement = (
            u"We really appreciate your bug report")
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"We really appreciate your bug report",
            view.getAcknowledgementMessage(product))

        # If the custom message is set to a string containing only white,
        # space, the default message is used again.
        product.bug_reported_acknowledgement = ' \t'
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(product))

    def test_getAcknowledgementMessage_product_in_project_group(self):
        # If a product is part of a project group and if the project
        # group has a customized bug filing confirmation message,
        # this message is displayed.
        project_group = self.factory.makeProject()
        product = self.factory.makeProduct(project=project_group)

        # Without any customized bug filing confirmation message, the
        # default message is used.
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(product))

        # If the project group has a customized message, it is used.
        project_group.bug_reported_acknowledgement = (
            "Thanks for filing a bug for one of our many products.")
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thanks for filing a bug for one of our many products.",
            view.getAcknowledgementMessage(product))

        # But if the product itself has a customized message too, this
        # message is used instead of the project group's message.
        product.bug_reported_acknowledgement = (
            u"Thanks for filing a bug for this very special product.")
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thanks for filing a bug for this very special product.",
            view.getAcknowledgementMessage(product))

    def test_getAcknowledgementMessage_product_series_in_project_group(self):
        # If a product_series is part of a project group and if the project
        # group has a customized bug filing confirmation message,
        # this message is displayed.
        project_group = self.factory.makeProject()
        product = self.factory.makeProduct(project=project_group)
        product_series = self.factory.makeProductSeries(product=product)

        # Without any customized bug filing confirmation message, the
        # default message is used.
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(product_series))

        # If the project group has a customized message, it is used.
        project_group.bug_reported_acknowledgement = (
            u"Thanks for filing a bug for one of our many product_seriess.")
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thanks for filing a bug for one of our many product_seriess.",
            view.getAcknowledgementMessage(product_series))

        # But if the product has a customized message too, this
        # message is used instead of the project group's message.
        product.bug_reported_acknowledgement = (
            u"Thanks for filing a bug for this very special product.")
        view = create_initialized_view(product, name='+filebug')
        self.assertEqual(
            u"Thanks for filing a bug for this very special product.",
            view.getAcknowledgementMessage(product_series))

    def test_getAcknowledgementMessage_distribution(self):
        # If there is not customized confirmation message, a default
        # message is displayed.
        distribution = self.factory.makeDistribution()
        view = create_initialized_view(distribution, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(distribution))

        # If a distribution contains a customized bug filing confirmation
        # message, it is retrieved by
        # FilebugViewBase.bug_reported_acknowledgement
        distribution.bug_reported_acknowledgement = (
            u"We really appreciate your bug report")
        view = create_initialized_view(distribution, name='+filebug')
        self.assertEqual(
            u"We really appreciate your bug report",
            view.getAcknowledgementMessage(distribution))

    def test_getAcknowledgementMessage_distributionsourcepackage(self):
        # If there is not customized confirmation message, a default
        # message is displayed.
        dsp = self.factory.makeDistributionSourcePackage()
        view = create_initialized_view(dsp, name='+filebug')
        self.assertEqual(
            u"Thank you for your bug report.",
            view.getAcknowledgementMessage(dsp))

        # If a custom message is defined for a DSP, it is used instead of
        # the default message.
        dsp.bug_reported_acknowledgement = (
            u"We really appreciate your bug report")
        view = create_initialized_view(dsp, name='+filebug')
        self.assertEqual(
            u"We really appreciate your bug report",
            view.getAcknowledgementMessage(dsp))

    def test_getAcknowledgementMessage_dsp_custom_distro_message(self):
        # If a distribution has a customized conformatom message, it
        # is used for bugs filed on DistributionSourcePackages.
        dsp = self.factory.makeDistributionSourcePackage()
        dsp.distribution.bug_reported_acknowledgement = (
            u"Thank you for filing a bug in our distribution")
        view = create_initialized_view(dsp, name='+filebug')
        self.assertEqual(
            u"Thank you for filing a bug in our distribution",
            view.getAcknowledgementMessage(dsp))

        # Bug if a custom message is defined for a DSP, it is used instead of
        # the message for the distribution.
        dsp.bug_reported_acknowledgement = (
            u"Thank you for filing a bug for this DSP")
        view = create_initialized_view(dsp, name='+filebug')
        self.assertEqual(
            u"Thank you for filing a bug for this DSP",
            view.getAcknowledgementMessage(dsp))

    def test_bug_filed_acknowlegdgement_notification(self):
        # When a user files a bug, an acknowledgement notification is added
        # to the response.
        product = self.factory.makeProduct()
        login_person(product.owner)
        create_initialized_view(product, name='+filebug')
        form_data = {
            'title': 'A bug title',
            'comment': 'whatever',
            }
        view = create_initialized_view(product, name='+filebug')
        view.submit_bug_action.success(form_data)
        self.assertEqual(
            ['<p class="last">Thank you for your bug report.</p>'],
            [notification.message
             for notification in view.request.response.notifications])

        # This message can be customized.
        product.bug_reported_acknowledgement = (
            u"We really appreciate your bug report")
        view = create_initialized_view(product, name='+filebug')
        view.submit_bug_action.success(form_data)
        self.assertEqual(
            [u'<p class="last">We really appreciate your bug report</p>'],
            [notification.message
             for notification in view.request.response.notifications])

    def test_bug_filing_view_with_dupe_search_enabled(self):
        # When a user files a bug for a product where searching for
        # duplicate bugs is enabled, he is asked to provide a
        # summary of the bug. This summary is used to find possible
        # existing duplicates f this bug.
        product = self.factory.makeProduct()
        login_person(product.owner)
        product.official_malone = True
        product.enable_bugfiling_duplicate_search = True
        user = self.factory.makePerson()
        login_person(user)
        view = create_initialized_view(
            product, name='+filebug', principal=user)
        html = view.render()
        self.assertIsNot(None, find_tag_by_id(html, 'filebug-search-form'))
        # The main bug filing form is rendered but hidden inside an invisible
        # filebug-container.
        main_content = find_main_content(html)
        filebug_form = main_content.find(id='filebug-form')
        self.assertIsNot(None, filebug_form)
        filebug_form_container = filebug_form.findParents(
            id='filebug-form-container')[0]
        class_attrs = [item.strip()
                       for item in filebug_form_container['class'].split(" ")]
        self.assertTrue('hidden' in class_attrs)

    def test_bug_filing_view_with_dupe_search_disabled(self):
        # When a user files a bug for a product where searching for
        # duplicate bugs is disabled, he can directly enter all
        # details of the bug.
        product = self.factory.makeProduct()
        login_person(product.owner)
        product.official_malone = True
        product.enable_bugfiling_duplicate_search = False
        user = self.factory.makePerson()
        login_person(user)
        view = create_initialized_view(
            product, name='+filebug', principal=user)
        html = view.render()
        self.assertIsNot(None, find_tag_by_id(html, 'filebug-form'))
        # The search form to fing possible duplicates is not shown.
        self.assertIs(None, find_tag_by_id(html, 'filebug-search-form'))


class TestFileBugViewBase(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    class FileBugTestView(FileBugViewBase):
        """A simple subclass."""
        schema = IBugAddForm

        def showFileBugForm(self):
            # Disable redirects on validation failure.
            pass

    def setUp(self):
        super(TestFileBugViewBase, self).setUp()
        self.target = self.factory.makeProduct()
        login_person(self.target.owner)
        self.target.official_malone = True

    def get_form(self, title='Test title', comment='Test comment'):
        return {
            'field.title': title,
            'field.comment': comment,
            'field.actions.submit_bug': 'Submit Bug Request',
            }

    def create_initialized_view(self, form=None):
        """Create and initialize the class without adaption."""
        request = LaunchpadTestRequest(form=form, method='POST')
        view = self.FileBugTestView(self.target, request)
        view.initialize()
        return view

    def test_submit_comment_empty_error(self):
        # The comment cannot be an empty string.
        form = self.get_form(comment='')
        view = self.create_initialized_view(form=form)
        self.assertEqual(1, len(view.errors))
        self.assertEqual(
            'Provide details about the issue.', view.getFieldError('comment'))

    def test_submit_comment_whitespace_only_error(self):
        # The comment cannot be a whitespace only string.
        form = self.get_form(comment=' ')
        view = self.create_initialized_view(form=form)
        self.assertEqual(2, len(view.errors))
        self.assertIsInstance(view.errors[0].errors, TooShort)
        self.assertEqual(
            'Provide details about the issue.', view.errors[1])

    def test_submit_comment_too_large_error(self):
        # The comment cannot exceed the max length of 50000.
        comment = 'x' * 50001
        form = self.get_form(comment=comment)
        view = self.create_initialized_view(form=form)
        self.assertEqual(2, len(view.errors))
        self.assertIsInstance(view.errors[0].errors, TooLong)
        message_start = 'The description is too long'
        self.assertTrue(
            view.getFieldError('comment').startswith(message_start))

    def test_submit_comment_max(self):
        # The comment can be as large as 50000.
        form = self.get_form(comment='x' * 50000)
        view = self.create_initialized_view(form=form)
        self.assertEqual(0, len(view.errors))
        self.assertTrue(view.added_bug is not None)


class TestFileBugReportingGuidelines(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_filebug_reporting_details(self):
        product = self.factory.makeProduct()
        login_person(product.owner)
        product.bug_reporting_guidelines = "Include bug details"
        view = create_initialized_view(
            product, '+filebug-reporting-guidelines')
        expected_guidelines = [{
            "source": product.displayname, "content": u"Include bug details",
            }]
        self.assertEqual(expected_guidelines, view.bug_reporting_guidelines)

    def filebug_via_view(self, private_bugs=False, information_type=None):
        feature_flag = {
            'disclosure.show_information_type_in_ui.enabled': 'on'}
        form = {
            'field.title': 'A bug',
            'field.comment': 'A comment',
            'field.actions.submit_bug': 'Submit Bug Request',
        }
        if information_type:
            form['field.information_type'] = information_type
        product = self.factory.makeProduct(official_malone=True)
        if private_bugs:
            removeSecurityProxy(product).private_bugs = True
        with FeatureFixture(feature_flag):
            with person_logged_in(product.owner):
                view = create_initialized_view(
                    product, '+filebug', form=form, principal=product.owner)
                bug_url = view.request.response.getHeader('Location')
                bug_number = bug_url.split('/')[-1]
                return getUtility(IBugSet).getByNameOrID(bug_number)

    def test_filebug_default_information_type(self):
        # If we don't specify the bug's information_type, it is PUBLIC for
        # products with private_bugs=False.
        bug = self.filebug_via_view()
        self.assertEqual(InformationType.PUBLIC, bug.information_type)

    def test_filebug_set_information_type(self):
        # When we specify the bug's information_type, it is set.
        bug = self.filebug_via_view(information_type='EMBARGOEDSECURITY')
        self.assertEqual(
            InformationType.EMBARGOEDSECURITY, bug.information_type)

    def test_filebug_information_type_with_private_bugs(self):
        # If we don't specify the bug's information_type, it is USERDATA for
        # products with private_bugs=True.
        bug = self.filebug_via_view(private_bugs=True)
        self.assertEqual(InformationType.USERDATA, bug.information_type)

    def test_filebug_information_type_vocabulary(self):
        # The vocabulary for information_type when filing a bug is created
        # correctly.
        feature_flags = {
            'disclosure.show_information_type_in_ui.enabled': 'on',
            'disclosure.proprietary_information_type.disabled': 'on',
            'disclosure.display_userdata_as_private.enabled': 'on'}
        product = self.factory.makeProduct(official_malone=True)
        with FeatureFixture(feature_flags):
            with person_logged_in(product.owner):
                view = create_initialized_view(
                    product, '+filebug', principal=product.owner)
                html = view.render()
                soup = BeautifulSoup(html)
        self.assertEqual(u'Private', soup.find('label', text="Private"))
        self.assertIs(None, soup.find('label', text="User Data"))
        self.assertIs(None, soup.find('label', text="Proprietary"))


class TestFileBugSourcePackage(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_filebug_works_on_official_package_branch(self):
        # It should be possible to file a bug against a source package
        # when there is an official package branch.
        user = self.factory.makePerson()
        sourcepackage = self.factory.makeSourcePackage('my-package')
        self.factory.makeRelatedBranchesForSourcePackage(
            sourcepackage=sourcepackage)
        removeSecurityProxy(sourcepackage.distribution).official_malone = True
        login_person(user)

        view = create_initialized_view(
            context=sourcepackage.distribution, name='+filebug',
            form={
                'field.title': 'A bug',
                'field.comment': 'A comment',
                'field.bugtarget.distribution': (
                    sourcepackage.distribution.name),
                'field.packagename': 'my-package',
                'field.actions.submit_bug': 'Submit Bug Request',
            }, layer=BugsLayer, principal=user)
        msg = "\n".join([
            notification.message
            for notification in view.request.response.notifications])
        self.assertIn("Thank you for your bug report.", msg)
