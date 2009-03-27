# Copyright 2009 Canonical Ltd.  All rights reserved.

"""Tests for the IBranchLookup implementation."""

__metaclass__ = type

import unittest

from lazr.uri import URI

from zope.component import getUtility
from zope.security.proxy import removeSecurityProxy

from canonical.config import config
from canonical.launchpad.ftests import ANONYMOUS, login, login_person
from canonical.launchpad.interfaces.branch import NoSuchBranch
from canonical.launchpad.interfaces.branchlookup import (
    CannotHaveLinkedBranch, IBranchLookup, ILinkedBranchTraverser,
    ISourcePackagePocketFactory, NoLinkedBranch)
from canonical.launchpad.interfaces.branchnamespace import (
    get_branch_namespace, InvalidNamespace)
from canonical.launchpad.interfaces.distroseries import NoSuchDistroSeries
from canonical.launchpad.interfaces.launchpad import ILaunchpadCelebrities
from canonical.launchpad.interfaces.person import NoSuchPerson
from canonical.launchpad.interfaces.product import (
    InvalidProductName, NoSuchProduct)
from canonical.launchpad.interfaces.productseries import NoSuchProductSeries
from canonical.launchpad.interfaces.publishing import PackagePublishingPocket
from canonical.launchpad.interfaces.sourcepackagename import (
    NoSuchSourcePackageName)
from canonical.launchpad.testing import TestCaseWithFactory
from canonical.testing.layers import DatabaseFunctionalLayer


class TestGetByUniqueName(TestCaseWithFactory):
    """Tests for `IBranchLookup.getByUniqueName`."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.branch_set = getUtility(IBranchLookup)

    def test_not_found(self):
        unused_name = self.factory.getUniqueString()
        found = self.branch_set.getByUniqueName(unused_name)
        self.assertIs(None, found)

    def test_junk(self):
        branch = self.factory.makePersonalBranch()
        found_branch = self.branch_set.getByUniqueName(branch.unique_name)
        self.assertEqual(branch, found_branch)

    def test_product(self):
        branch = self.factory.makeProductBranch()
        found_branch = self.branch_set.getByUniqueName(branch.unique_name)
        self.assertEqual(branch, found_branch)

    def test_source_package(self):
        branch = self.factory.makePackageBranch()
        found_branch = self.branch_set.getByUniqueName(branch.unique_name)
        self.assertEqual(branch, found_branch)


class TestGetByPath(TestCaseWithFactory):
    """Test `IBranchLookup.getByLPPath`."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.branch_lookup = getUtility(IBranchLookup)

    def getByPath(self, path):
        return self.branch_lookup.getByLPPath(path)

    def makeRelativePath(self):
        arbitrary_num_segments = 7
        return '/'.join([
            self.factory.getUniqueString()
            for i in range(arbitrary_num_segments)])

    def test_finds_exact_personal_branch(self):
        branch = self.factory.makePersonalBranch()
        found_branch, suffix = self.getByPath(branch.unique_name)
        self.assertEqual(branch, found_branch)
        self.assertEqual(None, suffix)

    def test_finds_suffixed_personal_branch(self):
        branch = self.factory.makePersonalBranch()
        suffix = self.makeRelativePath()
        found_branch, found_suffix = self.getByPath(
            branch.unique_name + '/' + suffix)
        self.assertEqual(branch, found_branch)
        self.assertEqual(suffix, found_suffix)

    def test_missing_personal_branch(self):
        owner = self.factory.makePerson()
        namespace = get_branch_namespace(owner)
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        self.assertRaises(NoSuchBranch, self.getByPath, branch_name)

    def test_missing_suffixed_personal_branch(self):
        owner = self.factory.makePerson()
        namespace = get_branch_namespace(owner)
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        suffix = self.makeRelativePath()
        self.assertRaises(
            NoSuchBranch, self.getByPath, branch_name + '/' + suffix)

    def test_finds_exact_product_branch(self):
        branch = self.factory.makeProductBranch()
        found_branch, suffix = self.getByPath(branch.unique_name)
        self.assertEqual(branch, found_branch)
        self.assertEqual(None, suffix)

    def test_finds_suffixed_product_branch(self):
        branch = self.factory.makeProductBranch()
        suffix = self.makeRelativePath()
        found_branch, found_suffix = self.getByPath(
            branch.unique_name + '/' + suffix)
        self.assertEqual(branch, found_branch)
        self.assertEqual(suffix, found_suffix)

    def test_missing_product_branch(self):
        owner = self.factory.makePerson()
        product = self.factory.makeProduct()
        namespace = get_branch_namespace(owner, product=product)
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        self.assertRaises(NoSuchBranch, self.getByPath, branch_name)

    def test_missing_suffixed_product_branch(self):
        owner = self.factory.makePerson()
        product = self.factory.makeProduct()
        namespace = get_branch_namespace(owner, product=product)
        suffix = self.makeRelativePath()
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        self.assertRaises(
            NoSuchBranch, self.getByPath, branch_name + '/' + suffix)

    def test_finds_exact_package_branch(self):
        branch = self.factory.makePackageBranch()
        found_branch, suffix = self.getByPath(branch.unique_name)
        self.assertEqual(branch, found_branch)
        self.assertEqual(None, suffix)

    def test_missing_package_branch(self):
        owner = self.factory.makePerson()
        distroseries = self.factory.makeDistroRelease()
        sourcepackagename = self.factory.makeSourcePackageName()
        namespace = get_branch_namespace(
            owner, distroseries=distroseries,
            sourcepackagename=sourcepackagename)
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        self.assertRaises(NoSuchBranch, self.getByPath, branch_name)

    def test_missing_suffixed_package_branch(self):
        owner = self.factory.makePerson()
        distroseries = self.factory.makeDistroRelease()
        sourcepackagename = self.factory.makeSourcePackageName()
        namespace = get_branch_namespace(
            owner, distroseries=distroseries,
            sourcepackagename=sourcepackagename)
        suffix = self.makeRelativePath()
        branch_name = namespace.getBranchName(self.factory.getUniqueString())
        self.assertRaises(
            NoSuchBranch, self.getByPath, branch_name + '/' + suffix)

    def test_too_short(self):
        person = self.factory.makePerson()
        self.assertRaises(
            InvalidNamespace, self.getByPath, '~%s' % person.name)

    def test_no_such_product(self):
        person = self.factory.makePerson()
        branch_name = '~%s/%s/%s' % (
            person.name, self.factory.getUniqueString(), 'branch-name')
        self.assertRaises(NoSuchProduct, self.getByPath, branch_name)


