# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""Source package in Distribution Cache interfaces."""

__metaclass__ = type

__all__ = [
    'IDistributionSourcePackageCache',
    ]

from zope.interface import Interface, Attribute

class IDistributionSourcePackageCache(Interface):

    distribution = Attribute("The distribution.")
    sourcepackagename = Attribute("The source package name.")

    name = Attribute("The source package name as text.")
    binpkgnames = Attribute("A concatenation of the binary package names "
        "associated with this source package in the distribution.")
    binpkgsummaries = Attribute("A concatenation of the binary package "
        "summaries for this source package.")
    binpkgdescriptions = Attribute("A concatenation of the descriptions "
        "of the binary packages from this source package name in the "
        "distro.")

    distributionsourcepackage = Attribute("The DistributionSourcePackage "
        "for which this is a cache.")

