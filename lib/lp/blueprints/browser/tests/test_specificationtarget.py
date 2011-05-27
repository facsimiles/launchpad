# Copyright 2009-2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type


from BeautifulSoup import BeautifulSoup

from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from canonical.launchpad.testing.pages import find_tag_by_id
from canonical.testing.layers import DatabaseFunctionalLayer
from lp.blueprints.interfaces.specificationtarget import (
    IHasSpecifications,
    ISpecificationTarget,
    )
from lp.app.enums import ServiceUsage
from lp.blueprints.browser.specificationtarget import HasSpecificationsView
from lp.blueprints.interfaces.specification import ISpecificationSet
from lp.blueprints.publisher import BlueprintsLayer
from lp.testing import (
    login_person,
    TestCaseWithFactory,
    )
from lp.testing.matchers import IsConfiguredBatchNavigator
from lp.testing.views import (
    create_view,
    create_initialized_view,
    )


class TestRegisterABlueprintButtonView(TestCaseWithFactory):
    """Test specification menus links."""
    layer = DatabaseFunctionalLayer

    def verify_view(self, context, name):
        view = create_view(
            context, '+register-a-blueprint-button')
        self.assertEqual(
            'http://blueprints.launchpad.dev/%s/+addspec' % name,
            view.target_url)
        self.assertTrue(
            '<div id="involvement" class="portlet involvement">' in view())

    def test_specificationtarget(self):
        context = self.factory.makeProduct(name='almond')
        self.assertTrue(ISpecificationTarget.providedBy(context))
        self.verify_view(context, context.name)

    def test_adaptable_to_specificationtarget(self):
        context = self.factory.makeProject(name='hazelnut')
        self.assertFalse(ISpecificationTarget.providedBy(context))
        self.verify_view(context, context.name)

    def test_sprint(self):
        # Sprints are a special case. They are not ISpecificationTargets,
        # nor can they be adapted to a ISpecificationTarget,
        # but can create a spcification for a ISpecificationTarget.
        context = self.factory.makeSprint(title='Walnut', name='walnut')
        self.assertFalse(ISpecificationTarget.providedBy(context))
        self.verify_view(context, 'sprints/%s' % context.name)


class TestHasSpecificationsViewInvolvement(TestCaseWithFactory):
    """Test specification menus links."""
    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.user = self.factory.makePerson(name="macadamia")
        login_person(self.user)

    def verify_involvment(self, context):
        self.assertTrue(IHasSpecifications.providedBy(context))
        view = create_view(
            context, '+specs', layer=BlueprintsLayer, principal=self.user)
        self.assertTrue(
            '<div id="involvement" class="portlet involvement">' in view())

    def test_specificationtarget(self):
        context = self.factory.makeProduct(name='almond')
        naked_product = removeSecurityProxy(context)
        naked_product.blueprints_usage = ServiceUsage.LAUNCHPAD
        self.verify_involvment(context)

    def test_adaptable_to_specificationtarget(self):
        # A project should adapt to the products within to determine
        # involvment.
        context = self.factory.makeProject(name='hazelnut')
        product = self.factory.makeProduct(project=context)
        naked_product = removeSecurityProxy(product)
        naked_product.blueprints_usage = ServiceUsage.LAUNCHPAD
        self.verify_involvment(context)

    def test_sprint(self):
        context = self.factory.makeSprint(title='Walnut', name='walnut')
        self.verify_involvment(context)

    def test_person(self):
        context = self.factory.makePerson(name='pistachio')
        self.assertTrue(IHasSpecifications.providedBy(context))
        view = create_view(
            context, '+specs', layer=BlueprintsLayer, principal=self.user)
        self.assertFalse(
            '<div id="involvement" class="portlet involvement">' in view())

    def test_specs_batch(self):
        # Some pages turn up in very large contexts and so batch. E.g.
        # Distro:+assignments which uses SpecificationAssignmentsView, a
        # subclass.
        person = self.factory.makePerson()
        view = create_initialized_view(person, name='+assignments')
        # Because +assignments is meant to provide an overview, we default to
        # 500 as the default batch size.
        self.assertThat(
            view.specs_batched,
            IsConfiguredBatchNavigator(
                'specification', 'specifications', batch_size=500))


