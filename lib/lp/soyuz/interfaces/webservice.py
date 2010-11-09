# Copyright 2010 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""All the interfaces that are exposed through the webservice."""

__all__ = [
    'AlreadySubscribed',
    'ArchiveDisabled',
    'ArchiveNotPrivate',
    'CannotBeRescored',
    'CannotCopy',
    'CannotSwitchPrivacy',
    'CannotUploadToArchive',
    'CannotUploadToPPA',
    'CannotUploadToPocket',
    'ComponentNotFound',
    'DistroSeriesNotFound',
    'DuplicatePackagesetName',
    'IArchive',
    'IArchiveDependency',
    'IArchivePermission',
    'IArchiveSubscriber',
    'IBinaryPackageBuild',
    'IBinaryPackagePublishingHistory',
    'IBinaryPackageReleaseDownloadCount',
    'IDistroArchSeries',
    'IPackageUpload',
    'IPackageset',
    'IPackagesetEdit',
    'IPackagesetSet',
    'IPackagesetViewOnly',
    'IncompatibleArguments',
    'InsufficientUploadRights',
    'InvalidComponent',
    'InvalidPocketForPPA',
    'InvalidPocketForPartnerArchive',
    'NoRightsForArchive',
    'NoRightsForComponent',
    'NoSuchPPA',
    'NoSuchPackageSet',
    'NoTokensForTeams',
    'PocketNotFound',
    'VersionRequiresName',
    ]

from lp.soyuz.interfaces.archive import (
    AlreadySubscribed,
    ArchiveDisabled,
    ArchiveNotPrivate,
    CannotCopy,
    CannotSwitchPrivacy,
    CannotUploadToArchive,
    CannotUploadToPPA,
    CannotUploadToPocket,
    ComponentNotFound,
    DistroSeriesNotFound,
    IArchive,
    InsufficientUploadRights,
    InvalidComponent,
    InvalidPocketForPPA,
    InvalidPocketForPartnerArchive,
    NoRightsForArchive,
    NoRightsForComponent,
    NoSuchPPA,
    NoTokensForTeams,
    PocketNotFound,
    VersionRequiresName,
    )
from lp.soyuz.interfaces.archivedependency import IArchiveDependency
from lp.soyuz.interfaces.archivepermission import IArchivePermission
from lp.soyuz.interfaces.archivesubscriber import IArchiveSubscriber
from lp.soyuz.interfaces.binarypackagebuild import (
    CannotBeRescored,
    IBinaryPackageBuild,
    )
from lp.soyuz.interfaces.binarypackagerelease import (
    IBinaryPackageReleaseDownloadCount,
    )
from lp.soyuz.interfaces.buildrecords import (
    IncompatibleArguments,
    )
from lp.soyuz.interfaces.distroarchseries import IDistroArchSeries
from lp.soyuz.interfaces.packageset import (
    DuplicatePackagesetName,
    IPackagesetViewOnly,
    IPackagesetEdit,
    IPackageset,
    IPackagesetSet,
    NoSuchPackageSet,
    )
from lp.soyuz.interfaces.publishing import IBinaryPackagePublishingHistory
from lp.soyuz.interfaces.queue import IPackageUpload
