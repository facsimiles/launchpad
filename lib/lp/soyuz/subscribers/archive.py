# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Event subscribers for source package uploads"""

from zope.component import getUtility

from lp.buildmaster.enums import BuildStatus
from lp.services.features import getFeatureFlag
from lp.services.webapp.publisher import canonical_url
from lp.services.webhooks.interfaces import IWebhookSet
from lp.soyuz.enums import PackageUploadStatus
from lp.soyuz.interfaces.archive import ARCHIVE_WEBHOOKS_FEATURE_FLAG


def _trigger_source_package_status_change_webhook(upload, event_type):
    if getFeatureFlag(ARCHIVE_WEBHOOKS_FEATURE_FLAG):
        payload = {
            "package_upload": canonical_url(upload, force_local_path=True),
            "action": "status-changed",
            "status": upload.status.name,
            "archive": canonical_url(upload.archive, force_local_path=True),
        }

        # Source package information
        if upload.sources and upload.sources[0].sourcepackagerelease:
            payload["package_name"] = str(
                upload.sources[0].sourcepackagerelease.sourcepackagename
            )
            payload["package_version"] = str(
                upload.sources[0].sourcepackagerelease.version
            )

        getUtility(IWebhookSet).trigger(upload.archive, event_type, payload)


def _trigger_binary_package_status_change_webhook(upload, event_type):
    if getFeatureFlag(ARCHIVE_WEBHOOKS_FEATURE_FLAG):
        payload = {
            "package_upload": canonical_url(upload, force_local_path=True),
            "action": "status-changed",
            "status": upload.status.name,
            "archive": canonical_url(upload.archive, force_local_path=True),
            "source_package_name": str(
                upload.builds[0].build.source_package_release.sourcepackagename
            ),
        }
        getUtility(IWebhookSet).trigger(upload.archive, event_type, payload)


def _trigger_build_status_change_webhook(build, event_type):
    if getFeatureFlag(ARCHIVE_WEBHOOKS_FEATURE_FLAG):
        payload = {
            "build": canonical_url(build, force_local_path=True),
            "action": "status-changed",
            "status": build.status.name,
            "archive": canonical_url(build.archive, force_local_path=True),
            "source_package_name": str(
                build.source_package_release.sourcepackagename
            ),
            "buildlog": build.log_url,
        }

        getUtility(IWebhookSet).trigger(build.archive, event_type, payload)


def package_status_change_webhook(upload, event):
    """Webhook for source package uploads."""

    # An upload can be a source package or a binary package.
    # Source packages don't have any builds and binary packages
    # don't have any sources.

    # For source packages
    # Instead of checking upload.sources, we check upload.builds, because
    # there are instances of rejected source package uploads which do not have
    # any sources
    if not upload.builds:
        if (
            event.edited_fields
            and "status" in event.edited_fields
            and (
                upload.status == PackageUploadStatus.ACCEPTED
                or upload.status == PackageUploadStatus.REJECTED
                or upload.status == PackageUploadStatus.UNAPPROVED
            )
        ):
            _trigger_source_package_status_change_webhook(
                upload,
                f"archive:source-package-upload:0.1::"
                f"{upload.status.name.lower()}",
            )

    # For binary packages
    else:
        if (
            event.edited_fields
            and "status" in event.edited_fields
            and (
                upload.status == PackageUploadStatus.ACCEPTED
                or upload.status == PackageUploadStatus.REJECTED
                or upload.status == PackageUploadStatus.UNAPPROVED
            )
        ):
            _trigger_binary_package_status_change_webhook(
                upload,
                f"archive:binary-package-upload:0.1::"
                f"{upload.status.name.lower()}",
            )


def build_status_change_webhook(build, event):
    """Webhook for binary builds"""

    if (
        event.edited_fields
        and "status" in event.edited_fields
        and (
            build.status == BuildStatus.FULLYBUILT
            or build.status == BuildStatus.FAILEDTOBUILD
            or build.status == BuildStatus.CHROOTWAIT
            or build.status == BuildStatus.CANCELLED
            or build.status == BuildStatus.FAILEDTOUPLOAD
            or build.status == BuildStatus.SUPERSEDED
        )
    ):
        _trigger_build_status_change_webhook(
            build, f"archive:binary-build:0.1::{build.status.name.lower()}"
        )