class TestAssignments(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_assignments_are_batched(self):
        product = self.factory.makeProduct()
        self.factory.makeSpecification(product=product)
        self.factory.makeSpecification(product=product)
        view = create_initialized_view(product, name='+assignments',
            query_string="batch=1")
        content = view.render()
        self.assertEqual('next',
            find_tag_by_id(content, 'upper-batch-nav-batchnav-next')['class'])
        self.assertEqual('next',
            find_tag_by_id(content, 'lower-batch-nav-batchnav-next')['class'])


class TestHasSpecificationsTemplates(TestCaseWithFactory):
    """Tests the selection of templates based on blueprints usage."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestHasSpecificationsTemplates, self).setUp()
        self.user = self.factory.makePerson()
        login_person(self.user)

    def _test_templates_for_configuration(self, target, context=None):
        if context is None:
            context = target
        naked_target = removeSecurityProxy(target)
        test_configurations = [
            ServiceUsage.UNKNOWN,
            ServiceUsage.EXTERNAL,
            ServiceUsage.NOT_APPLICABLE,
            ServiceUsage.LAUNCHPAD,
            ]
        correct_templates = [
            HasSpecificationsView.not_launchpad_template.filename,
            HasSpecificationsView.not_launchpad_template.filename,
            HasSpecificationsView.not_launchpad_template.filename,
            HasSpecificationsView.default_template.filename,
            ]
        used_templates = list()
        for config in test_configurations:
            naked_target.blueprints_usage = config
            view = create_view(
                context,
                '+specs',
                layer=BlueprintsLayer,
                principal=self.user)
            used_templates.append(view.template.filename)
        self.assertEqual(correct_templates, used_templates)

    def test_product(self):
        product = self.factory.makeProduct()
        self._test_templates_for_configuration(product)

    def test_product_series(self):
        product = self.factory.makeProduct()
        product_series = self.factory.makeProductSeries(product=product)
        self._test_templates_for_configuration(
            target=product,
            context=product_series)

    def test_distribution(self):
        distribution = self.factory.makeDistribution()
        self._test_templates_for_configuration(distribution)

    def test_distroseries(self):
        distribution = self.factory.makeDistribution()
        distro_series = self.factory.makeDistroSeries(
            distribution=distribution)
        self._test_templates_for_configuration(
            target=distribution,
            context=distro_series)

    def test_projectgroup(self):
        project = self.factory.makeProject()
        product1 = self.factory.makeProduct(project=project)
        self.factory.makeProduct(project=project)
        self._test_templates_for_configuration(
            target=product1,
            context=project)


class TestHasSpecificationsConfiguration(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def test_cannot_configure_blueprints_product_no_edit_permission(self):
        product = self.factory.makeProduct()
        view = create_initialized_view(product, '+specs')
        self.assertEqual(False, view.can_configure_blueprints)

    def test_can_configure_blueprints_product_with_edit_permission(self):
        product = self.factory.makeProduct()
        login_person(product.owner)
        view = create_initialized_view(product, '+specs')
        self.assertEqual(True, view.can_configure_blueprints)

    def test_cant_configure_blueprints_distribution_no_edit_permission(self):
        distribution = self.factory.makeDistribution()
        view = create_initialized_view(distribution, '+specs')
        self.assertEqual(False, view.can_configure_blueprints)

    def test_can_configure_blueprints_distribution_with_edit_permission(self):
        distribution = self.factory.makeDistribution()
        login_person(distribution.owner)
        view = create_initialized_view(distribution, '+specs')
        self.assertEqual(True, view.can_configure_blueprints)

    def test_cannot_configure_blueprints_projectgroup(self):
        project_group = self.factory.makeProject()
        login_person(project_group.owner)
        view = create_initialized_view(project_group, '+specs')
        self.assertEqual(False, view.can_configure_blueprints)


class TestSpecificationsRobots(TestCaseWithFactory):
    """Test the behaviour of specfications when usage is UNKNOWN."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        super(TestSpecificationsRobots, self).setUp()
        self.product = self.factory.makeProduct()
        self.naked_product = removeSecurityProxy(self.product)

    def _configure_project(self, usage):
        self.naked_product.blueprints_usage = usage
        view = create_initialized_view(self.product, '+specs')
        soup = BeautifulSoup(view())
        robots = soup.find('meta', attrs={'name': 'robots'})
        return soup, robots

    def _verify_robots_not_blocked(self, usage):
        soup, robots = self._configure_project(usage)
        self.assertTrue(robots is None)
        self.assertTrue(soup.find(True, id='specs-unknown') is None)

    def _verify_robots_are_blocked(self, usage):
        soup, robots = self._configure_project(usage)
        self.assertEqual('noindex,nofollow', robots['content'])
        self.assertTrue(soup.find(True, id='specs-unknown') is not None)

    def test_UNKNOWN_blocks_robots(self):
        self._verify_robots_are_blocked(ServiceUsage.UNKNOWN)

    def test_EXTERNAL_blocks_robots(self):
        self._verify_robots_are_blocked(ServiceUsage.EXTERNAL)

    def test_NOT_APPLICABLE_blocks_robots(self):
        self._verify_robots_are_blocked(ServiceUsage.NOT_APPLICABLE)

    def test_LAUNCHPAD_does_not_block_robots(self):
        self._verify_robots_not_blocked(ServiceUsage.LAUNCHPAD)


class SpecificationSetViewTestCase(TestCaseWithFactory):
    """Test the specification application root view."""

    layer = DatabaseFunctionalLayer

    def test_search_specifications_form_rendering(self):
        # The view's template directly renders the form widgets.
        specification_set = getUtility(ISpecificationSet)
        view = create_initialized_view(specification_set, '+index')
        content = find_tag_by_id(view.render(), 'search-all-specifications')
        self.assertEqual('form', content.name)
        self.assertTrue(
            content.find(True, id='text') is not None)
        self.assertTrue(
            content.find(True, id='field.actions.search') is not None)
        self.assertTrue(
            content.find(True, id='field.scope.option.all') is not None)
        self.assertTrue(
            content.find(True, id='field.scope.option.project') is not None)
        target_widget = view.widgets['scope'].target_widget
        self.assertTrue(
            content.find(True, id=target_widget.show_widget_id) is not None)
        text = str(content)
        picker_script = (
            "Y.lp.app.picker.create('DistributionOrProductOrProjectGroup'")
        self.assertTrue(picker_script in text)
        focus_script = "setFocusByName('field.search_text')"
        self.assertTrue(focus_script in text)
