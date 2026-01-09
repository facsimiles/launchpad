# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = ["CTDeliveryDebJob"]

import logging
from datetime import datetime, timedelta, timezone

from storm.expr import (
    SQL,
    Alias,
    And,
    Column,
    Eq,
    Gt,
    Join,
    Le,
    LeftJoin,
    Lt,
    Ne,
    Select,
    Table,
)
from zope.component import getUtility
from zope.interface import implementer, provider

from lp.archivepublisher.interfaces.ctdeliveryjob import (
    CTDeliveryJobType,
    ICTDeliveryDebJob,
    ICTDeliveryDebJobSource,
)
from lp.archivepublisher.model.archivepublisherrun import (
    ArchivePublisherRun,
    ArchivePublisherRunStatus,
)
from lp.archivepublisher.model.archivepublishinghistory import (
    ArchivePublishingHistory,
)
from lp.archivepublisher.model.ctdeliveryjob import (
    CTDeliveryJob,
    CTDeliveryJobDerived,
)
from lp.registry.interfaces.pocket import PackagePublishingPocket, pocketsuffix
from lp.services.commitmenttracker import get_commitment_tracker_client
from lp.services.config import config
from lp.services.database.interfaces import IPrimaryStore, IStore
from lp.services.features import getFeatureFlag
from lp.services.job.model.job import Job
from lp.soyuz.enums import ArchivePurpose, PackagePublishingStatus
from lp.soyuz.interfaces.archive import IArchiveSet

logger = logging.getLogger(__name__)

CT_DELIVERY_ENABLED = "commitment_tracker.delivery.enabled"

POCKET_TO_NAME = {
    item.value: pocketsuffix[item][1:] if pocketsuffix[item] else None
    for item in PackagePublishingPocket.items
}


