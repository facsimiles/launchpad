# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

"""Distribution architecture release interfaces."""

__metaclass__ = type

__all__ = [
    'IDistroArchRelease',
    'IPocketChroot',
    ]

from zope.interface import Interface, Attribute
from zope.i18nmessageid import MessageIDFactory

from canonical.launchpad.interfaces import IHasOwner

_ = MessageIDFactory('launchpad')

class IDistroArchRelease(IHasOwner):
    """DistroArchRelease Table Interface"""
    id = Attribute("Identifier")
    distrorelease = Attribute("DistroRelease")
    processorfamily = Attribute("ProcessorFamily")
    architecturetag = Attribute("ArchitectureTag")
    owner = Attribute("Owner")

    #joins
    packages = Attribute('List of binary packages in this port.')

    # for page layouts etc
    title = Attribute('Title')

    # useful attributes
    binarycount = Attribute('Count of Binary Packages')
    isNominatedArchIndep = Attribute(
        'True if this distroarchrelease is the NominatedArchIndep one.')

    def getChroot(pocket=None, default=None):
        """Return the librarian file alias of the chroot for a given Pocket.

        The pocket defaults to the RELEASE pocket and if not found returns
        'default'.
        """

    def findPackagesByName(pattern):
        """Search BinaryPackages matching pattern"""

    def getReleasedPackages(name, pocket=None):
        """Get the publishing records for the given binary package name.

        The 'name' passed in should either be a BinaryPackageName instance
        or else a string which will be looked up as a BinaryPackageName.

        If pocket is not specified, we look in all pockets.
        """

    def findPackagesByArchtagName(pattern, fti=False):
        """Search BinaryPackages matching pattern and archtag"""

    def __getitem__(name):
        """Getter"""

class IPocketChroot(Interface):
    """PocketChroot Table Interface"""

    distroarchrelease = Attribute("The DistroArchRelease this chroot "
                                  "belongs to.")
    pocket = Attribute("The Pocket this chroot is for.")
    chroot = Attribute("The file alias of the chroot.")

