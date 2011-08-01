# Copyright 2011 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type


from zope.security.proxy import removeSecurityProxy

from canonical.testing.layers import ZopelessDatabaseLayer
from lp.testing import TestCaseWithFactory
from lp.translations.interfaces.side import (
    TranslationSide,
    )
from lp.translations.utilities.translationsplitter import (
    TranslationSplitter,
    TranslationTemplateSplitter,
    )


def use_in_template(factory, potmsgset, potemplate):
    return potmsgset.setSequence(
        potemplate, factory.getUniqueInteger())


def make_translation_splitter(factory):
    return TranslationSplitter(
        factory.makeProductSeries(), factory.makeSourcePackage())


def make_shared_potmsgset(factory, splitter=None):
    if splitter is None:
        splitter = make_translation_splitter(factory)
    upstream_template = factory.makePOTemplate(
        productseries=splitter.productseries)
    potmsgset = factory.makePOTMsgSet(
        upstream_template, sequence=factory.getUniqueInteger())
    (upstream_item,) = potmsgset.getAllTranslationTemplateItems()
    ubuntu_template = factory.makePOTemplate(
        sourcepackage=splitter.sourcepackage)
    ubuntu_item = use_in_template(factory, potmsgset, ubuntu_template)
    return upstream_item, ubuntu_item


class TestTranslationSplitter(TestCaseWithFactory):

    layer = ZopelessDatabaseLayer

    def test_findShared_requires_both(self):
        """Results are only included when both sides have the POTMsgSet."""
        upstream_template = self.factory.makePOTemplate(
            side=TranslationSide.UPSTREAM)
        productseries = upstream_template.productseries
        ubuntu_template = self.factory.makePOTemplate(
            side=TranslationSide.UBUNTU)
        package = ubuntu_template.sourcepackage
        potmsgset = self.factory.makePOTMsgSet(upstream_template, sequence=1)
        splitter = TranslationSplitter(productseries, package)
        self.assertContentEqual([], splitter.findShared())
        (upstream_item,) = potmsgset.getAllTranslationTemplateItems()
        ubuntu_item = use_in_template(
            self.factory, potmsgset, ubuntu_template)
        self.assertContentEqual(
            [(upstream_item, ubuntu_item)], splitter.findShared())
        removeSecurityProxy(upstream_item).destroySelf()
        self.assertContentEqual([], splitter.findShared())

    def test_findSharedGroupsPOTMsgSet(self):
        """POTMsgSets are correctly grouped."""
        splitter = make_translation_splitter(self.factory)
        make_shared_potmsgset(self.factory, splitter)
        make_shared_potmsgset(self.factory, splitter)
        for num, (upstream, ubuntu) in enumerate(splitter.findShared()):
            self.assertEqual(upstream.potmsgset, ubuntu.potmsgset)
        self.assertEqual(1, num)

    def test_splitPOTMsgSet(self):
        """Splitting a POTMsgSet clones it and updates TemplateItem."""
        splitter = make_translation_splitter(self.factory)
        upstream_item, ubuntu_item = make_shared_potmsgset(
            self.factory, splitter)
        ubuntu_template = ubuntu_item.potemplate
        ubuntu_sequence = ubuntu_item.sequence
        new_potmsgset = splitter.splitPOTMsgSet(ubuntu_item)
        self.assertEqual(new_potmsgset, ubuntu_item.potmsgset)

    def test_migrateTranslations_diverged_upstream(self):
        """Diverged upstream translation stays put."""
        splitter = make_translation_splitter(self.factory)
        upstream_item, ubuntu_item = make_shared_potmsgset(
            self.factory, splitter)
        upstream_message = self.factory.makeCurrentTranslationMessage(
            potmsgset=upstream_item.potmsgset,
            potemplate=upstream_item.potemplate, diverged=True)
        splitter.splitPOTMsgSet(ubuntu_item)
        upstream_translation = splitter.migrateTranslations(
            upstream_item.potmsgset, ubuntu_item)
        self.assertEqual(
            upstream_message,
            upstream_item.potmsgset.getAllTranslationMessages().one())
        self.assertIs(
            None, ubuntu_item.potmsgset.getAllTranslationMessages().one())

    def test_migrateTranslations_diverged_ubuntu(self):
        """Diverged ubuntu translation moves."""
        splitter = make_translation_splitter(self.factory)
        upstream_item, ubuntu_item = make_shared_potmsgset(
            self.factory, splitter)
        ubuntu_message = self.factory.makeCurrentTranslationMessage(
            potmsgset=ubuntu_item.potmsgset,
            potemplate=ubuntu_item.potemplate, diverged=True)
        splitter.splitPOTMsgSet(ubuntu_item)
        upstream_translation = splitter.migrateTranslations(
            upstream_item.potmsgset, ubuntu_item)
        self.assertEqual(
            ubuntu_message,
            ubuntu_item.potmsgset.getAllTranslationMessages().one())
        self.assertIs(
            None,
            upstream_item.potmsgset.getAllTranslationMessages().one())

    def test_migrateTranslations_shared(self):
        """Shared translation is copied."""
        splitter = make_translation_splitter(self.factory)
        upstream_item, ubuntu_item = make_shared_potmsgset(
            self.factory, splitter)
        self.factory.makeCurrentTranslationMessage(
            potmsgset=upstream_item.potmsgset)
        splitter.splitPOTMsgSet(ubuntu_item)
        splitter.migrateTranslations(upstream_item.potmsgset, ubuntu_item)
        (upstream_translation,) = (
            upstream_item.potmsgset.getAllTranslationMessages())
        (ubuntu_translation,) = (
            ubuntu_item.potmsgset.getAllTranslationMessages())
        self.assertEqual(
            ubuntu_translation.translations,
            upstream_translation.translations)

    def test_split_translations(self):
        """Split translations splits POTMsgSet and TranslationMessage."""
        splitter = make_translation_splitter(self.factory)
        upstream_item, ubuntu_item = make_shared_potmsgset(
            self.factory, splitter)
        upstream_message = self.factory.makeCurrentTranslationMessage(
            potmsgset=upstream_item.potmsgset,
            potemplate=upstream_item.potemplate)
        splitter.split()
        self.assertNotEqual(
            list(upstream_item.potemplate), list(ubuntu_item.potemplate))
        self.assertNotEqual(
            list(upstream_item.potmsgset.getAllTranslationMessages()),
            list(ubuntu_item.potmsgset.getAllTranslationMessages()),
            )
        self.assertEqual(
            upstream_item.potmsgset.getAllTranslationMessages().count(),
            ubuntu_item.potmsgset.getAllTranslationMessages().count(),
        )


