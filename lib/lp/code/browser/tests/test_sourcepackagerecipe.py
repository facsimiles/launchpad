# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Tests for the product view classes and templates."""

__metaclass__ = type


from datetime import datetime
from textwrap import dedent
import re

from pytz import utc
from canonical.testing import DatabaseFunctionalLayer
from zope.security.proxy import removeSecurityProxy

from canonical.launchpad.webapp import canonical_url
from canonical.launchpad.testing.pages import extract_text, find_main_content
from lp.buildmaster.interfaces.buildbase import BuildStatus
from lp.testing import (TestCaseWithFactory)

class TestSourcePackageRecipe(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def makeRecipe(self):
        chef = self.factory.makePersonNoCommit(displayname='Master Chef',
                name='chef')
        chocolate = self.factory.makeProduct(name='chocolate')
        cake_branch = self.factory.makeProductBranch(owner=chef, name='cake',
            product=chocolate)
        distroseries = self.factory.makeDistroSeries(
            displayname='Secret Squirrel')
        return self.factory.makeSourcePackageRecipe(
            None, chef, distroseries, None, u'Cake Recipe', cake_branch)

    def getMainText(self, recipe):
        browser = self.getUserBrowser(canonical_url(recipe))
        return extract_text(find_main_content(browser.contents))

    def test_index(self):
        recipe = self.makeRecipe()
        build = removeSecurityProxy(self.factory.makeSourcePackageRecipeBuild(
            recipe=recipe))
        build.buildstate = BuildStatus.FULLYBUILT
        build.datebuilt = datetime(2010, 03, 16, tzinfo=utc)
        pattern = re.compile(dedent("""\
            Master Chef
            Branches
            Description
            This recipe .*changes.
            Recipe Information
            Owner:
            Master Chef
            Base branch:
            lp://dev/~chef/chocolate/cake
            Debian version:
            1.0
            Distros:
            Secret Squirrel
            Build records
            Successful build.on 2010-03-16
            Recipe contents
            # bzr-builder format 0.2 deb-version 1.0
            lp://dev/~chef/chocolate/cake"""), re.S)
        main_text = self.getMainText(recipe)
        self.assertTrue(pattern.search(main_text), main_text)

    def test_index_no_suitable_builders(self):
        recipe = self.makeRecipe()
        build = removeSecurityProxy(self.factory.makeSourcePackageRecipeBuild(
            recipe=recipe))
        pattern = re.compile(dedent("""\
            Build records
            No suitable builders
            Recipe contents"""), re.S)
        main_text = self.getMainText(recipe)
        self.assertTrue(pattern.search(main_text), main_text)

    def test_index_pending(self):
        recipe = self.makeRecipe()
        build = self.factory.makeSourcePackageRecipeBuild(recipe=recipe)
        buildjob = self.factory.makeSourcePackageRecipeBuildJob(
            recipe_build=build)
        builder = self.factory.makeBuilder()
        pattern = re.compile(dedent("""\
            Build records
            Pending build.in .*\(estimated\)
            Recipe contents"""), re.S)
        main_text = self.getMainText(recipe)
        self.assertTrue(pattern.search(main_text), main_text)
