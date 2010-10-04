# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

from __future__ import with_statement

__metaclass__ = type

from BeautifulSoup import BeautifulSoup
from storm.zope.interfaces import IResultSet
from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

import unittest

from canonical.config import config
from canonical.launchpad.interfaces.launchpad import ILaunchpadCelebrities
from canonical.launchpad.webapp.batching import BatchNavigator
from canonical.launchpad.webapp.publisher import canonical_url
from canonical.testing import (
    LaunchpadZopelessLayer,
    LaunchpadFunctionalLayer,
    )
from lp.registry.enum import (
    DistroSeriesDifferenceStatus,
    DistroSeriesDifferenceType,
    )
from lp.services.features.flags import FeatureController
from lp.services.features.model import (
    FeatureFlag,
    getFeatureStore,
    )
from lp.services.features import (
    getFeatureFlag,
    per_thread,
    )
from lp.testing import (
    TestCaseWithFactory,
    person_logged_in
    )
from lp.testing.views import create_initialized_view


class TestDistroSeriesNeedsPackagesView(TestCaseWithFactory):
    """Test the distroseries +needs-packaging view."""

    layer = LaunchpadZopelessLayer

    def test_cached_unlinked_packages(self):
        ubuntu = getUtility(ILaunchpadCelebrities).ubuntu
        distroseries = self.factory.makeDistroSeries(distribution=ubuntu)
        view = create_initialized_view(distroseries, '+needs-packaging')
        naked_packages = removeSecurityProxy(view.cached_unlinked_packages)
        self.assertTrue(
            IResultSet.providedBy(
                view.cached_unlinked_packages.currentBatch().list),
            '%s should batch IResultSet so that slicing will limit the '
            'query' % view.cached_unlinked_packages.currentBatch().list)


class TestDistroSeriesView(TestCaseWithFactory):
    """Test the distroseries +index view."""

    layer = LaunchpadZopelessLayer

    def test_needs_linking(self):
        ubuntu = getUtility(ILaunchpadCelebrities).ubuntu
        distroseries = self.factory.makeDistroSeries(distribution=ubuntu)
        view = create_initialized_view(distroseries, '+index')
        self.assertEqual(view.needs_linking, None)


