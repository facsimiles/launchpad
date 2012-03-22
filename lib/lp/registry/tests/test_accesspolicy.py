# Copyright 2011-2012 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__metaclass__ = type

from storm.exceptions import LostObjectError
from testtools.matchers import AllMatch
from zope.component import getUtility

from lp.registry.enums import (
    InformationType,
    SharingPermission,
    )
from lp.registry.interfaces.accesspolicy import (
    IAccessArtifact,
    IAccessArtifactGrant,
    IAccessArtifactGrantSource,
    IAccessArtifactSource,
    IAccessPolicy,
    IAccessPolicyArtifact,
    IAccessPolicyArtifactSource,
    IAccessPolicyGrant,
    IAccessPolicyGrantFlatSource,
    IAccessPolicyGrantSource,
    IAccessPolicySource,
    )
from lp.services.database.lpstorm import IStore
from lp.testing import TestCaseWithFactory
from lp.testing.layers import DatabaseFunctionalLayer
from lp.testing.matchers import Provides


class TestAccessPolicy(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_provides_interface(self):
        self.assertThat(
            self.factory.makeAccessPolicy(), Provides(IAccessPolicy))

    def test_pillar(self):
        product = self.factory.makeProduct()
        policy = self.factory.makeAccessPolicy(pillar=product)
        self.assertEqual(product, policy.pillar)


class TestAccessPolicySource(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_create(self):
        wanted = [
            (self.factory.makeProduct(), InformationType.PROPRIETARY),
            (self.factory.makeDistribution(),
                InformationType.UNEMBARGOEDSECURITY),
            ]
        policies = getUtility(IAccessPolicySource).create(wanted)
        self.assertThat(
            policies,
            AllMatch(Provides(IAccessPolicy)))
        self.assertContentEqual(
            wanted,
            [(policy.pillar, policy.type) for policy in policies])

    def test_find(self):
        # find() finds the right policies.
        product = self.factory.makeProduct()
        distribution = self.factory.makeDistribution()
        other_product = self.factory.makeProduct()

        wanted = [
            (product, InformationType.PROPRIETARY),
            (product, InformationType.UNEMBARGOEDSECURITY),
            (distribution, InformationType.PROPRIETARY),
            (distribution, InformationType.UNEMBARGOEDSECURITY),
            (other_product, InformationType.PROPRIETARY),
            ]
        getUtility(IAccessPolicySource).create(wanted)

        query = [
            (product, InformationType.PROPRIETARY),
            (product, InformationType.UNEMBARGOEDSECURITY),
            (distribution, InformationType.UNEMBARGOEDSECURITY),
            ]
        self.assertContentEqual(
            query,
            [(policy.pillar, policy.type) for policy in
             getUtility(IAccessPolicySource).find(query)])

        query = [(distribution, InformationType.PROPRIETARY)]
        self.assertContentEqual(
            query,
            [(policy.pillar, policy.type) for policy in
             getUtility(IAccessPolicySource).find(query)])

    def test_findByID(self):
        # findByID finds the right policies.
        policies = [self.factory.makeAccessPolicy() for i in range(2)]
        self.factory.makeAccessPolicy()
        self.assertContentEqual(
            policies,
            getUtility(IAccessPolicySource).findByID(
                [policy.id for policy in policies]))

    def test_findByPillar(self):
        # findByPillar finds only the relevant policies.
        product = self.factory.makeProduct()
        distribution = self.factory.makeProduct()
        other_product = self.factory.makeProduct()
        policies = (
            (product, InformationType.EMBARGOEDSECURITY),
            (product, InformationType.USERDATA),
            (distribution, InformationType.EMBARGOEDSECURITY),
            (distribution, InformationType.USERDATA),
            (other_product, InformationType.EMBARGOEDSECURITY),
            (other_product, InformationType.USERDATA),
            )
        self.assertContentEqual(
            policies,
            [(ap.pillar, ap.type)
                for ap in getUtility(IAccessPolicySource).findByPillar(
                [product, distribution, other_product])])
        self.assertContentEqual(
            [policy for policy in policies if policy[0] == product],
            [(ap.pillar, ap.type)
                for ap in getUtility(IAccessPolicySource).findByPillar(
                    [product])])


class TestAccessArtifact(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_provides_interface(self):
        self.assertThat(
            self.factory.makeAccessArtifact(),
            Provides(IAccessArtifact))


class TestAccessArtifactSourceOnce(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_ensure_other_fails(self):
        # ensure() rejects unsupported objects.
        self.assertRaises(
            ValueError,
            getUtility(IAccessArtifactSource).ensure,
            [self.factory.makeProduct()])


class BaseAccessArtifactTests:
    layer = DatabaseFunctionalLayer

    def getConcreteArtifact(self):
        raise NotImplementedError()

    def test_ensure(self):
        # ensure() creates abstract artifacts which map to the
        # concrete ones.
        concretes = [self.getConcreteArtifact() for i in range(2)]
        abstracts = getUtility(IAccessArtifactSource).ensure(concretes)
        self.assertContentEqual(
            concretes,
            [abstract.concrete_artifact for abstract in abstracts])

    def test_find(self):
        # find() finds abstract artifacts which map to the concrete ones.
        concretes = [self.getConcreteArtifact() for i in range(2)]
        abstracts = getUtility(IAccessArtifactSource).ensure(concretes)
        self.assertContentEqual(
            abstracts, getUtility(IAccessArtifactSource).find(concretes))

    def test_ensure_twice(self):
        # ensure() will reuse an existing matching abstract artifact if
        # it exists.
        concrete1 = self.getConcreteArtifact()
        concrete2 = self.getConcreteArtifact()
        [abstract1] = getUtility(IAccessArtifactSource).ensure([concrete1])

        abstracts = getUtility(IAccessArtifactSource).ensure(
            [concrete1, concrete2])
        self.assertIn(abstract1, abstracts)
        self.assertContentEqual(
            [concrete1, concrete2],
            [abstract.concrete_artifact for abstract in abstracts])

    def test_delete(self):
        # delete() removes the abstract artifacts and any associated
        # grants.
        concretes = [self.getConcreteArtifact() for i in range(2)]
        abstracts = getUtility(IAccessArtifactSource).ensure(concretes)
        grant = self.factory.makeAccessArtifactGrant(artifact=abstracts[0])
        link = self.factory.makeAccessPolicyArtifact(artifact=abstracts[0])
        self.assertContentEqual(
            [link],
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [abstracts[0]]))

        # Make some other grants and links to ensure they're unaffected.
        other_grants = [
            self.factory.makeAccessArtifactGrant(
                artifact=self.factory.makeAccessArtifact()),
            self.factory.makeAccessPolicyGrant(
                policy=self.factory.makeAccessPolicy()),
            ]
        other_link = self.factory.makeAccessPolicyArtifact()

        getUtility(IAccessArtifactSource).delete(concretes)
        IStore(grant).invalidate()
        self.assertRaises(LostObjectError, getattr, grant, 'grantor')
        self.assertRaises(
            LostObjectError, getattr, abstracts[0], 'concrete_artifact')

        for other_grant in other_grants:
            self.assertIsNot(None, other_grant.grantor)

        self.assertContentEqual(
            [],
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [abstracts[0]]))
        self.assertContentEqual(
            [other_link],
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [other_link.abstract_artifact]))

    def test_delete_noop(self):
        # delete() works even if there's no abstract artifact.
        concrete = self.getConcreteArtifact()
        getUtility(IAccessArtifactSource).delete([concrete])


class TestAccessArtifactBranch(BaseAccessArtifactTests,
                               TestCaseWithFactory):

    def getConcreteArtifact(self):
        return self.factory.makeBranch()


class TestAccessArtifactBug(BaseAccessArtifactTests,
                            TestCaseWithFactory):

    def getConcreteArtifact(self):
        return self.factory.makeBug()


class TestAccessArtifactGrant(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_provides_interface(self):
        self.assertThat(
            self.factory.makeAccessArtifactGrant(),
            Provides(IAccessArtifactGrant))

    def test_concrete_artifact(self):
        bug = self.factory.makeBug()
        abstract = self.factory.makeAccessArtifact(bug)
        grant = self.factory.makeAccessArtifactGrant(artifact=abstract)
        self.assertEqual(bug, grant.concrete_artifact)


class TestAccessArtifactGrantSource(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_grant(self):
        wanted = [
            (self.factory.makeAccessArtifact(), self.factory.makePerson(),
             self.factory.makePerson()),
            (self.factory.makeAccessArtifact(), self.factory.makePerson(),
             self.factory.makePerson()),
            ]
        grants = getUtility(IAccessArtifactGrantSource).grant(wanted)
        self.assertContentEqual(
            wanted,
            [(g.abstract_artifact, g.grantee, g.grantor) for g in grants])

    def test_find(self):
        # find() finds the right grants.
        grants = [self.factory.makeAccessArtifactGrant() for i in range(2)]
        self.assertContentEqual(
            grants,
            getUtility(IAccessArtifactGrantSource).find(
                [(g.abstract_artifact, g.grantee) for g in grants]))

    def test_findByArtifact(self):
        # findByArtifact() finds only the relevant grants.
        artifact = self.factory.makeAccessArtifact()
        grants = [
            self.factory.makeAccessArtifactGrant(artifact=artifact)
            for i in range(3)]
        self.factory.makeAccessArtifactGrant()
        self.assertContentEqual(
            grants,
            getUtility(IAccessArtifactGrantSource).findByArtifact([artifact]))

    def test_revokeByArtifact(self):
        # revokeByArtifact() removes the relevant grants.
        artifact = self.factory.makeAccessArtifact()
        grant = self.factory.makeAccessArtifactGrant(artifact=artifact)
        other_grant = self.factory.makeAccessArtifactGrant()
        getUtility(IAccessArtifactGrantSource).revokeByArtifact([artifact])
        IStore(grant).invalidate()
        self.assertRaises(LostObjectError, getattr, grant, 'grantor')
        self.assertIsNot(None, other_grant.grantor)


class TestAccessPolicyArtifact(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_provides_interface(self):
        self.assertThat(
            self.factory.makeAccessPolicyArtifact(),
            Provides(IAccessPolicyArtifact))


class TestAccessPolicyArtifactSource(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_create(self):
        wanted = [
            (self.factory.makeAccessArtifact(),
             self.factory.makeAccessPolicy()),
            (self.factory.makeAccessArtifact(),
             self.factory.makeAccessPolicy()),
            ]
        links = getUtility(IAccessPolicyArtifactSource).create(wanted)
        self.assertContentEqual(
            wanted,
            [(link.abstract_artifact, link.policy) for link in links])

    def test_find(self):
        links = [self.factory.makeAccessPolicyArtifact() for i in range(3)]
        self.assertContentEqual(
            links,
            getUtility(IAccessPolicyArtifactSource).find(
                [(link.abstract_artifact, link.policy) for link in links]))

    def test_findByArtifact(self):
        # findByArtifact() finds only the relevant links.
        artifact = self.factory.makeAccessArtifact()
        links = [
            self.factory.makeAccessPolicyArtifact(artifact=artifact)
            for i in range(3)]
        self.factory.makeAccessPolicyArtifact()
        self.assertContentEqual(
            links,
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [artifact]))

    def test_findByPolicy(self):
        # findByPolicy() finds only the relevant links.
        policy = self.factory.makeAccessPolicy()
        links = [
            self.factory.makeAccessPolicyArtifact(policy=policy)
            for i in range(3)]
        self.factory.makeAccessPolicyArtifact()
        self.assertContentEqual(
            links,
            getUtility(IAccessPolicyArtifactSource).findByPolicy([policy]))

    def test_deleteByArtifact(self):
        # deleteByArtifact() removes the relevant grants.
        grant = self.factory.makeAccessPolicyArtifact()
        other_grant = self.factory.makeAccessPolicyArtifact()
        getUtility(IAccessPolicyArtifactSource).deleteByArtifact(
            [grant.abstract_artifact])
        self.assertContentEqual(
            [],
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [grant.abstract_artifact]))
        self.assertContentEqual(
            [other_grant],
            getUtility(IAccessPolicyArtifactSource).findByArtifact(
                [other_grant.abstract_artifact]))


class TestAccessPolicyGrant(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_provides_interface(self):
        self.assertThat(
            self.factory.makeAccessPolicyGrant(),
            Provides(IAccessPolicyGrant))


class TestAccessPolicyGrantSource(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_grant(self):
        wanted = [
            (self.factory.makeAccessPolicy(), self.factory.makePerson(),
             self.factory.makePerson()),
            (self.factory.makeAccessPolicy(), self.factory.makePerson(),
             self.factory.makePerson()),
            ]
        grants = getUtility(IAccessPolicyGrantSource).grant(wanted)
        self.assertContentEqual(
            wanted, [(g.policy, g.grantee, g.grantor) for g in grants])

    def test_find(self):
        # find() finds the right grants.
        grants = [self.factory.makeAccessPolicyGrant() for i in range(2)]
        self.assertContentEqual(
            grants,
            getUtility(IAccessPolicyGrantSource).find(
                [(g.policy, g.grantee) for g in grants]))

    def test_findByPolicy(self):
        # findByPolicy() finds only the relevant grants.
        policy = self.factory.makeAccessPolicy()
        grants = [
            self.factory.makeAccessPolicyGrant(policy=policy)
            for i in range(3)]
        self.factory.makeAccessPolicyGrant()
        self.assertContentEqual(
            grants,
            getUtility(IAccessPolicyGrantSource).findByPolicy([policy]))

    def test_revoke(self):
        # revoke() removes the specified grants.
        policy = self.factory.makeAccessPolicy()
        grants = [
            self.factory.makeAccessPolicyGrant(policy=policy)
            for i in range(3)]

        # Make some other grants to ensure they're unaffected.
        other_grants = [
            self.factory.makeAccessPolicyGrant(policy=policy)
            for i in range(3)]
        other_grants.extend([
            self.factory.makeAccessPolicyGrant()
            for i in range(3)])

        to_delete = [(grant.policy, grant.grantee) for grant in grants]
        getUtility(IAccessPolicyGrantSource).revoke(to_delete)
        IStore(policy).invalidate()

        for grant in grants:
            self.assertRaises(LostObjectError, getattr, grant, 'grantor')
        self.assertEqual(
            0, getUtility(IAccessPolicyGrantSource).find(to_delete).count())
        for other_grant in other_grants:
            self.assertIsNot(None, other_grant.grantor)


class TestAccessPolicyGrantFlatSource(TestCaseWithFactory):
    layer = DatabaseFunctionalLayer

    def test_findGranteesByPolicy(self):
        # findGranteesByPolicy() returns anyone with a grant for any of
        # the policies or the policies' artifacts.
        apgfs = getUtility(IAccessPolicyGrantFlatSource)

        # People with grants on the policy show up.
        policy_with_no_grantees = self.factory.makeAccessPolicy()
        policy = self.factory.makeAccessPolicy()
        policy_grant = self.factory.makeAccessPolicyGrant(policy=policy)
        self.assertContentEqual(
            [policy_grant.grantee],
            apgfs.findGranteesByPolicy([policy, policy_with_no_grantees]))

        # But not people with grants on artifacts.
        artifact_grant = self.factory.makeAccessArtifactGrant()
        self.assertContentEqual(
            [policy_grant.grantee],
            apgfs.findGranteesByPolicy([policy, policy_with_no_grantees]))

        # Unless the artifacts are linked to the policy.
        another_policy = self.factory.makeAccessPolicy()
        self.factory.makeAccessPolicyArtifact(
            artifact=artifact_grant.abstract_artifact, policy=another_policy)
        self.assertContentEqual(
            [policy_grant.grantee, artifact_grant.grantee],
            apgfs.findGranteesByPolicy([
                policy, another_policy, policy_with_no_grantees]))

    def test_findGranteePermissionsByPolicy(self):
        # findGranteePermissionsByPolicy() returns anyone with a grant for any
        # of the policies or the policies' artifacts.
        apgfs = getUtility(IAccessPolicyGrantFlatSource)

        # People with grants on the policy show up.
        policy_with_no_grantees = self.factory.makeAccessPolicy()
        policy = self.factory.makeAccessPolicy()
        policy_grant = self.factory.makeAccessPolicyGrant(policy=policy)
        self.assertContentEqual(
            [(policy_grant.grantee, policy, SharingPermission.ALL)],
            apgfs.findGranteePermissionsByPolicy(
                [policy, policy_with_no_grantees]))

        # But not people with grants on artifacts.
        artifact_grant = self.factory.makeAccessArtifactGrant()
        self.assertContentEqual(
            [(policy_grant.grantee, policy, SharingPermission.ALL)],
            apgfs.findGranteePermissionsByPolicy(
                [policy, policy_with_no_grantees]))

        # Unless the artifacts are linked to the policy.
        another_policy = self.factory.makeAccessPolicy()
        self.factory.makeAccessPolicyArtifact(
            artifact=artifact_grant.abstract_artifact, policy=another_policy)
        self.assertContentEqual(
            [(policy_grant.grantee, policy, SharingPermission.ALL),
            (artifact_grant.grantee, another_policy, SharingPermission.SOME)],
            apgfs.findGranteePermissionsByPolicy([
                policy, another_policy, policy_with_no_grantees]))

    def test_findGranteePermissionsByPolicy_filter_grantees(self):
        # findGranteePermissionsByPolicy() returns anyone with a grant for any
        # of the policies or the policies' artifacts so long as the grantee is
        # in the specified list of grantees.
        apgfs = getUtility(IAccessPolicyGrantFlatSource)

        # People with grants on the policy show up.
        policy = self.factory.makeAccessPolicy()
        grantee_in_result = self.factory.makePerson()
        grantee_not_in_result = self.factory.makePerson()
        policy_grant = self.factory.makeAccessPolicyGrant(
            policy=policy, grantee=grantee_in_result)
        self.factory.makeAccessPolicyGrant(
            policy=policy, grantee=grantee_not_in_result)
        self.assertContentEqual(
            [(policy_grant.grantee, policy, SharingPermission.ALL)],
            apgfs.findGranteePermissionsByPolicy(
                [policy], [grantee_in_result]))

    def test_findArtifactsByGrantee(self):
        # findArtifactsByGrantee() returns the artifacts for grantee for any of
        # the policies.
        apgfs = getUtility(IAccessPolicyGrantFlatSource)
        policy = self.factory.makeAccessPolicy()
        grantee = self.factory.makePerson()
        # Artifacts not linked to the policy do not show up.
        artifact = self.factory.makeAccessArtifact()
        self.factory.makeAccessArtifactGrant(artifact, grantee)
        self.assertContentEqual(
            [], apgfs.findArtifactsByGrantee(grantee, [policy]))
        # Artifacts linked to the policy do show up.
        self.factory.makeAccessPolicyArtifact(artifact=artifact, policy=policy)
        self.assertContentEqual(
            [artifact], apgfs.findArtifactsByGrantee(grantee, [policy]))