class TestGetByUrl(TestCaseWithFactory):

    layer = DatabaseFunctionalLayer

    def makeProductBranch(self):
        """Create a branch with aa/b/c as its unique name."""
        # XXX: JonathanLange 2009-01-13 spec=package-branches: This test is
        # bad because it assumes that the interesting branches for testing are
        # product branches.
        owner = self.factory.makePerson(name='aa')
        product = self.factory.makeProduct('b')
        return self.factory.makeProductBranch(
            owner=owner, product=product, name='c')

    def test_getByUrl_with_http(self):
        """getByUrl recognizes LP branches for http URLs."""
        branch = self.makeProductBranch()
        branch_set = getUtility(IBranchLookup)
        branch2 = branch_set.getByUrl('http://bazaar.launchpad.dev/~aa/b/c')
        self.assertEqual(branch, branch2)

    def test_getByUrl_with_ssh(self):
        """getByUrl recognizes LP branches for bzr+ssh URLs."""
        branch = self.makeProductBranch()
        branch_set = getUtility(IBranchLookup)
        branch2 = branch_set.getByUrl(
            'bzr+ssh://bazaar.launchpad.dev/~aa/b/c')
        self.assertEqual(branch, branch2)

    def test_getByUrl_with_sftp(self):
        """getByUrl recognizes LP branches for sftp URLs."""
        branch = self.makeProductBranch()
        branch_set = getUtility(IBranchLookup)
        branch2 = branch_set.getByUrl('sftp://bazaar.launchpad.dev/~aa/b/c')
        self.assertEqual(branch, branch2)

    def test_getByUrl_with_ftp(self):
        """getByUrl does not recognize LP branches for ftp URLs.

        This is because Launchpad doesn't currently support ftp.
        """
        branch = self.makeProductBranch()
        branch_set = getUtility(IBranchLookup)
        branch2 = branch_set.getByUrl('ftp://bazaar.launchpad.dev/~aa/b/c')
        self.assertIs(None, branch2)

    def test_getByURL_with_lp_prefix(self):
        """lp: URLs for the configured prefix are supported."""
        branch_set = getUtility(IBranchLookup)
        url = '%s~aa/b/c' % config.codehosting.bzr_lp_prefix
        self.assertRaises(NoSuchPerson, branch_set.getByUrl, url)
        owner = self.factory.makePerson(name='aa')
        product = self.factory.makeProduct('b')
        branch2 = branch_set.getByUrl(url)
        self.assertIs(None, branch2)
        branch = self.factory.makeProductBranch(
            owner=owner, product=product, name='c')
        branch2 = branch_set.getByUrl(url)
        self.assertEqual(branch, branch2)

    def test_getByURL_for_production(self):
        """test_getByURL works with production values."""
        branch_set = getUtility(IBranchLookup)
        branch = self.makeProductBranch()
        self.pushConfig('codehosting', lp_url_hosts='edge,production,,')
        branch2 = branch_set.getByUrl('lp://staging/~aa/b/c')
        self.assertIs(None, branch2)
        branch2 = branch_set.getByUrl('lp://asdf/~aa/b/c')
        self.assertIs(None, branch2)
        branch2 = branch_set.getByUrl('lp:~aa/b/c')
        self.assertEqual(branch, branch2)
        branch2 = branch_set.getByUrl('lp://production/~aa/b/c')
        self.assertEqual(branch, branch2)
        branch2 = branch_set.getByUrl('lp://edge/~aa/b/c')
        self.assertEqual(branch, branch2)

    def test_uriToUniqueName(self):
        """Ensure uriToUniqueName works.

        Only codehosting-based using http, sftp or bzr+ssh URLs will
        be handled. If any other URL gets passed the returned will be
        None.
        """
        branch_set = getUtility(IBranchLookup)
        uri = URI(config.codehosting.supermirror_root)
        uri.path = '/~foo/bar/baz'
        # Test valid schemes
        uri.scheme = 'http'
        self.assertEqual('~foo/bar/baz', branch_set.uriToUniqueName(uri))
        uri.scheme = 'sftp'
        self.assertEqual('~foo/bar/baz', branch_set.uriToUniqueName(uri))
        uri.scheme = 'bzr+ssh'
        self.assertEqual('~foo/bar/baz', branch_set.uriToUniqueName(uri))
        # Test invalid scheme
        uri.scheme = 'ftp'
        self.assertIs(None, branch_set.uriToUniqueName(uri))
        # Test valid scheme, invalid domain
        uri.scheme = 'sftp'
        uri.host = 'example.com'
        self.assertIs(None, branch_set.uriToUniqueName(uri))


