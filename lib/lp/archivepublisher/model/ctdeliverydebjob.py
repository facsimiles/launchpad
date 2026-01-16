# Copyright 2025 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

__all__ = ["CTDeliveryDebJob"]

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

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
CT_DELIVERY_MANUAL_TIMEOUT = (
    "commitment_tracker.delivery.manual_timeout_minutes"
)

POCKET_TO_NAME = {
    item.value: (
        "release" if (_suffix := pocketsuffix[item]) == "" else _suffix[1:]
    )
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

    @staticmethod
    def _get_manual_timeout_minutes():
        """Return the timeout in minutes for manual mode jobs.

        Defaults to 30 minutes if not configured via feature flag.
        """
        timeout_str = getFeatureFlag(CT_DELIVERY_MANUAL_TIMEOUT)
        if timeout_str:
            try:
                return int(timeout_str)
            except (ValueError, TypeError):
                logger.warning(
                    f"[CT] Invalid value for {CT_DELIVERY_MANUAL_TIMEOUT}: "
                    f"{timeout_str}, using default 30"
                )
        return 30

    @property
    def publishing_history(self):
        # Prefer the Storm-loaded reference on the context; fall back to an
        # explicit fetch by id if not already loaded.
        if getattr(self.context, "publishing_history", None) is not None:
            return self.context.publishing_history
        if self.context.publishing_history_id is not None:
            return IStore(ArchivePublishingHistory).get(
                self.context.publishing_history_id
            )
        return None

    @property
    def error_description(self):
        return self.metadata.get("result", {}).get("error_description", [])

    @property
    def metadata(self):
        return self.context.metadata

    @classmethod
    def create(
        cls, publishing_history_id: int
    ) -> Optional["CTDeliveryDebJob"]:
        """Create a new `CTDeliveryDebJob` using `IArchivePublishingHistory`.

        :param publishing_history_id: The id of the
            `IArchivePublishingHistory` associated with this job.
        """
        if not cls._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag "
                f"{CT_DELIVERY_ENABLED}"
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
    def create_manual(
        cls,
        archive_id: int,
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None,
        distroseries: Optional[int] = None,
        status: int = PackagePublishingStatus.PUBLISHED.value,
    ) -> Optional["CTDeliveryDebJob"]:
        """Create a new `CTDeliveryDebJob` manually.

        :param archive_id: The id of the archive to process.
        :param date_start: Start of the date range.
        :param date_end: End of the date range.
        :param distroseries: The id of the distroseries to filter.
        :param status: The publishing status to filter by.
        """
        if not cls._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag "
                f"{CT_DELIVERY_ENABLED}"
            )
            return None

        if archive_id is None:
            raise ValueError("archive_id is required")

        if date_start and date_end and date_start > date_end:
            raise ValueError(
                "date_start must be less than or equal to date_end"
            )

        manual_mode = {
            "archive_id": archive_id,
            "status": status,
            "date_start": date_start.timestamp() if date_start else None,
            "date_end": date_end.timestamp() if date_end else None,
            "distroseries": distroseries,
        }

        metadata = {
            "result": {
                "error_description": [],
                "bpph": [],
                "spph": [],
                "ct_success_count": 0,
                "ct_failure_count": 0,
            },
            "manual_mode": manual_mode,
        }

        ctdeliveryjob = CTDeliveryJob(None, cls.class_job_type, metadata)
        # Configure retry policy for the underlying Job.
        ctdeliveryjob.job.max_retries = cls.max_retries

        store = IPrimaryStore(CTDeliveryJob)
        store.add(ctdeliveryjob)
        derived_job = cls(ctdeliveryjob)

        # Manual mode jobs can be slow if the archive is large.
        derived_job.task_queue = "launchpad_job_slow"
        # Configure time limits from feature flag
        timeout_minutes = cls._get_manual_timeout_minutes()
        derived_job.soft_time_limit = timedelta(minutes=timeout_minutes)
        derived_job.lease_duration = timedelta(minutes=timeout_minutes)

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
    def get(cls, publishing_history) -> Optional["CTDeliveryDebJob"]:
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

    def __repr__(self) -> str:
        """Returns an informative representation of the job."""
        return (
            f"<{self.__class__.__name__} for "
            f"publishing_history: {self.publishing_history.id}, "
            f"metadata: {self.metadata}>"
        )

    def run(self) -> None:
        """See `IRunnableJob`."""
        if not self._is_delivery_enabled():
            logger.info(
                "[CT] Delivery disabled via feature flag "
                f"{CT_DELIVERY_ENABLED}; skipping."
            )
            return

        manual_mode = self.metadata.get("manual_mode")

        if manual_mode:
            # Manual mode: process date range for an archive
            self._run_manual_mode(manual_mode)
        else:
            # Single publishing history mode
            self._run_publishing_mode()

    def _run_publishing_mode(self) -> None:
        """Run in single publishing history mode."""
        if self.publishing_history is None:
            logger.warning(
                f"Publishing history {self.context.publishing_history_id} not "
                "found; skipping job"
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
                f"No previous successful run found for archive {archive.id}; "
                f"run={current_run.id}. Using lookback window starting "
                f"{lookback_start}."
            )
        else:
            prev_run_id, prev_finished = prev_row

        self._deliver_to_ct(
            archive=archive,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            datecreated_start=lookback_start,
            datecreated_end=curr_finished,
            datepublished_start=prev_finished,
            datepublished_end=curr_finished,
            prev_run_id=prev_run_id,
            current_run_id=current_run.id if current_run else None,
            distroseries=None,
        )

    def _run_manual_mode(self, manual_mode_params: dict) -> None:
        """Run in manual mode for initial population or backfilling."""
        archive_id = int(manual_mode_params["archive_id"])
        date_start = manual_mode_params.get("date_start")
        date_end = manual_mode_params.get("date_end")
        distroseries = manual_mode_params.get("distroseries")
        status_raw = manual_mode_params.get("status")
        status = (
            int(status_raw)
            if status_raw is not None
            else PackagePublishingStatus.PUBLISHED.value
        )

        lookback_start = None
        if date_start is not None:
            date_start = datetime.fromtimestamp(date_start, tz=timezone.utc)
            lookback_start = date_start - timedelta(days=60)
        if date_end is not None:
            date_end = datetime.fromtimestamp(date_end, tz=timezone.utc)

        # Fetch archive
        archive = getUtility(IArchiveSet).get(archive_id)
        if archive is None:
            logger.warning(f"Archive {archive_id} not found; skipping job")
            return

        distribution_name = archive.distribution.name
        archive_reference = (
            "primary"
            if archive.purpose == ArchivePurpose.PRIMARY
            else archive.reference
        )

        logger.info(
            f"CTDeliveryDebJob manual mode: archive={archive_id} "
            f"date_start={date_start} date_end={date_end} "
            f"distroseries={distroseries}"
        )

        self._deliver_to_ct(
            archive=archive,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            datecreated_start=lookback_start,
            datecreated_end=date_end,
            datepublished_start=date_start,
            datepublished_end=date_end,
            prev_run_id=None,
            current_run_id=None,
            distroseries=distroseries,
            status=status,
        )

    def _deliver_to_ct(
        self,
        archive,
        distribution_name: str,
        archive_reference: str,
        datecreated_start: Optional[datetime],
        datecreated_end: Optional[datetime],
        datepublished_start: Optional[datetime],
        datepublished_end: Optional[datetime],
        prev_run_id: Optional[int],
        current_run_id: Optional[int],
        distroseries: Optional[int],
        status: int = PackagePublishingStatus.PUBLISHED.value,
    ) -> None:
        """Common processing and delivery logic for both modes."""
        logger.debug(
            f"CTDeliveryDebJob for archive={archive.reference} "
            f"datecreated_start={datecreated_start} "
            f"datecreated_end={datecreated_end} "
            f"datepublished_start={datepublished_start} "
            f"datepublished_end={datepublished_end} "
            f"distroseries={distroseries} status={status}"
        )

        store = IStore(ArchivePublisherRun)

        # Fetch BPPH/SPPH rows in the window.
        logger.info(f"Querying BPPH rows for archive {archive.reference}")
        bpph_rows = self._query_bpph_rows(
            store=store,
            archive=archive,
            datecreated_start=datecreated_start,
            datecreated_end=datecreated_end,
            datepublished_start=datepublished_start,
            datepublished_end=datepublished_end,
            distroseries=distroseries,
            status=status,
        )

        logger.info(f"Querying SPPH rows for archive {archive.reference}")
        spph_rows = self._query_spph_rows(
            store=store,
            archive=archive,
            datecreated_start=datecreated_start,
            datecreated_end=datecreated_end,
            datepublished_start=datepublished_start,
            datepublished_end=datepublished_end,
            distroseries=distroseries,
            status=status,
        )

        logger.info(
            f"Building payloads for CT delivery: binaries={len(bpph_rows)} "
            f"sources={len(spph_rows)}"
        )
        payloads, bpph_ids, spph_ids = self._build_payloads(
            bpph_rows=bpph_rows,
            spph_rows=spph_rows,
            distribution_name=distribution_name,
            archive_reference=archive_reference,
            curr_finished=datepublished_end,
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

        logger.info(f"Sending {len(payloads)} payloads to CT")
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
            f"CTDeliveryDebJob window: archive={archive.id} "
            f"prev_run={prev_run_id}({datepublished_start}) "
            f"curr_run={current_run_id}({datepublished_end}) "
            f"binaries={len(bpph_rows)} sources={len(spph_rows)}"
        )

    def notifyUserError(self, error) -> None:
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

    def getOopsVars(self) -> List[Tuple]:
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

    def _find_previous_run(
        self, archive_id: int, before_ts: datetime
    ) -> Optional[Tuple]:
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
        self,
        store,
        archive,
        datecreated_start: Optional[datetime],
        datecreated_end: Optional[datetime],
        datepublished_start: Optional[datetime],
        datepublished_end: Optional[datetime],
        distroseries: Optional[int],
        status: int,
    ) -> List[Tuple]:
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

        bpph_where_clauses = [
            Eq(Column("archive", bpph), archive.id),
            Eq(Column("status", bpph), status),
        ]
        if datecreated_start is not None:
            bpph_where_clauses.append(
                Gt(Column("datecreated", bpph), datecreated_start)
            )
        if datecreated_end is not None:
            bpph_where_clauses.append(
                Le(Column("datecreated", bpph), datecreated_end)
            )
        if datepublished_start is not None:
            bpph_where_clauses.append(
                Gt(Column("datepublished", bpph), datepublished_start)
            )
        if datepublished_end is not None:
            bpph_where_clauses.append(
                Le(Column("datepublished", bpph), datepublished_end)
            )
        if distroseries:
            bpph_where_clauses.append(Eq(Column("id", ds), distroseries))
        bpph_where = And(*bpph_where_clauses)

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
        self,
        store,
        archive,
        datecreated_start: Optional[datetime],
        datecreated_end: Optional[datetime],
        datepublished_start: Optional[datetime],
        datepublished_end: Optional[datetime],
        distroseries: Optional[int],
        status: int,
    ) -> List[Tuple]:
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

        spph_where_clauses = [
            Eq(Column("archive", spph), archive.id),
            Eq(Column("status", spph), status),
        ]
        if datecreated_start is not None:
            spph_where_clauses.append(
                Gt(Column("datecreated", spph), datecreated_start)
            )
        if datecreated_end is not None:
            spph_where_clauses.append(
                Le(Column("datecreated", spph), datecreated_end)
            )
        if datepublished_start is not None:
            spph_where_clauses.append(
                Gt(Column("datepublished", spph), datepublished_start)
            )
        if datepublished_end is not None:
            spph_where_clauses.append(
                Le(Column("datepublished", spph), datepublished_end)
            )
        if distroseries is not None:
            spph_where_clauses.append(Eq(Column("id", ds_s), distroseries))
        spph_where = And(*spph_where_clauses)

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
        bpph_rows: List[Tuple],
        spph_rows: List[Tuple],
        distribution_name: str,
        archive_reference: str,
        curr_finished: Optional[datetime],
    ) -> Tuple[List[dict], List[int], List[int]]:
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
            binary_payload: Dict[str, Any] = {
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
                binary_payload["release"]["properties"][
                    "source_package_name"
                ] = sourcepackagename
            if sourcepackageversion:
                binary_payload["release"]["properties"][
                    "source_package_version"
                ] = sourcepackageversion
            binary_payloads.append(binary_payload)

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
            source_payload: Dict[str, Any] = {
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
            source_payloads.append(source_payload)

        payloads = binary_payloads + source_payloads

        return payloads, bpph_ids, spph_ids
