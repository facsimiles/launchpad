# Copyright 2015 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""A person's view on a source package in a distribution."""

__metaclass__ = type
__all__ = [
    'PersonDistributionSourcePackage',
    ]

from zope.interface import (
    classProvides,
    implements,
    )

from lp.registry.interfaces.persondistributionsourcepackage import (
    IPersonDistributionSourcePackage,
    IPersonDistributionSourcePackageFactory,
    )


class PersonDistributionSourcePackage:

    implements(IPersonDistributionSourcePackage)

    classProvides(IPersonDistributionSourcePackageFactory)

    def __init__(self, person, distro_source_package):
        self.person = person
        self.distro_source_package = distro_source_package

    @staticmethod
    def create(person, distro_source_package):
        return PersonDistributionSourcePackage(person, distro_source_package)

    @property
    def displayname(self):
        return '%s in %s' % (
            self.person.displayname, self.distro_source_package.displayname)