@implementer(ICTDeliveryDebJob)
@provider(ICTDeliveryDebJobSource)
class CTDeliveryDebJob(CTDeliveryJobDerived):
    class_job_type = CTDeliveryJobType.DEB

    user_error_types = ()
    retry_error_types = ()

    # Retry sooner than the default.
    retry_delay = timedelta(minutes=5)
    max_retries = 3

    config = config.ICTDeliveryDebJobSource

    @staticmethod
    def _is_delivery_enabled():
        """Return True if the CT delivery feature flag is enabled."""
        return bool(getFeatureFlag(CT_DELIVERY_ENABLED))

    @property
    def publishing_history(self):
        # Prefer the Storm-loaded reference on the context; fall back to an
        # explicit fetch by id if not already loaded.
        if getattr(self.context, "publishing_history", None) is not None:
            return self.context.publishing_history
        return IStore(ArchivePublishingHistory).get(
            self.context.publishing_history_id
        )

    @property
    def error_description(self):
        return self.metadata.get("result", {}).get("error_description", [])

    @property
    def metadata(self):
        return self.context.metadata

    @classmethod
    def create(cls, publishing_history_id):
        """Create a new `CTDeliveryDebJob` using `IArchivePublishingHistory`.

        :param publishing_history_id: The id of the
            `IArchivePublishingHistory` associated with this job.
        """
        if not cls._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag %s",
                CT_DELIVERY_ENABLED,
            )
            return None

        if publishing_history_id is None:
            raise ValueError("publishing_history not found")

        # Schedule the initialization.
        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
        }

        ctdeliveryjob = CTDeliveryJob(
            publishing_history_id, cls.class_job_type, metadata
        )
        # Configure retry policy for the underlying Job.
        ctdeliveryjob.job.max_retries = cls.max_retries

        store = IPrimaryStore(CTDeliveryJob)
        store.add(ctdeliveryjob)
        derived_job = cls(ctdeliveryjob)
        derived_job.celeryRunOnCommit()
        IStore(CTDeliveryJob).flush()
        return derived_job

    @classmethod
    def create_manual(cls, archive_id, date_start, date_end):
        """Create a new `CTDeliveryDebJob` manually.

        :param archive_id: The id of the archive to process.
        :param date_start: Start of the date range.
        :param date_end: End of the date range.
        """
        if not cls._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag %s",
                CT_DELIVERY_ENABLED,
            )
            return None
        # Manual mode: require archive_id and date range
        if archive_id is None:
            raise ValueError("archive_id is required")

        if date_start is None or date_end is None:
            raise ValueError("date_start and date_end are required")

        if date_start > date_end:
            raise ValueError(
                "date_start must be less than or equal to date_end"
            )

        # Schedule the initialization.
        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
            "manual_mode": {
                "archive_id": archive_id,
                "date_start": date_start.timestamp(),
                "date_end": date_end.timestamp(),
            },
        }

        ctdeliveryjob = CTDeliveryJob(None, cls.class_job_type, metadata)
        # Configure retry policy for the underlying Job.
        ctdeliveryjob.job.max_retries = cls.max_retries

        store = IPrimaryStore(CTDeliveryJob)
        store.add(ctdeliveryjob)
        derived_job = cls(ctdeliveryjob)

        # Manual mode jobs can be slow if the archive is large.
        derived_job.task_queue = "launchpad_job_slow"
        derived_job.soft_time_limit = timedelta(minutes=15)
        derived_job.lease_duration = timedelta(minutes=15)

        derived_job.celeryRunOnCommit()
        IStore(CTDeliveryJob).flush()
        return derived_job

    @classmethod
    def iterReady(cls):
        """See `IJobSource`."""
        store = IPrimaryStore(CTDeliveryJob)
        jobs = store.find(
            CTDeliveryJob,
            And(
                CTDeliveryJob.job_type == cls.class_job_type,
                CTDeliveryJob.job_id.is_in(Job.ready_jobs),
            ),
        )
        return (cls(job) for job in jobs)

    @classmethod
    def get(cls, publishing_history):
        """See `ICTDeliveryDebJob`."""
        ctdelivery_job = (
            IStore(CTDeliveryJob)
            .find(
                CTDeliveryJob,
                CTDeliveryJob.job_id == Job.id,
                CTDeliveryJob.job_type == cls.class_job_type,
                CTDeliveryJob.publishing_history == publishing_history,
            )
            .one()
        )
        return None if ctdelivery_job is None else cls(ctdelivery_job)

    def __repr__(self):
        """Returns an informative representation of the job."""
        return (
            f"<{self.__class__.__name__} for "
            f"publishing_history: {self.publishing_history.id}, "
            f"metadata: {self.metadata}>"
        )

    def run(self):
        """See `IRunnableJob`."""
        if not self._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag %s; skipping.",
                CT_DELIVERY_ENABLED,
            )
            return

        manual_mode = self.metadata.get("manual_mode")

        if manual_mode:
            # Manual mode: process date range for an archive
            self._run_manual_mode(manual_mode)
        else:
            # Single publishing history mode
            self._run_publishing_mode()

    def _run_publishing_mode(self):
        """Run in single publishing history mode."""
        if self.publishing_history is None:
            logger.warning(
                "Publishing history %s not found; skipping job",
                self.context.publishing_history_id,
            )
            return

        archive = self.publishing_history.archive
        distribution_name = archive.distribution.name
        current_run = self.publishing_history.publisher_run
        archive_reference = (
            "primary"
            if archive.purpose == ArchivePurpose.PRIMARY
            else archive.reference
        )

        curr_finished = current_run.date_finished
        if curr_finished is None:
            # If `curr_finished` is None, we can just use `now()`.
            # A job gets created with the last transaction in the publisher
            # for that archive so the xpph are all set for that archive.
            curr_finished = datetime.now(timezone.utc)

        lookback_start = datetime.now(timezone.utc) - timedelta(days=60)

        prev_row = self._find_previous_run(
            archive_id=archive.id, before_ts=curr_finished
        )
        if prev_row is None:
            # First run for this archive: fall back to the lookback window so
            # initial publishes are still delivered to CT.
            prev_run_id, prev_finished = None, lookback_start
            logger.info(
                (
                    "No previous successful run found for archive %s; "
                    "run=%s. Using lookback window starting %s."
                ),
                archive.id,
                current_run.id,
                lookback_start,
            )
        else:
            prev_run_id, prev_finished = prev_row

        self._deliver_to_ct(
            archive=archive,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            prev_finished=prev_finished,
            curr_finished=curr_finished,
            lookback_start=lookback_start,
            prev_run_id=prev_run_id,
            current_run_id=current_run.id if current_run else None,
        )

    def _run_manual_mode(self, manual_mode_params):
        """Run in manual mode for initial population or backfilling."""
        archive_id = int(manual_mode_params["archive_id"])
        date_start = datetime.fromtimestamp(manual_mode_params["date_start"])
        date_end = datetime.fromtimestamp(manual_mode_params["date_end"])
        lookback_start = date_start - timedelta(days=60)

        # Fetch archive
        archive = getUtility(IArchiveSet).get(archive_id)
        if archive is None:
            logger.warning("Archive %s not found; skipping job", archive_id)
            return

        distribution_name = archive.distribution.name
        archive_reference = (
            "primary"
            if archive.purpose == ArchivePurpose.PRIMARY
            else archive.reference
        )

        logger.info(
            (
                "CTDeliveryDebJob manual mode: archive=%s "
                "date_start=%s date_end=%s"
            ),
            archive_id,
            date_start,
            date_end,
        )

        self._deliver_to_ct(
            archive=archive,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            prev_finished=date_start,
            curr_finished=date_end,
            lookback_start=lookback_start,
            prev_run_id=None,
            current_run_id=None,
        )

    def _deliver_to_ct(
        self,
        archive,
        distribution_name,
        archive_reference,
        prev_finished,
        curr_finished,
        lookback_start,
        prev_run_id,
        current_run_id,
    ):
        """Common processing and delivery logic for both modes."""
        store = IStore(ArchivePublisherRun)

        # Fetch BPPH/SPPH rows in the window.
        bpph_rows = self._query_bpph_rows(
            store=store,
            archive=archive,
            prev_finished=prev_finished,
            curr_finished=curr_finished,
            lookback_start=lookback_start,
        )
        spph_rows = self._query_spph_rows(
            store=store,
            archive=archive,
            prev_finished=prev_finished,
            curr_finished=curr_finished,
            lookback_start=lookback_start,
        )

        payloads, bpph_ids, spph_ids = self._build_payloads(
            bpph_rows=bpph_rows,
            spph_rows=spph_rows,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            curr_finished=curr_finished,
        )

        # Persist a light summary in metadata (keep payloads out).
        metadata = self.metadata
        metadata.setdefault("result", {})
        metadata["result"]["bpph"] = bpph_ids
        metadata["result"]["spph"] = spph_ids

        # Deliver to Commitment Tracker if configured/enabled.
        if not payloads:
            logger.info("[CT] no payloads to deliver for this window.")
            return

        client = get_commitment_tracker_client()
        success_count, failure_errors = client.send_payloads_with_results(
            payloads
        )
        metadata["result"]["ct_success_count"] = success_count
        metadata["result"]["ct_failure_count"] = len(failure_errors)
        metadata["result"].setdefault("error_description", []).extend(
            failure_errors
        )

        logger.info(
            (
                "CTDeliveryDebJob window: archive=%s prev_run=%s(%s) "
                "curr_run=%s(%s) binaries=%d sources=%d"
            ),
            archive.id,
            prev_run_id,
            prev_finished,
            current_run_id,
            curr_finished,
            len(bpph_rows),
            len(spph_rows),
        )

    def notifyUserError(self, error):
        """Calls up and also saves the error text in this job's metadata.

        See `BaseRunnableJob`.
        """
        # This method is called when error is an instance of
        # self.user_error_types.
        super().notifyUserError(error)
        logger.error(error)
        error_description = self.metadata.get("result").get(
            "error_description", []
        )
        error_description.append(str(error))
        self.metadata["result"]["error_description"] = error_description

    def getOopsVars(self):
        """See `IRunnableJob`."""
        vars = super().getOopsVars()
        vars.extend(
            [
                ("ctdeliveryjob_job_id", self.context.id),
                ("ctdeliveryjob_job_type", self.context.job_type.title),
                ("publishing_history", self.context.publishing_history),
            ]
        )
        return vars

    def _find_previous_run(self, archive_id, before_ts):
        """Find previous successful run for this archive before a timestamp."""
        apr = Alias(Table("ArchivePublisherRun"), "apr")
        aph = Alias(Table("ArchivePublishingHistory"), "aph")
        tables = Join(
            aph, apr, on=Eq(Column("publisher_run", aph), Column("id", apr))
        )
        where = And(
            Eq(Column("archive", aph), archive_id),
            Eq(
                Column("status", apr),
                ArchivePublisherRunStatus.SUCCEEDED.value,
            ),
            Lt(Column("date_finished", apr), before_ts),
            Ne(Column("date_finished", apr), None),
        )
        select = Select(
            columns=[Column("id", apr), Column("date_finished", apr)],
            tables=tables,
            where=where,
            order_by=[SQL("apr.date_finished DESC")],
            limit=1,
        )
        row = IStore(ArchivePublisherRun).execute(select).get_one()
        return None if row is None else row

    def _query_bpph_rows(
        self, store, archive, prev_finished, curr_finished, lookback_start
    ):
        # Window is (prev_finished, curr_finished]
        bpph = Alias(Table("binarypackagepublishinghistory"), "bpph")
        bpr = Alias(Table("binarypackagerelease"), "bpr")
        bpn = Alias(Table("binarypackagename"), "bpn")
        das = Alias(Table("distroarchseries"), "das")
        ds = Alias(Table("distroseries"), "ds")
        archive_tbl = Alias(Table("archive"), "archive_tbl")
        component_tbl = Alias(Table("component"), "component_tbl")
        bpf = Alias(Table("binarypackagefile"), "bpf")
        lfa = Alias(Table("libraryfilealias"), "lfa")
        lfc = Alias(Table("libraryfilecontent"), "lfc")
        spn_src = Alias(Table("sourcepackagename"), "spn_src")
        bpb = Alias(Table("binarypackagebuild"), "bpb")
        spr_src = Alias(Table("sourcepackagerelease"), "spr_src")

        bpph_tables = Join(
            bpph,
            bpr,
            on=Eq(Column("binarypackagerelease", bpph), Column("id", bpr)),
        )
        bpph_tables = Join(
            bpph_tables,
            bpn,
            on=Eq(Column("binarypackagename", bpr), Column("id", bpn)),
        )
        bpph_tables = Join(
            bpph_tables,
            das,
            on=Eq(Column("distroarchseries", bpph), Column("id", das)),
        )
        bpph_tables = Join(
            bpph_tables,
            ds,
            on=Eq(Column("distroseries", das), Column("id", ds)),
        )
        bpph_tables = Join(
            bpph_tables,
            archive_tbl,
            on=Eq(Column("archive", bpph), Column("id", archive_tbl)),
        )
        bpph_tables = Join(
            bpph_tables,
            component_tbl,
            on=Eq(Column("component", bpph), Column("id", component_tbl)),
        )
        bpph_tables = Join(
            bpph_tables,
            bpf,
            on=Eq(
                Column("binarypackagerelease", bpph),
                Column("binarypackagerelease", bpf),
            ),
        )
        bpph_tables = Join(
            bpph_tables,
            lfa,
            on=Eq(Column("libraryfile", bpf), Column("id", lfa)),
        )
        bpph_tables = Join(
            bpph_tables, lfc, on=Eq(Column("content", lfa), Column("id", lfc))
        )
        bpph_tables = LeftJoin(
            bpph_tables,
            spn_src,
            on=Eq(Column("sourcepackagename", bpph), Column("id", spn_src)),
        )
        bpph_tables = LeftJoin(
            bpph_tables, bpb, on=Eq(Column("build", bpr), Column("id", bpb))
        )
        bpph_tables = LeftJoin(
            bpph_tables,
            spr_src,
            on=Eq(
                Column("source_package_release", bpb), Column("id", spr_src)
            ),
        )

        bpph_where = And(
            Eq(Column("archive", bpph), archive.id),
            Eq(
                Column("status", bpph), PackagePublishingStatus.PUBLISHED.value
            ),
            Gt(Column("datecreated", bpph), lookback_start),
            Le(Column("datecreated", bpph), curr_finished),
            Gt(Column("datepublished", bpph), prev_finished),
            Le(Column("datepublished", bpph), curr_finished),
        )

        arch_agg = SQL(
            "string_agg(DISTINCT das.architecturetag, ', ' "
            "ORDER BY das.architecturetag)"
        )

        bpph_select = Select(
            columns=[
                Column("name", bpn),  # package_name
                Column("name", component_tbl),  # component
                Column("pocket", bpph),  # pocket
                arch_agg,  # architectures
                Column("name", ds),  # distroseries
                Column("version", bpr),  # version
                Column("id", bpb),  # build id as artifact_id
                Column("name", spn_src),  # sourcepackagename
                Column("version", spr_src),  # sourcepackageversion
                Column("sha256", lfc),  # sha256
                Column("id", bpph),  # bpph id
            ],
            tables=bpph_tables,
            where=bpph_where,
            group_by=[
                Column("id", bpn),
                Column("id", component_tbl),
                Column("pocket", bpph),
                Column("id", ds),
                Column("id", bpr),
                Column("id", bpb),
                Column("id", spn_src),
                Column("id", spr_src),
                Column("id", lfc),
                Column("id", bpph),
            ],
        )
        return store.execute(bpph_select).get_all()

    def _query_spph_rows(
        self, store, archive, prev_finished, curr_finished, lookback_start
    ):
        # SPPH aggregation in window.
        spph = Alias(Table("sourcepackagepublishinghistory"), "spph")
        spr = Alias(Table("sourcepackagerelease"), "spr")
        spn = Alias(Table("sourcepackagename"), "spn")
        archive_tbl_s = Alias(Table("archive"), "archive_s")
        component_tbl_s = Alias(Table("component"), "component_s")
        ds_s = Alias(Table("distroseries"), "ds_s")
        sprf = Alias(Table("sourcepackagereleasefile"), "sprf")
        lfa_s = Alias(Table("libraryfilealias"), "lfa_s")
        lfc_s = Alias(Table("libraryfilecontent"), "lfc_s")

        spph_tables = Join(
            spph,
            spr,
            on=Eq(Column("sourcepackagerelease", spph), Column("id", spr)),
        )
        spph_tables = Join(
            spph_tables,
            spn,
            on=Eq(Column("sourcepackagename", spr), Column("id", spn)),
        )
        spph_tables = Join(
            spph_tables,
            archive_tbl_s,
            on=Eq(Column("archive", spph), Column("id", archive_tbl_s)),
        )
        spph_tables = Join(
            spph_tables,
            component_tbl_s,
            on=Eq(Column("component", spph), Column("id", component_tbl_s)),
        )
        spph_tables = Join(
            spph_tables,
            ds_s,
            on=Eq(Column("distroseries", spph), Column("id", ds_s)),
        )
        spph_tables = Join(
            spph_tables,
            sprf,
            on=Eq(
                Column("sourcepackagerelease", spph),
                Column("sourcepackagerelease", sprf),
            ),
        )
        spph_tables = Join(
            spph_tables,
            lfa_s,
            on=Eq(Column("libraryfile", sprf), Column("id", lfa_s)),
        )
        spph_tables = Join(
            spph_tables,
            lfc_s,
            on=Eq(Column("content", lfa_s), Column("id", lfc_s)),
        )

        spph_where = And(
            Eq(Column("archive", spph), archive.id),
            Eq(
                Column("status", spph), PackagePublishingStatus.PUBLISHED.value
            ),
            Gt(Column("datecreated", spph), lookback_start),
            Le(Column("datecreated", spph), curr_finished),
            Gt(Column("datepublished", spph), prev_finished),
            Le(Column("datepublished", spph), curr_finished),
        )

        spph_select = Select(
            columns=[
                Column("name", spn),  # package_name
                Column("name", component_tbl_s),  # component
                Column("pocket", spph),  # pocket
                Column("name", ds_s),  # distroseries
                Column("version", spr),  # version
                Column("sha256", lfc_s),  # sha256
                Column("id", spph),  # spph id
            ],
            tables=spph_tables,
            where=spph_where,
            group_by=[
                Column("id", spn),
                Column("id", component_tbl_s),
                Column("pocket", spph),
                Column("id", ds_s),
                Column("id", spr),
                Column("id", lfc_s),
                Column("id", spph),
            ],
        )
        return store.execute(spph_select).get_all()

    def _build_payloads(
        self,
        bpph_rows,
        spph_rows,
        distribution_name,
        archive_reference,
        curr_finished,
    ):
        released_at = curr_finished.isoformat() if curr_finished else None

        binary_payloads = []
        bpph_ids = []
        for row in bpph_rows:
            (
                package_name,
                component,
                pocket,
                architectures_csv,
                distroseries_name,
                version,
                build_id,
                sourcepackagename,
                sourcepackageversion,
                sha256,
                bpph_id,
            ) = row
            bpph_ids.append(bpph_id)
            architectures = (
                [a.strip() for a in architectures_csv.split(",")]
                if architectures_csv
                else []
            )
            payload = {
                "release": {
                    "released_at": released_at,
                    "external_link": None,
                    "properties": {
                        "type": "deb",
                        "id": str(build_id),
                        "name": package_name,
                        "architectures": architectures,
                        "version": version,
                        "sha256": sha256,
                        "archive_base": distribution_name,
                        "archive_reference": archive_reference,
                        "archive_series": distroseries_name,
                        "archive_pocket": POCKET_TO_NAME.get(pocket),
                        "archive_component": component,
                    },
                },
            }
            if sourcepackagename:
                payload["release"]["properties"][
                    "source_package_name"
                ] = sourcepackagename
            if sourcepackageversion:
                payload["release"]["properties"][
                    "source_package_version"
                ] = sourcepackageversion
            binary_payloads.append(payload)

        source_payloads = []
        spph_ids = []
        for row in spph_rows:
            (
                package_name,
                component,
                pocket,
                distroseries_name,
                version,
                sha256,
                spph_id,
            ) = row
            spph_ids.append(spph_id)
            payload = {
                "release": {
                    "released_at": released_at,
                    "external_link": None,
                    "properties": {
                        "type": "deb-source",
                        "name": package_name,
                        "architectures": [],
                        "sha256": sha256,
                        "archive_base": distribution_name,
                        "archive_reference": archive_reference,
                        "archive_series": distroseries_name,
                        "archive_pocket": POCKET_TO_NAME.get(pocket),
                        "archive_component": component,
                    },
                },
            }
            source_payloads.append(payload)

        payloads = binary_payloads + source_payloads

        return payloads, bpph_ids, spph_ids