class TestTranslationTemplateSplitterBase:

    layer = ZopelessDatabaseLayer

    def getPOTMsgSetAndTemplateToSplit(self, splitter):
        return [(tti1.potmsgset, tti1.potemplate)
                for tti1, tti2 in splitter.findShared()]

    def makePOTemplate(self):
        raise NotImplementedError('Subclasses should implement this.')

    def makeSharingTemplate(self, template):
        raise NotImplementedError('Subclasses should implement this.')

    def test_findShared_renamed(self):
        """Shared POTMsgSets are included for a renamed template."""
        template1 = self.makePOTemplate()
        template2 = self.makeSharingTemplate(template1)

        shared_potmsgset = self.factory.makePOTMsgSet(template1, sequence=1)
        shared_potmsgset.setSequence(template2, 1)

        # POTMsgSets appearing in only one of the templates are not returned.
        unshared_message1 = self.factory.makePOTMsgSet(template1, sequence=2)
        unshared_message2 = self.factory.makePOTMsgSet(template2, sequence=2)

        splitter = TranslationTemplateSplitter(template2)
        self.assertContentEqual([], splitter.findShared())

        template2.name = 'renamed'
        self.assertContentEqual(
            [(shared_potmsgset, template1)],
            self.getPOTMsgSetAndTemplateToSplit(splitter))

    def test_findShared_moved_product(self):
        """Shared POTMsgSets are included for a template moved elsewhere."""
        template1 = self.makePOTemplate()
        template2 = self.makeSharingTemplate(template1)

        shared_potmsgset = self.factory.makePOTMsgSet(template1, sequence=1)
        shared_potmsgset.setSequence(template2, 1)

        # POTMsgSets appearing in only one of the templates are not returned.
        unshared_message1 = self.factory.makePOTMsgSet(template1, sequence=2)
        unshared_message2 = self.factory.makePOTMsgSet(template2, sequence=2)

        splitter = TranslationTemplateSplitter(template2)
        self.assertContentEqual([], splitter.findShared())

        # Move the template to a different product entirely.
        template2.productseries = self.factory.makeProduct().development_focus
        template2.distroseries = None
        template2.sourcepackagename = None
        self.assertContentEqual(
            [(shared_potmsgset, template1)],
            self.getPOTMsgSetAndTemplateToSplit(splitter))

    def test_findShared_moved_distribution(self):
        """Shared POTMsgSets are included for a template moved elsewhere."""
        template1 = self.makePOTemplate()
        template2 = self.makeSharingTemplate(template1)

        shared_potmsgset = self.factory.makePOTMsgSet(template1, sequence=1)
        shared_potmsgset.setSequence(template2, 1)

        # POTMsgSets appearing in only one of the templates are not returned.
        unshared_message1 = self.factory.makePOTMsgSet(template1, sequence=2)
        unshared_message2 = self.factory.makePOTMsgSet(template2, sequence=2)

        splitter = TranslationTemplateSplitter(template2)
        self.assertContentEqual([], splitter.findShared())

        # Move the template to a different distribution entirely.
        sourcepackage = self.factory.makeSourcePackage()
        template2.distroseries = sourcepackage.distroseries
        template2.sourcepackagename = sourcepackage.sourcepackagename
        template2.productseries = None
        self.assertContentEqual(
            [(shared_potmsgset, template1)],
            self.getPOTMsgSetAndTemplateToSplit(splitter))


