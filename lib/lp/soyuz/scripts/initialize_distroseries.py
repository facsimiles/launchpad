# Copyright 2009-2011 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Initialize a distroseries from its parent distroseries."""


__metaclass__ = type
__all__ = [
    'InitializationError',
    'InitializeDistroSeries',
    ]

from operator import methodcaller

import transaction
from zope.component import getUtility

from canonical.database.sqlbase import sqlvalues
from canonical.launchpad.helpers import ensure_unicode
from canonical.launchpad.interfaces.lpstorm import IMasterStore
from lp.app.errors import NotFoundError
from lp.buildmaster.enums import BuildStatus
from lp.registry.interfaces.distroseriesparent import IDistroSeriesParentSet
from lp.registry.interfaces.pocket import PackagePublishingPocket
from lp.services.database import bulk
from lp.soyuz.adapters.packagelocation import PackageLocation
from lp.soyuz.enums import (
    ArchivePurpose,
    PackagePublishingStatus,
    PackageUploadStatus,
    )
from lp.soyuz.interfaces.archive import (
    CannotCopy,
    IArchiveSet,
    )
from lp.soyuz.interfaces.component import IComponentSet
from lp.soyuz.interfaces.distributionjob import (
    IDistroSeriesDifferenceJobSource,
    )
from lp.soyuz.interfaces.packagecloner import IPackageCloner
from lp.soyuz.interfaces.packageset import (
    IPackagesetSet,
    NoSuchPackageSet,
    )
from lp.soyuz.interfaces.queue import IPackageUploadSet
from lp.soyuz.model.packageset import Packageset
from lp.soyuz.scripts.packagecopier import do_copy


class InitializationError(Exception):
    """Raised when there is an exception during the initialization process."""

# Pockets to consider when initializing the derived series from its parent(s).
INIT_POCKETS = [
    PackagePublishingPocket.RELEASE,
    PackagePublishingPocket.SECURITY,
    PackagePublishingPocket.UPDATES,
    ]