class DistroSeriesLocalPackageDiffsTestCase(TestCaseWithFactory):
    """Test the distroseries +localpackagediffs view."""

    layer = LaunchpadFunctionalLayer

    def makeDerivedSeries(self, derived_name=None, parent_name=None):
        # Helper that creates a derived distro series.
        parent = self.factory.makeDistroSeries(name=parent_name)
        derived_series = self.factory.makeDistroSeries(
            name=derived_name, parent_series=parent)
        return derived_series

    def setDerivedSeriesUIFeatureFlag(self):
        # Helper to set the feature flag enabling the derived series ui.
        ignore = getFeatureStore().add(FeatureFlag(
            scope=u'default', flag=u'soyuz.derived-series-ui.enabled',
            value=u'on', priority=1))

        # XXX Michael Nelson 2010-09-21 bug=631884
        # Currently LaunchpadTestRequest doesn't set per-thread
        # features.
        def in_scope(value):
            return True
        per_thread.features = FeatureController(in_scope)

        def reset_per_thread_features():
            per_thread.features = None
        self.addCleanup(reset_per_thread_features)

    def test_view_redirects_without_feature_flag(self):
        # If the feature flag soyuz.derived-series-ui.enabled is not set the
        # view simply redirects to the derived series.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')

        self.assertIs(
            None, getFeatureFlag('soyuz.derived-series-ui.enabled'))
        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        response = view.request.response
        self.assertEqual(302, response.getStatus())
        self.assertEqual(
            canonical_url(derived_series), response.getHeader('location'))

    def test_label(self):
        # The view label includes the names of both series.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')

        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        self.assertEqual(
            "Source package differences between 'Derilucid' and "
            "parent series 'Lucid'",
            view.label)

    def test_batch_includes_needing_attention_only(self):
        # The differences attribute includes differences needing
        # attention only.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        current_difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)
        old_difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series,
            status=DistroSeriesDifferenceStatus.RESOLVED)

        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        self.assertContentEqual(
            [current_difference], view.cached_differences.batch)

    def test_batch_includes_different_versions_only(self):
        # The view contains differences of type DIFFERENT_VERSIONS only.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        different_versions_diff = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)
        unique_diff = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series,
            difference_type=(
                DistroSeriesDifferenceType.UNIQUE_TO_DERIVED_SERIES))

        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        self.assertContentEqual(
            [different_versions_diff], view.cached_differences.batch)

    def test_template_includes_help_link(self):
        # The help link for popup help is included.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')

        self.setDerivedSeriesUIFeatureFlag()
        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        soup = BeautifulSoup(view())
        help_links = soup.findAll(
            'a', href='/+help/soyuz/derived-series-syncing.html')
        self.assertEqual(1, len(help_links))

    def test_diff_row_includes_last_comment_only(self):
        # The most recent comment is rendered for each difference.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)
        difference.addComment(difference.owner, "Earlier comment")
        difference.addComment(difference.owner, "Latest comment")

        self.setDerivedSeriesUIFeatureFlag()
        view = create_initialized_view(
            derived_series, '+localpackagediffs')

        # Find all the rows within the body of the table
        # listing the differences.
        soup = BeautifulSoup(view())
        diff_table = soup.find('table', {'class': 'listing'})
        rows = diff_table.tbody.findAll('tr')

        self.assertEqual(1, len(rows))
        self.assertIn("Latest comment", unicode(rows[0]))
        self.assertNotIn("Earlier comment", unicode(rows[0]))

    def test_diff_row_links_to_extra_details(self):
        # The source package name links to the difference details.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        view = create_initialized_view(
            derived_series, '+localpackagediffs')
        soup = BeautifulSoup(view())
        diff_table = soup.find('table', {'class': 'listing'})
        row = diff_table.tbody.findAll('tr')[0]

        href = canonical_url(difference).replace('http://launchpad.dev', '')
        links = row.findAll('a', href=href)
        self.assertEqual(1, len(links))
        self.assertEqual(difference.source_package_name.name, links[0].string)

    def test_sync_option_for_non_editor(self):
        # Non-editors cannot perform syncs.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        #with person_logged_in(self.factory.makePerson()):
        view = create_initialized_view(
            derived_series, '+localpackagediffs')
        soup = BeautifulSoup(view())

        checkbox = soup.find(
            'input', id='field.selected_differences.%d' % difference.id)
        self.assertIs(None, checkbox)
        button = soup.find('input', id='field.actions.sync')
        self.assertIs(None, button)

    def test_sync_option_for_editor(self):
        # Editors can perform syncs.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        #with person_logged_in(derived_series.owner):
        view = create_initialized_view(
            derived_series, '+localpackagediffs')
        soup = BeautifulSoup(view())

        checkbox = soup.find(
            'input', id='field.selected_differences.%d' % difference.id)
        self.assertIsNot(None, checkbox)
        button = soup.find('input', id='field.actions.sync')
        self.assertEqual(
            "Sync selected Lucid versions into Derilucid",
            button['value'])

    def test_selected_differences_field_for_non_editor(self):
        # Non-editors do not get a selected_differences field
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        with person_logged_in(self.factory.makePerson()):
            view = create_initialized_view(
                derived_series, '+localpackagediffs')

        self.assertIs(None, view.widgets.get('selected_differences'))

    def test_selected_differences_field_for_editor(self):
        # Editors see a selected diffs field with the correct
        # vocabulary.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            source_package_name_str='my-src-name',
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        with person_logged_in(derived_series.owner):
            view = create_initialized_view(
                derived_series, '+localpackagediffs')

        widget = view.widgets['selected_differences']
        self.assertEqual(
            ['my-src-name'],
            widget.vocabulary.by_token.keys())

    def test_notification_after_sync(self):
        # Syncing one or more diffs results in a stub notification.
        derived_series = self.makeDerivedSeries(
            parent_name='lucid', derived_name='derilucid')
        difference = self.factory.makeDistroSeriesDifference(
            source_package_name_str='my-src-name',
            derived_series=derived_series)

        self.setDerivedSeriesUIFeatureFlag()
        with person_logged_in(derived_series.owner):
            view = create_initialized_view(
                derived_series, '+localpackagediffs',
                method='POST', form={
                    'field.selected_differences': [
                        difference.source_package_name.name,
                        ],
                    'field.actions.sync': 'Sync',
                    })

        self.assertEqual(0, len(view.errors))


class TestMilestoneBatchNavigatorAttribute(TestCaseWithFactory):
    """Test the series.milestone_batch_navigator attribute."""

    layer = LaunchpadZopelessLayer

    def test_distroseries_milestone_batch_navigator(self):
        ubuntu = getUtility(ILaunchpadCelebrities).ubuntu
        distroseries = self.factory.makeDistroSeries(distribution=ubuntu)
        for name in ('a', 'b', 'c', 'd'):
            distroseries.newMilestone(name)
        view = create_initialized_view(distroseries, name='+index')
        self._check_milestone_batch_navigator(view)

    def test_productseries_milestone_batch_navigator(self):
        product = self.factory.makeProduct()
        for name in ('a', 'b', 'c', 'd'):
            product.development_focus.newMilestone(name)

        view = create_initialized_view(
            product.development_focus, name='+index')
        self._check_milestone_batch_navigator(view)

    def _check_milestone_batch_navigator(self, view):
        config.push('default-batch-size', """
        [launchpad]
        default_batch_size: 2
        """)
        self.assert_(
            isinstance(view.milestone_batch_navigator, BatchNavigator),
            'milestone_batch_navigator is not a BatchNavigator object: %r'
            % view.milestone_batch_navigator)
        self.assertEqual(4, view.milestone_batch_navigator.batch.total())
        expected = [
            'd',
            'c',
            ]
        milestone_names = [
            item.name
            for item in view.milestone_batch_navigator.currentBatch()]
        self.assertEqual(expected, milestone_names)
        config.pop('default-batch-size')


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