class TestProductTranslationTemplateSplitter(
    TestCaseWithFactory, TestTranslationTemplateSplitterBase):

    def makePOTemplate(self):
        return self.factory.makePOTemplate(
            name='template',
            side=TranslationSide.UPSTREAM)

    def makeSharingTemplate(self, template):
        product = template.productseries.product
        other_series = self.factory.makeProductSeries(product=product)
        return self.factory.makePOTemplate(name='template',
                                           productseries=other_series)


class TestDistributionTranslationTemplateSplitter(
    TestCaseWithFactory, TestTranslationTemplateSplitterBase):

    def makePOTemplate(self):
        return self.factory.makePOTemplate(
            name='template',
            side=TranslationSide.UBUNTU)

    def makeSharingTemplate(self, template):
        distro = template.distroseries.distribution
        other_series = self.factory.makeDistroRelease(distribution=distro)
        return self.factory.makePOTemplate(
            name='template',
            distroseries=other_series,
            sourcepackagename=template.sourcepackagename)

    def test_findShared_moved_sourcepackage(self):
        """Shared POTMsgSets are included for a template moved to
        a different source package inside the same distroseries."""
        template1 = self.makePOTemplate()
        template2 = self.makeSharingTemplate(template1)

        shared_potmsgset = self.factory.makePOTMsgSet(template1, sequence=1)
        shared_potmsgset.setSequence(template2, 1)

        # POTMsgSets appearing in only one of the templates are not returned.
        unshared_message1 = self.factory.makePOTMsgSet(template1, sequence=2)
        unshared_message2 = self.factory.makePOTMsgSet(template2, sequence=2)

        splitter = TranslationTemplateSplitter(template2)
        self.assertContentEqual([], splitter.findShared())

        # Move the template to a different source package inside the
        # same distroseries.
        sourcepackage = self.factory.makeSourcePackage(
            distroseries=template2.distroseries)
        template2.sourcepackagename = sourcepackage.sourcepackagename
        self.assertContentEqual(
            [(shared_potmsgset, template1)],
            self.getPOTMsgSetAndTemplateToSplit(splitter))