class TestLinkedBranchTraverser(TestCaseWithFactory):
    """Tests for the linked branch traverser."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.traverser = getUtility(ILinkedBranchTraverser)

    def assertTraverses(self, path, result):
        """Assert that 'path' resolves to 'result'."""
        self.assertEqual(result, self.traverser.traverse(path))

    def test_error_fallthrough_product_series(self):
        # For the short name of a series branch, `traverse` raises
        # `NoSuchProduct` if the first component refers to a non-existent
        # product, and `NoSuchProductSeries` if the second component refers to
        # a non-existent series.
        self.assertRaises(
            NoSuchProduct, self.traverser.traverse, 'bb/dd')
        product = self.factory.makeProduct(name='bb')
        self.assertRaises(
            NoSuchProductSeries, self.traverser.traverse, 'bb/dd')

    def test_product_series(self):
        # `traverse` resolves the path to a product series to the product
        # series itself.
        series = self.factory.makeSeries()
        short_name = '%s/%s' % (series.product.name, series.name)
        self.assertTraverses(short_name, series)

    def test_product_that_doesnt_exist(self):
        # `traverse` raises `NoSuchProduct` when resolving an lp path of
        # 'product' if the product doesn't exist.
        self.assertRaises(NoSuchProduct, self.traverser.traverse, 'bb')

    def test_invalid_product(self):
        # `traverse` raises `InvalidProductIdentifier` when resolving an lp
        # path for a completely invalid product development focus branch.
        self.assertRaises(
            InvalidProductName, self.traverser.traverse, 'b')

    def test_product(self):
        # `traverse` resolves the name of a product to the product itself.
        product = self.factory.makeProduct()
        self.assertTraverses(product.name, product)

    def test_source_package(self):
        # `traverse` resolves 'distro/series/package' to the release pocket of
        # that package in that series.
        package = self.factory.makeSourcePackage()
        self.assertTraverses(
            package.path,
            getUtility(ISourcePackagePocketFactory).new(
                package, PackagePublishingPocket.RELEASE))

    def test_traverse_source_package_pocket(self):
        # `traverse` resolves 'distro/series-pocket/package' to the official
        # branch for 'pocket' on that package.
        package = self.factory.makeSourcePackage()
        pocket = PackagePublishingPocket.BACKPORTS
        sourcepackagepocket = getUtility(ISourcePackagePocketFactory).new(
            package, pocket)
        self.assertTraverses(sourcepackagepocket.path, sourcepackagepocket)

    def test_no_such_distribution(self):
        # `traverse` raises `NoSuchProduct` error if the distribution doesn't
        # exist. That's because it can't tell the difference between the name
        # of a product that doesn't exist and the name of a distribution that
        # doesn't exist.
        self.assertRaises(
            NoSuchProduct, self.traverser.traverse,
            'distro/series/package')

    def test_no_such_distro_series(self):
        # `traverse` raises `NoSuchDistroSeries` if the distro series doesn't
        # exist.
        distro = self.factory.makeDistribution(name='distro')
        self.assertRaises(
            NoSuchDistroSeries, self.traverser.traverse,
            'distro/series/package')

    def test_no_such_sourcepackagename(self):
        # `traverse` raises `NoSuchSourcePackageName` if the package in
        # distro/series/package doesn't exist.
        distroseries = self.factory.makeDistroRelease()
        path = '%s/%s/doesntexist' % (
            distroseries.distribution.name, distroseries.name)
        self.assertRaises(
            NoSuchSourcePackageName, self.traverser.traverse, path)


class TestGetByLPPath(TestCaseWithFactory):
    """Ensure URLs are correctly expanded."""

    layer = DatabaseFunctionalLayer

    def setUp(self):
        TestCaseWithFactory.setUp(self)
        self.branch_lookup = getUtility(IBranchLookup)

    def test_error_fallthrough_product_branch(self):
        # getByLPPath raises `NoSuchPerson` if the person component is not
        # found, then `NoSuchProduct` if the person component is found but the
        # product component isn't, then `NoSuchBranch` if the first two
        # components are found.
        self.assertRaises(
            NoSuchPerson, self.branch_lookup.getByLPPath, '~aa/bb/c')
        owner = self.factory.makePerson(name='aa')
        self.assertRaises(
            NoSuchProduct, self.branch_lookup.getByLPPath, '~aa/bb/c')
        product = self.factory.makeProduct(name='bb')
        self.assertRaises(
            NoSuchBranch, self.branch_lookup.getByLPPath, '~aa/bb/c')

    def test_private_branch(self):
        # If the unique name refers to an invisible branch, getByLPPath raises
        # NoSuchBranch, just as if the branch weren't there at all.
        branch = self.factory.makeAnyBranch(private=True)
        path = removeSecurityProxy(branch).unique_name
        self.assertRaises(
            NoSuchBranch, self.branch_lookup.getByLPPath, path)

    def test_resolve_product_branch_unique_name(self):
        # getByLPPath returns the branch, no trailing path and no series if
        # given the unique name of an existing product branch.
        branch = self.factory.makeProductBranch()
        self.assertEqual(
            (branch, None),
            self.branch_lookup.getByLPPath(branch.unique_name))

    def test_resolve_product_branch_unique_name_with_trailing(self):
        # getByLPPath returns the branch and the trailing path (with no
        # series) if the given path is inside an existing branch.
        branch = self.factory.makeProductBranch()
        path = '%s/foo/bar/baz' % (branch.unique_name,)
        self.assertEqual(
            (branch, 'foo/bar/baz'), self.branch_lookup.getByLPPath(path))

    def test_error_fallthrough_personal_branch(self):
        # getByLPPath raises `NoSuchPerson` if the first component doesn't
        # match an existing person, and `NoSuchBranch` if the last component
        # doesn't match an existing branch.
        self.assertRaises(
            NoSuchPerson, self.branch_lookup.getByLPPath, '~aa/+junk/c')
        owner = self.factory.makePerson(name='aa')
        self.assertRaises(
            NoSuchBranch, self.branch_lookup.getByLPPath, '~aa/+junk/c')

    def test_resolve_personal_branch_unique_name(self):
        # getByLPPath returns the branch, no trailing path and no series if
        # given the unique name of an existing junk branch.
        branch = self.factory.makePersonalBranch()
        self.assertEqual(
            (branch, None),
            self.branch_lookup.getByLPPath(branch.unique_name))

    def test_resolve_personal_branch_unique_name_with_trailing(self):
        # getByLPPath returns the branch and the trailing path (with no
        # series) if the given path is inside an existing branch.
        branch = self.factory.makePersonalBranch()
        path = '%s/foo/bar/baz' % (branch.unique_name,)
        self.assertEqual(
            (branch, 'foo/bar/baz'),
            self.branch_lookup.getByLPPath(path))

    def test_no_product_series_branch(self):
        # getByLPPath raises `NoLinkedBranch` if there's no branch registered
        # linked to the requested series.
        series = self.factory.makeSeries()
        short_name = '%s/%s' % (series.product.name, series.name)
        exception = self.assertRaises(
            NoLinkedBranch, self.branch_lookup.getByLPPath, short_name)
        self.assertEqual(series, exception.component)

    def test_product_with_no_dev_focus(self):
        # getByLPPath raises `NoLinkedBranch` if the product is found but
        # doesn't have a development focus branch.
        product = self.factory.makeProduct()
        exception = self.assertRaises(
            NoLinkedBranch, self.branch_lookup.getByLPPath, product.name)
        self.assertEqual(product, exception.component)

    def test_private_linked_branch(self):
        # If the given path refers to an object with an invisible linked
        # branch, then getByLPPath raises `NoLinkedBranch`, as if the branch
        # weren't there at all.
        branch = self.factory.makeProductBranch(private=True)
        product = removeSecurityProxy(branch).product
        removeSecurityProxy(product).development_focus.user_branch = branch
        self.assertRaises(
            NoLinkedBranch, self.branch_lookup.getByLPPath, product.name)

    def test_no_official_branch(self):
        sourcepackage = self.factory.makeSourcePackage()
        exception = self.assertRaises(
            NoLinkedBranch,
            self.branch_lookup.getByLPPath, sourcepackage.path)
        sourcepackagepocket =  getUtility(ISourcePackagePocketFactory).new(
            sourcepackage, PackagePublishingPocket.RELEASE)
        self.assertEqual(sourcepackagepocket, exception.component)

    def test_distribution_linked_branch(self):
        # Distributions cannot have linked branches, so `getByLPPath` raises a
        # `CannotHaveLinkedBranch` error if we try to get the linked branch
        # for a distribution.
        distribution = self.factory.makeDistribution()
        exception = self.assertRaises(
            CannotHaveLinkedBranch,
            self.branch_lookup.getByLPPath, distribution.name)
        self.assertEqual(distribution, exception.component)

    def test_project_linked_branch(self):
        # Projects cannot have linked branches, so `getByLPPath` raises a
        # `CannotHaveLinkedBranch` error if we try to get the linked branch
        # for a project.
        project = self.factory.makeProject()
        exception = self.assertRaises(
            CannotHaveLinkedBranch,
            self.branch_lookup.getByLPPath, project.name)
        self.assertEqual(project, exception.component)

    def test_partial_lookup(self):
        owner = self.factory.makePerson()
        product = self.factory.makeProduct()
        path = '~%s/%s' % (owner.name, product.name)
        self.assertRaises(
            InvalidNamespace, self.branch_lookup.getByLPPath, path)


class TestSourcePackagePocket(TestCaseWithFactory):
    """Tests for the SourcePackagePocket wrapper class."""

    layer = DatabaseFunctionalLayer

    def makeSourcePackagePocket(self, sourcepackage=None, pocket=None):
        if sourcepackage is None:
            sourcepackage = self.factory.makeSourcePackage()
        if pocket is None:
            pocket = PackagePublishingPocket.RELEASE
        return getUtility(ISourcePackagePocketFactory).new(
            sourcepackage, pocket)

    def test_suite_release_pocket(self):
        # The suite of a RELEASE source package pocket is the name of the
        # distroseries.
        package = self.factory.makeSourcePackage()
        package_pocket = self.makeSourcePackagePocket(
            package, PackagePublishingPocket.RELEASE)
        self.assertEqual(package.distroseries.name, package_pocket.suite)

    def test_suite_non_release_pocket(self):
        # The suite of a non-RELEASE source package pocket is the name of the
        # distroseries, followed by a hyphen and the lower-case name of the
        # pocket.
        package = self.factory.makeSourcePackage()
        pocket = PackagePublishingPocket.SECURITY
        package_pocket = self.makeSourcePackagePocket(package, pocket)
        self.assertEqual(
            '%s-%s' % (package.distroseries.name, pocket.name.lower()),
            package_pocket.suite)

    def test_branch(self):
        # The 'branch' attribute is the linked branch for the pocket on that
        # packet.
        package = self.factory.makeSourcePackage()
        branch = self.factory.makePackageBranch(sourcepackage=package)
        registrant = self.factory.makePerson()
        ubuntu_branches = getUtility(ILaunchpadCelebrities).ubuntu_branches
        login_person(ubuntu_branches.teamowner)
        try:
            package.setBranch(
                PackagePublishingPocket.SECURITY, branch, registrant)
        finally:
            login(ANONYMOUS)
        package_pocket = self.makeSourcePackagePocket(
            sourcepackage=package, pocket=PackagePublishingPocket.SECURITY)
        self.assertEqual(branch, package_pocket.branch)

    def test_path_release_pocket(self):
        # The path of a RELEASE source package pocket is the path of the
        # source package.
        package = self.factory.makeSourcePackage()
        package_pocket = self.makeSourcePackagePocket(
            package, PackagePublishingPocket.RELEASE)
        self.assertEqual(package.path, package_pocket.path)

    def test_path_non_release_pocket(self):
        # The path of a non-RELEASE source package pocket is the path of the
        # source package, except with the middle series component replaced by
        # <series>-<pocket>.
        package = self.factory.makeSourcePackage()
        package_pocket = self.makeSourcePackagePocket(
            package, PackagePublishingPocket.BACKPORTS)
        self.assertEqual(
            '%s/%s-%s/%s' % (
                package.distribution.name,
                package.distroseries.name,
                PackagePublishingPocket.BACKPORTS.name.lower(),
                package.sourcepackagename.name),
            package_pocket.path)

    def test_display_name(self):
        # A SourcePackagePocket also has a display name, so we can use it in
        # error messages.
        package_pocket = self.makeSourcePackagePocket()
        self.assertEqual(package_pocket.path, package_pocket.displayname)

    def test_equality(self):
        package = self.factory.makeSourcePackage()
        pocket = PackagePublishingPocket.SECURITY
        package_pocket1 = self.makeSourcePackagePocket(package, pocket)
        package_pocket2 = self.makeSourcePackagePocket(package, pocket)
        self.assertEqual(package_pocket1, package_pocket2)


def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