class InitializeDistroSeries:
    """Copy in all of the parents distroseries's configuration. This
    includes all configuration for distroseries as well as distroarchseries,
    publishing and all publishing records for sources and binaries.

    We support 2 use cases here:
      #1 If the child distribution has zero initialized series:
        - the parent list can't be empty (otherwise we trigger an error);
        - the series will be derived from the parents passed as argument;
        - the parents will be set to the parents passed as argument;
        - first_derivation = True.
      #2 If the child distribution has more than zero initialized series:
        - the series will be derived from the previous_series;
        - the parents will be set to the parents passed as argument or
          the parents of the previous_series if the passed argument is empty;
        - first_derivation = False.

    Preconditions:
      The distroseries must exist, and be completly unused, with no source
      or binary packages existing, as well as no distroarchseries set up.
      Section and component selections must be empty. It must not have any
      parent series.

    Outcome:
      The distroarchseries set up in the parent series will be copied.
      The publishing structure will be copied from the parents. All
      PUBLISHED and PENDING packages in the parents will be created in
      this distroseries and its distroarchseriess. All component and section
      selections will be duplicated, as will any permission-related
      structures.

    Note:
      This method will raise a InitializationError when the pre-conditions
      are not met. After this is run, you still need to construct chroots
      for building, you need to add anything missing wrt. ports etc. This
      method is only meant to give you a basic copy of parent series in
      order to assist you in preparing a new series of a distribution or
      in the initialization of a derivative.
    """

    def __init__(
        self, distroseries, parents=(), arches=(), packagesets=(),
        rebuild=False, overlays=(), overlay_pockets=(),
        overlay_components=()):
        # Avoid circular imports
        from lp.registry.model.distroseries import DistroSeries

        self.distroseries = distroseries
        self.parent_ids = [int(id) for id in parents]
        # Load parent objects in bulk...
        parents_bulk = bulk.load(DistroSeries, self.parent_ids)
        # ... sort the parents to match the order in the 'parents' parameter.
        self.parents = sorted(
            parents_bulk,
            key=lambda parent: self.parent_ids.index(parent.id))
        self.arches = arches
        self.packagesets_ids = [
            ensure_unicode(packageset) for packageset in packagesets]
        self.packagesets = bulk.load(
            Packageset, [int(packageset) for packageset in packagesets])
        self.rebuild = rebuild
        self.overlays = overlays
        self.overlay_pockets = overlay_pockets
        self.overlay_components = overlay_components
        self._store = IMasterStore(DistroSeries)

        self.first_derivation = (
            not self.distroseries.distribution.has_published_sources)

        if self.first_derivation:
            # Use-case #1.
            self.derivation_parents = self.parents
            self.derivation_parent_ids = self.parent_ids
        else:
            # Use-case #2.
            self.derivation_parents = [self.distroseries.previous_series]
            self.derivation_parent_ids = [
                p.id for p in self.derivation_parents if p is not None]
            if self.parent_ids == []:
                self.parents = (
                    self.distroseries.previous_series.getParentSeries())
        self._create_source_names_by_parent()

    def check(self):
        if self.distroseries.isDerivedSeries():
            raise InitializationError(
                ("DistroSeries {child.name} has already been initialized"
                 ".").format(
                    child=self.distroseries))
        if (self.distroseries.distribution.has_published_sources and
            self.distroseries.previous_series is None):
            raise InitializationError(
                ("DistroSeries {child.name} has no previous series and "
                 "the distribution already has initialized series"
                 ".").format(
                    child=self.distroseries))
        self._checkParents()
        for parent in self.derivation_parents:
            if self.distroseries.distribution.id == parent.distribution.id:
                self._checkBuilds(parent)
            self._checkQueue(parent)
        self._checkSeries()
        return True

    def _checkParents(self):
        """If self.first_derivation, the parents list cannot be empty."""
        if self.first_derivation:
            # Use-case #1.
            if len(self.parent_ids) == 0:
                raise InitializationError(
                    ("Distroseries {child.name} cannot be initialized: "
                     "No other series in the distribution is initialized "
                     "and no parent was passed to the initilization method"
                     ".").format(
                        child=self.distroseries))

    def _checkBuilds(self, parent):
        """Assert there are no pending builds for the given parent series.

        Only cares about the RELEASE, SECURITY and UPDATES pockets, which are
        the only ones inherited via initializeFromParent method.
        Restrict the check to the select architectures (if applicable).
        Restrict the check to the selected packages if a limited set of
        packagesets is used by the initialization.
        """
        spns = self.source_names_by_parent.get(parent, None)
        if spns is not None and len(spns) == 0:
            # If no sources are selected in this parent, skip the check.
            return
        # spns=None means no packagesets selected so we need to consider
        # all sources.

        arch_tags = self.arches if self.arches is not () else None
        pending_builds = parent.getBuildRecords(
            BuildStatus.NEEDSBUILD, pocket=INIT_POCKETS,
            arch_tag=arch_tags, name=spns)

        if not pending_builds.is_empty():
            raise InitializationError(
                "Parent series has pending builds for selected sources, "
                "see help text for more information.")

    def _checkQueue(self, parent):
        """Assert upload queue is empty on the given parent series.

        Only cares about the RELEASE, SECURITY and UPDATES pockets, which are
        the only ones inherited via initializeFromParent method.
        Restrict the check to the selected packages if a limited set of
        packagesets is used by the initialization.
         """
        statuses = [
            PackageUploadStatus.NEW,
            PackageUploadStatus.ACCEPTED,
            PackageUploadStatus.UNAPPROVED,
            ]
        spns = self.source_names_by_parent.get(parent, None)
        if spns is not None and len(spns) == 0:
            # If no sources are selected in this parent, skip the check.
            return
        # spns=None means no packagesets selected so we need to consider
        # all sources.

        items = getUtility(IPackageUploadSet).getBuildsForSources(
            parent, statuses, INIT_POCKETS, spns)
        if not items.is_empty():
            raise InitializationError(
                "Parent series has sources waiting in its upload queues "
                "that match your selection, see help text for more "
                "information.")

    def _checkSeries(self):
        error = (
            "Can not copy distroarchseries from parent, there are "
            "already distroarchseries(s) initialized for this series.")
        sources = self.distroseries.getAllPublishedSources()
        binaries = self.distroseries.getAllPublishedBinaries()
        if not all(
            map(methodcaller('is_empty'), (
                sources, binaries, self.distroseries.architectures,
                self.distroseries.sections))):
            raise InitializationError(error)
        if self.distroseries.components:
            raise InitializationError(error)

    def initialize(self):
        self._set_parents()
        self._copy_configuration()
        self._copy_architectures()
        self._copy_packages()
        self._copy_packagesets()
        self._create_dsds()
        self._set_initialized()
        transaction.commit()

    def _set_parents(self):
        count = 0
        for parent in self.parents:
            dsp_set = getUtility(IDistroSeriesParentSet)
            if self.overlays and self.overlays[count]:
                pocket = PackagePublishingPocket.__metaclass__.getTermByToken(
                    PackagePublishingPocket,
                    self.overlay_pockets[count]).value
                component_set = getUtility(IComponentSet)
                component = component_set[self.overlay_components[count]]
                dsp_set.new(
                    self.distroseries, parent, initialized=False,
                    is_overlay=True, pocket=pocket, component=component,
                    ordering=count)
            else:
                dsp_set.new(
                    self.distroseries, parent, initialized=False,
                    is_overlay=False, ordering=count)
            count += 1

    def _set_initialized(self):
        dsp_set = getUtility(IDistroSeriesParentSet)
        distroseriesparents = dsp_set.getByDerivedSeries(
            self.distroseries)
        for distroseriesparent in distroseriesparents:
            distroseriesparent.initialized = True

    def _has_same_parents_as_previous_series(self):
        # Does this distroseries have the same parents as its previous
        # series? (note that the parent's order does not matter here)
        dsp_set = getUtility(IDistroSeriesParentSet)
        previous_series_parents = [
            dsp.parent_series for dsp in dsp_set.getByDerivedSeries(
                self.distroseries.previous_series)]
        return set(previous_series_parents) == set(self.parents)

    def _create_dsds(self):
        if not self.first_derivation:
            if (self._has_same_parents_as_previous_series() and
                not self.packagesets_ids):
                # If the parents are the same as previous_series's
                # parents and all the packagesets are being copied,
                # then we simply copy the DSDs from previous_series
                # for performance reasons.
                self._copy_dsds_from_previous_series()
            else:
                # Either the parents have changed (compared to
                # previous_series's parents) or a selection only of the
                # packagesets is being copied so we have to recompute
                # the DSDs by creating DSD Jobs.
                self._create_dsd_jobs()
        else:
            # If this is the first derivation, create the DSD Jobs.
            self._create_dsd_jobs()

    def _copy_dsds_from_previous_series(self):
        self._store.execute("""
            INSERT INTO DistroSeriesDifference
                (derived_series, source_package_name, package_diff,
                status, difference_type, parent_package_diff,
                source_version, parent_source_version,
                base_version, parent_series)
            SELECT
                %s AS derived_series, source_package_name,
                package_diff, status,
                difference_type, parent_package_diff, source_version,
                parent_source_version, base_version, parent_series
            FROM DistroSeriesDifference AS dsd
                WHERE dsd.derived_series = %s
            """ % sqlvalues(
                self.distroseries.id,
                self.distroseries.previous_series.id))

    def _create_dsd_jobs(self):
        job_source = getUtility(IDistroSeriesDifferenceJobSource)
        job_source.massCreateForSeries(self.distroseries)

    def _copy_configuration(self):
        self.distroseries.backports_not_automatic = any(
            parent.backports_not_automatic
                for parent in self.derivation_parents)
        self.distroseries.include_long_descriptions = any(
            parent.include_long_descriptions
                for parent in self.derivation_parents)

    def _copy_architectures(self):
        das_filter = ' AND distroseries IN %s ' % (
                sqlvalues([p.id for p in self.derivation_parents]))
        if self.arches:
            das_filter += ' AND architecturetag IN %s ' % (
                sqlvalues(self.arches))
        self._store.execute("""
            INSERT INTO DistroArchSeries
            (distroseries, processorfamily, architecturetag, owner, official,
             supports_virtualized)
            SELECT %s, processorfamily, architecturetag, %s,
                bool_and(official), bool_or(supports_virtualized)
            FROM DistroArchSeries WHERE enabled = TRUE %s
            GROUP BY processorfamily, architecturetag
            """ % (sqlvalues(self.distroseries, self.distroseries.owner)
            + (das_filter, )))
        self._store.flush()
        # Take nominatedarchindep from the first parent.
        self.distroseries.nominatedarchindep = self.distroseries[
            self.derivation_parents[0].nominatedarchindep.architecturetag]

    def _copy_packages(self):
        # Perform the copies
        self._copy_component_section_and_format_selections()

        # Prepare the lists of distroarchseries for which binary packages
        # shall be copied.
        distroarchseries_lists = {}
        for parent in self.derivation_parents:
            distroarchseries_lists[parent] = []
            for arch in self.distroseries.architectures:
                if self.arches and (arch.architecturetag not in self.arches):
                    continue
                try:
                    parent_arch = parent.getDistroArchSeries(
                        arch.architecturetag)
                except NotFoundError:
                    continue

                distroarchseries_lists[parent].append((parent_arch, arch))
        # Now copy source and binary packages.
        self._copy_publishing_records(distroarchseries_lists)
        self._copy_packaging_links()

    def _use_cloner(self, target_archive, archive):
        """Returns True if it's safe to use the packagecloner (as opposed
        to using the packagecopier).
        We use two different ways to copy packages:
         - the packagecloner: fast but not conflict safe.
         - the packagecopier: slow but performs lots of checks to
         avoid creating conflicts.
        1. We'll use the cloner:
        If this is not a first initialization.
        And If:
            1.a If the archives are different and the target archive is
                empty use the cloner.
            Or
            1.b. If the archives are the same and the target series is
                empty use the cloner.
        2.  Otherwise use the copier.
        """
        if self.first_derivation:
            return False

        target_archive_empty = target_archive.getPublishedSources().is_empty()
        case_1a = (target_archive != archive and
                   target_archive_empty)
        case_1b = (target_archive == archive and
                   (target_archive_empty or
                    target_archive.getPublishedSources(
                        distroseries=self.distroseries).is_empty()))
        return case_1a or case_1b

    def _create_source_names_by_parent(self):
        """If only a subset of the packagesets was selected to be copied,
        create a dict with the list of source names to be copied for each
        parent.

        source_names_by_parent.get(parent) can be 3 different things:
        - None: this means that no specific packagesets where selected
        for the initialization. In this case we need to consider *all*
        the packages in this parent.
        - []: this means that some specific packagesets where selected
        for the initialization but none in this parent. We can skip
        this parent for all the copy/check operations.
        - [name1, ...]: this means that some specific packagesets
        were selected for the initialization and some are in this
        parent so the list of packages to consider in not empty.
        """
        source_names_by_parent = {}
        if self.packagesets_ids:
            for parent in self.derivation_parents:
                spns = []
                for pkgset in self.packagesets:
                    if pkgset.distroseries == parent:
                        spns += list(pkgset.getSourcesIncluded())
                source_names_by_parent[parent] = spns
        self.source_names_by_parent = source_names_by_parent

    def _copy_publishing_records(self, distroarchseries_lists):
        """Copy the publishing records from the parent arch series
        to the given arch series in ourselves.

        We copy all PENDING and PUBLISHED records as PENDING into our own
        publishing records.

        We copy only the RELEASE pocket in the PRIMARY and DEBUG archives.
        """
        archive_set = getUtility(IArchiveSet)

        for parent in self.derivation_parents:
            spns = self.source_names_by_parent.get(parent, None)
            if spns is not None and len(spns) == 0:
                # Some packagesets where selected but not a single
                # source from this parent: we skip the copy since
                # calling copy with spns=[] would copy all the packagesets
                # from this parent.
                continue
            # spns=None means no packagesets selected so we need to consider
            # all sources.

            distroarchseries_list = distroarchseries_lists[parent]
            for archive in parent.distribution.all_distro_archives:
                if archive.purpose not in (
                    ArchivePurpose.PRIMARY, ArchivePurpose.DEBUG):
                    continue

                target_archive = archive_set.getByDistroPurpose(
                    self.distroseries.distribution, archive.purpose)
                if archive.purpose is ArchivePurpose.PRIMARY:
                    assert target_archive is not None, (
                        "Target archive doesn't exist?")
                if self._use_cloner(target_archive, archive):
                    origin = PackageLocation(
                        archive, parent.distribution, parent,
                        PackagePublishingPocket.RELEASE)
                    destination = PackageLocation(
                        target_archive, self.distroseries.distribution,
                        self.distroseries, PackagePublishingPocket.RELEASE)
                    proc_families = None
                    if self.rebuild:
                        proc_families = [
                            das[1].processorfamily
                            for das in distroarchseries_list]
                        distroarchseries_list = ()
                    getUtility(IPackageCloner).clonePackages(
                        origin, destination, distroarchseries_list,
                        proc_families, spns, self.rebuild)
                else:
                    # There is only one available pocket in an unreleased
                    # series.
                    target_pocket = PackagePublishingPocket.RELEASE
                    sources = archive.getPublishedSources(
                        distroseries=parent, pocket=INIT_POCKETS,
                        status=(PackagePublishingStatus.PENDING,
                                PackagePublishingStatus.PUBLISHED),
                        name=spns)
                    # XXX: rvb 2011-06-23 bug=801112: do_copy is atomic (all
                    # or none of the sources will be copied). This might
                    # lead to a partially initialised series if there is a
                    # single conflict in the destination series.
                    try:
                        sources_published = do_copy(
                            sources, target_archive, self.distroseries,
                            target_pocket, include_binaries=not self.rebuild,
                            check_permissions=False, strict_binaries=False,
                            close_bugs=False, create_dsd_job=False)
                        if self.rebuild:
                            for pubrec in sources_published:
                                pubrec.createMissingBuilds(
                                   list(self.distroseries.architectures))
                    except CannotCopy, error:
                        raise InitializationError(error)

    def _copy_component_section_and_format_selections(self):
        """Copy the section, component and format selections from the parents
        distro series into this one.
        """
        # Copy the component selections
        self._store.execute('''
            INSERT INTO ComponentSelection (distroseries, component)
            SELECT DISTINCT %s AS distroseries, cs.component AS component
            FROM ComponentSelection AS cs WHERE cs.distroseries IN %s
            ''' % sqlvalues(self.distroseries.id,
            self.derivation_parent_ids))
        # Copy the section selections
        self._store.execute('''
            INSERT INTO SectionSelection (distroseries, section)
            SELECT DISTINCT %s as distroseries, ss.section AS section
            FROM SectionSelection AS ss WHERE ss.distroseries IN %s
            ''' % sqlvalues(self.distroseries.id,
            self.derivation_parent_ids))
        # Copy the source format selections
        self._store.execute('''
            INSERT INTO SourcePackageFormatSelection (distroseries, format)
            SELECT DISTINCT %s as distroseries, spfs.format AS format
            FROM SourcePackageFormatSelection AS spfs
            WHERE spfs.distroseries IN %s
            ''' % sqlvalues(self.distroseries.id,
            self.derivation_parent_ids))

    def _copy_packaging_links(self):
        """Copy the packaging links from the parent series to this one."""
        # We iterate over the parents and copy into the child in
        # sequence to avoid creating duplicates.
        for parent_id in self.derivation_parent_ids:
            self._store.execute("""
                INSERT INTO
                    Packaging(
                        distroseries, sourcepackagename, productseries,
                        packaging, owner)
                SELECT
                    ChildSeries.id,
                    Packaging.sourcepackagename,
                    Packaging.productseries,
                    Packaging.packaging,
                    Packaging.owner
                FROM
                    Packaging
                    -- Joining the parent distroseries permits the query to
                    -- build the data set for the series being updated, yet
                    -- results are in fact the data from the original series.
                    JOIN Distroseries ChildSeries
                        ON Packaging.distroseries = %s
                WHERE
                    -- Select only the packaging links that are in the parent
                    -- that are not in the child.
                    ChildSeries.id = %s
                    AND Packaging.sourcepackagename in (
                        SELECT sourcepackagename
                        FROM Packaging
                        WHERE distroseries in (
                            SELECT id
                            FROM Distroseries
                            WHERE id = %s
                            )
                        EXCEPT
                        SELECT sourcepackagename
                        FROM Packaging
                        WHERE distroseries in (
                            SELECT id
                            FROM Distroseries
                            WHERE id = ChildSeries.id
                            )
                        )
                """ % sqlvalues(
                    parent_id, self.distroseries.id, parent_id))

    def _copy_packagesets(self):
        """Copy packagesets from the parent distroseries."""
        # Avoid circular imports.
        from lp.registry.model.distroseries import DistroSeries

        packagesets = self._store.find(
            Packageset, DistroSeries.id.is_in(self.derivation_parent_ids))
        parent_to_child = {}
        # Create the packagesets and any archivepermissions if we're not
        # copying cross-distribution.
        parent_distro_ids = [
            parent.distribution.id for parent in self.derivation_parents]
        for parent_ps in packagesets:
            # Cross-distro initializations get packagesets owned by the
            # distro owner, otherwise the old owner is preserved.
            if (self.packagesets_ids and
                str(parent_ps.id) not in self.packagesets_ids):
                continue
            packageset_set = getUtility(IPackagesetSet)
            # First, try to fetch an existing packageset with this name.
            try:
                child_ps = packageset_set.getByName(
                    parent_ps.name, self.distroseries)
            except NoSuchPackageSet:
                if self.distroseries.distribution.id in parent_distro_ids:
                    new_owner = parent_ps.owner
                else:
                    new_owner = self.distroseries.owner
                child_ps = getUtility(IPackagesetSet).new(
                    parent_ps.name, parent_ps.description,
                    new_owner, distroseries=self.distroseries,
                    related_set=parent_ps)
            parent_to_child[parent_ps] = child_ps
            # Copy archivepermissions if we're not copying
            # cross-distribution.
            if (self.distroseries.distribution ==
                    parent_ps.distroseries.distribution):
                self._store.execute("""
                    INSERT INTO Archivepermission
                    (person, permission, archive, packageset, explicit)
                    SELECT person, permission, %s, %s, explicit
                    FROM Archivepermission WHERE packageset = %s
                    """ % sqlvalues(
                        self.distroseries.main_archive, child_ps.id,
                        parent_ps.id))
        # Copy the relations between sets, and the contents.
        for old_series_ps, new_series_ps in parent_to_child.items():
            old_series_sets = old_series_ps.setsIncluded(
                direct_inclusion=True)
            for old_series_child in old_series_sets:
                new_series_ps.add(parent_to_child[old_series_child])
            new_series_ps.add(old_series_ps.sourcesIncluded(
                direct_inclusion=True))
