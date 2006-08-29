# (C) Canonical Software Ltd. 2004, all rights reserved.

import os
from StringIO import StringIO
from md5 import md5
from sha import sha
from datetime import datetime


from canonical.librarian.client import LibrarianClient
from canonical.lp.dbschema import (
    PackagePublishingStatus, PackagePublishingPriority,
    PackagePublishingPocket, DistributionReleaseStatus)
from canonical.launchpad.interfaces import NotInPool

__all__ = [ 'Publisher', 'pocketsuffix', 'suffixpocket' ]


pocketsuffix = {
    PackagePublishingPocket.RELEASE: "",
    PackagePublishingPocket.SECURITY: "-security",
    PackagePublishingPocket.UPDATES: "-updates",
    PackagePublishingPocket.PROPOSED: "-proposed",
    PackagePublishingPocket.BACKPORTS: "-backports",
}

suffixpocket = dict((v, k) for (k, v) in pocketsuffix.items())


def package_name(filename):
    """Extract a package name from a debian package filename."""
    return (os.path.basename(filename).split("_"))[0]

def f_touch(*parts):
    """Touch the file named by the arguments concatenated as a path."""
    fname = os.path.join(*parts)
    open(fname, "w").close()

def reorder_components(components):
    """Return a list of the components provided.

    The list will be ordered by the semi arbitrary rules of ubuntu.
    Over time this method needs to be removed and replaced by having
    component ordering codified in the database.
    """
    ret = []
    for comp in ['main', 'restricted', 'universe', 'multiverse']:
        if comp in components:
            ret.append(comp)
            components.remove(comp)
    ret.extend(components)
    return ret


class Publisher(object):
    """Publisher is the class used to provide the facility to publish
    files in the pool of a Distribution. The publisher objects will be
    instantiated by the archive build scripts and will be used throughout
    the processing of each DistroRelease and DistroArchRelease in question
    """

    def __init__(self, logger, config, diskpool, distribution, library=None):
        """Initialise a publisher. Publishers need the pool root dir
        and a DiskPool object.
        """
        self._config = config
        self._root = config.poolroot
        if not os.path.isdir(self._root):
            raise ValueError("Root %s is not a directory or does "
                             "not exist" % self._root)
        self._diskpool = diskpool
        if library is None:
            self._library = LibrarianClient()
        else:
            self._library = library
        self._logger = logger
        self._pathfor = diskpool.pathFor
        self.distro = distribution

        # We need somewhere to note down where the debian-installer
        # components came from. in _di_release_components we store
        # sets, keyed by distrorelease name of the component names
        # which contain debian-installer binaries.  This is filled out
        # when generating overrides and file lists, and then consumed
        # when generating apt-ftparchive configuration.
        self._di_release_components = {}

        # As we generate file lists for apt-ftparchive we record which
        # distroreleases and so on we need to generate Release files for.
        # We store this in _release_files_needed and consume the information
        # when writeReleaseFiles is called.
        self._release_files_needed = {}

    def debug(self, *args, **kwargs):
        self._logger.debug(*args, **kwargs)

    def publishOverrides(self, sourceoverrides, binaryoverrides, \
                         defaultcomponent = "main"):
        """Given the provided sourceoverrides and binaryoverrides, output
        a set of override files for use in apt-ftparchive.

        The files will be written to overrideroot with filenames of the form:
        override.<distrorelease>.<component>[.src]

        Attributes which must be present in sourceoverrides are:
        drname, spname, cname, sname

        Attributes which must be present in binaryoverrides are:
        drname, spname, cname, sname, priority

        The binary priority will be mapped via the values in dbschema.py
        """

        # overrides[distrorelease][component][src/bin] = list of lists
        overrides = {}

        prio = {}
        for p in PackagePublishingPriority._items:
            prio[p] = PackagePublishingPriority._items[p].title.lower()
            self.debug("Recording priority %d with name %s", p, prio[p])

        for so in sourceoverrides:
            distrorelease = so.distroreleasename.encode('utf-8')
            distrorelease += pocketsuffix[so.pocket]
            component = so.componentname.encode('utf-8')
            section = so.sectionname.encode('utf-8')
            sourcepackagename = so.sourcepackagename.encode('utf-8')
            if component != defaultcomponent:
                section = "%s/%s" % (component, section)
            overrides.setdefault(distrorelease, {})
            this_override = overrides[distrorelease]
            this_override.setdefault(component, {})
            this_override[component].setdefault('src', [])
            this_override[component].setdefault('bin', [])
            this_override[component]['src'].append((sourcepackagename,
                                                    section))

        for bo in binaryoverrides:
            distrorelease = bo.distroreleasename.encode('utf-8')
            distrorelease += pocketsuffix[bo.pocket]
            component = bo.componentname.encode('utf-8')
            section = bo.sectionname.encode('utf-8')
            binarypackagename = bo.binarypackagename.encode('utf-8')
            priority = bo.priority
            if priority not in prio:
                raise ValueError, "Unknown priority value %d" % priority
            priority = prio[priority]
            if component != defaultcomponent:
                section = "%s/%s" % (component, section)
            overrides.setdefault(distrorelease, {})
            this_override = overrides[distrorelease]
            this_override.setdefault(component, {})
            this_override[component].setdefault('src', [])
            this_override[component].setdefault('bin', [])
            this_override[component]['bin'].append((binarypackagename,
                                                    priority,
                                                    section))

        # Now generate the files on disk...
        for distrorelease in overrides:
            for component in overrides[distrorelease]:
                self.debug("Generating overrides for %s/%s..." % (
                    distrorelease, component))
                di_overrides = []
                # XXX: use os.path.join
                #   -- kiko, 2005-09-23
                f = open("%s/override.%s.%s" % (self._config.overrideroot,
                                                distrorelease, component), "w")
                ef = open("%s/override.%s.extra.%s" % (
                    self._config.overrideroot, distrorelease, component), "w")
                overrides[distrorelease][component]['bin'].sort()
                for tup in overrides[distrorelease][component]['bin']:
                    if tup[2].endswith("debian-installer"):
                        # Note in _di_release_components that this
                        # distrorelease has d-i contents in this component.
                        self._di_release_components.setdefault(distrorelease,
                                                set()).add(component)
                        # And record the tuple for later output in the d-i
                        # override file instead
                        di_overrides.append(tup)
                    else:
                        f.write("\t".join(tup))
                        f.write("\n")
                        # XXX: dsilvers: This needs to be made databaseish
                        # and be actually managed within Launchpad. (Or else
                        # we need to change the ubuntu as appropriate and look
                        # for bugs addresses etc in launchpad.
                        # bug 3900
                        ef.write("\t".join([tup[0], "Origin", "Ubuntu"]))
                        ef.write("\n")
                        ef.write("\t".join(
                            [tup[0], "Bugs",
                             "mailto:ubuntu-users@lists.ubuntu.com"]))
                        ef.write("\n")
                f.close()

                # XXX: dsilvers: As above, this needs to be integrated into
                # the database at some point.
                # bug 3900
                extra_extra_overrides = os.path.join(
                    self._config.miscroot,
                    "more-extra.override.%s.%s" % (distrorelease,
                                                   component))
                if not os.path.exists(extra_extra_overrides):
                    unpocketed_release = "-".join(
                        distrorelease.split('-')[:-1])
                    extra_extra_overrides = os.path.join(
                        self._config.miscroot,
                        "more-extra.override.%s.%s" % (unpocketed_release,
                                                       component))
                if os.path.exists(extra_extra_overrides):
                    eef = open(extra_extra_overrides, "r")
                    extras = {}
                    for line in eef:
                        line = line.strip()
                        if line:
                            (package, header, value) = line.split(None, 2)
                            pkg_extras = extras.setdefault(package, {})
                            header_values = pkg_extras.setdefault(header, [])
                            header_values.append(value)
                    eef.close()
                    for pkg, headers in extras.items():
                        for header, values in headers.items():
                            ef.write("\t".join(
                                [pkg, header, ", ".join(values)]))
                            ef.write("\n")
                ef.close()

                if len(di_overrides):
                    # We managed to find some d-i bits in these binaries,
                    # so we output a magical "component"-ish "section"-y sort
                    # of thing.
                    # Elmo informs me that the technical term for the d-i stuff
                    # is "horrible f***ing bodge"
                    # XXX: use os.path.join
                    #   -- kiko, 2005-09-23
                    f = open("%s/override.%s.%s.debian-installer" % (
                        self._config.overrideroot, distrorelease, component),
                             "w")
                    di_overrides.sort()
                    for tup in di_overrides:
                        f.write("\t".join(tup))
                        f.write("\n")
                    f.close()

                # XXX: use os.path.join
                #   -- kiko, 2005-09-23
                f = open("%s/override.%s.%s.src" % (self._config.overrideroot,
                                                    distrorelease,
                                                    component), "w")
                overrides[distrorelease][component]['src'].sort()
                for tup in overrides[distrorelease][component]['src']:
                    f.write("\t".join(tup))
                    f.write("\n")
                f.close()

    def publishFileLists(self, sourcefiles, binaryfiles):
        """Collate the set of source files and binary files provided and
        write out all the file list files for them.

        listroot/distrorelease_component_source
        listroot/distrorelease_component_binary-archname
        """
        filelist = {}
        self.debug("Collating lists of source files...")
        for f in sourcefiles:
            distrorelease = f.distroreleasename.encode('utf-8')
            distrorelease += pocketsuffix[f.pocket]
            component = f.componentname.encode('utf-8')
            sourcepackagename = f.sourcepackagename.encode('utf-8')
            filename = f.libraryfilealiasfilename.encode('utf-8')
            ondiskname = self._pathfor(component, sourcepackagename,
                                       filename)

            filelist.setdefault(distrorelease, {})
            filelist[distrorelease].setdefault(component, {})
            filelist[distrorelease][component].setdefault('source', [])
            filelist[distrorelease][component]['source'].append(ondiskname)

        self.debug("Collating lists of binary files...")
        for f in binaryfiles:
            distrorelease = f.distroreleasename.encode('utf-8')
            distrorelease += pocketsuffix[f.pocket]
            component = f.componentname.encode('utf-8')
            sourcepackagename = f.sourcepackagename.encode('utf-8')
            filename = f.libraryfilealiasfilename.encode('utf-8')
            architecturetag = f.architecturetag.encode('utf-8')
            architecturetag = "binary-%s" % architecturetag

            ondiskname = self._pathfor(component, sourcepackagename, filename)

            filelist.setdefault(distrorelease, {})
            this_file = filelist[distrorelease]
            this_file.setdefault(component, {})
            this_file[component].setdefault(architecturetag, [])
            this_file[component][architecturetag].append(ondiskname)

        # Now write them out...
        for distrorelease, components in filelist.items():
            self.debug("Writing file lists for %s" % distrorelease)
            for component, architectures in components.items():
                for architecture, file_names in architectures.items():
                    di_files = []
                    files = []
                    f = open(os.path.join(self._config.overrideroot,
                                          "%s_%s_%s" % (distrorelease,
                                                        component,
                                                        architecture)), "w")
                    for name in file_names:
                        if name.endswith(".udeb"):
                            # Once again, note that this componentonent in this
                            # distrorelease has d-i elements
                            self._di_release_components.setdefault(
                                distrorelease, set()).add(component)
                            # And note the name for output later
                            di_files.append(name)
                        else:
                            files.append(name)
                    files.sort(key=package_name)
                    f.write("\n".join(files))
                    f.write("\n")
                    f.close()
                    # Record this distrorelease/component/arch as needing a
                    # Release file.
                    self._release_files_needed.setdefault(
                        distrorelease, {}).setdefault(component,
                                                      set()).add(architecture)
                    if len(di_files):
                        # Once again, some d-i stuff to write out...
                        self.debug("Writing d-i file list for %s/%s/%s" % (
                            distrorelease, component, architecture))
                        # Erm, os.path.join would be much more of a pain
                        # here than the interpolation.
                        f = open("%s/%s_%s_debian-installer_%s" % (
                            self._config.overrideroot, distrorelease,
                            component, architecture), "w")
                        di_files.sort(key=package_name)
                        f.write("\n".join(di_files))
                        f.write("\n")
                        f.close()


    def generateAptFTPConfig(self, fullpublish=False, dirty_pockets=None):
        """Generate an APT FTPArchive configuration from the provided
        config object and the paths we either know or have given to us.

        If fullpublish is true, we generate config for everything.

        Otherwise, we aim to limit our config to certain distroreleases
        and pockets. By default, we will exclude release pockets for
        released distros, and in addition, if dirty_pockets is specified,
        we exclude any pocket not mentioned in it. dirty_pockets must be
        a nested dictionary of booleans, keyed by distrorelease.name then
        pocket.
        """
        cnf = StringIO()
        cnf.write("""
Dir
{
    ArchiveDir "%s";
    OverrideDir "%s";
    CacheDir "%s";
};

Default
{
    Packages::Compress ". gzip bzip2";
    Sources::Compress ". gzip bzip2";
    Contents::Compress "gzip";
    DeLinkLimit 0;
    MaxContentsChange 12000;
    FileMode 0644;
}

TreeDefault
{
    Contents::Header "%s/contents.header";
};


        """ % (
        self._config.archiveroot,
        self._config.overrideroot,
        self._config.cacheroot,
        self._config.miscroot
        ))

        stanza_template = """
tree "%(DISTS)s/%(DISTRORELEASEONDISK)s"
{
    FileList "%(LISTPATH)s/%(DISTRORELEASEBYFILE)s_$(SECTION)_binary-$(ARCH)";
    SourceFileList "%(LISTPATH)s/%(DISTRORELEASE)s_$(SECTION)_source";
    Sections "%(SECTIONS)s";
    Architectures "%(ARCHITECTURES)s";
    BinOverride "override.%(DISTRORELEASE)s.$(SECTION)";
    SrcOverride "override.%(DISTRORELEASE)s.$(SECTION).src";
    %(HIDEEXTRA)sExtraOverride "override.%(DISTRORELEASE)s.extra.$(SECTION)";
    Packages::Extensions "%(EXTENSIONS)s";
    BinCacheDB "packages-%(CACHEINSERT)s$(ARCH).db";
    Contents " ";
}

"""
        # cnf now contains a basic header. Add a dists entry for each
        # of the distroreleases we've touched
        for dr in self._config.distroReleaseNames():
            if (not fullpublish and
                dirty_pockets is not None and
                not dirty_pockets.get(dr, False)):
                self.debug("Skipping a-f stanza for %s" % dr)
                continue
            
            db_dr = self.distro[dr]
            for pocket in pocketsuffix:
                if (pocketsuffix[pocket] == '' and
                    (db_dr.releasestatus not in (
                    DistributionReleaseStatus.FROZEN,
                    DistributionReleaseStatus.DEVELOPMENT,
                    DistributionReleaseStatus.EXPERIMENTAL))
                    and not fullpublish):
                    # We don't write out the entries for releases in the
                    # CURRENT/SUPPORTED/OBSOLETE states (unless we're doing a
                    # a full publisher run).
                    continue

                if (not fullpublish and
                    dirty_pockets is not None and
                    not dirty_pockets.get(dr, {}).get(pocket, False)):
                    self.debug("Skipping a-f stanza for %s/%s" %
                                       (dr, pocket.name))
                    continue
                
                oarchs = self._config.archTagsForRelease(dr)
                ocomps = self._config.componentsForRelease(dr)
                # Firstly, pare comps down to the ones we've output
                comps = []
                for comp in ocomps:
                    comp_path = os.path.join(
                        self._config.overrideroot,
                        "_".join([dr + pocketsuffix[pocket],
                                  comp, "source"]))
                    if not os.path.exists(comp_path):
                        # Create an empty file if we don't have one so that
                        # apt-ftparchive will dtrt.
                        open(comp_path, "w").close()
                        # Also create an empty override file just in case.
                        open(os.path.join(
                            self._config.overrideroot,
                            ".".join(["override", dr + pocketsuffix[pocket],
                                      comp])), "w").close()
                        # Also create an empty source override file
                        open(os.path.join(
                            self._config.overrideroot,
                            ".".join(["override", dr + pocketsuffix[pocket],
                                      comp, "src"])), "w").close()
                    comps.append(comp)
                if len(comps) == 0:
                    self.debug("Did not find any components to create config "
                               "for %s%s" % (dr, pocketsuffix[pocket]))
                    continue
                # Second up, pare archs down as appropriate
                archs = []
                for arch in oarchs:
                    arch_path = os.path.join(
                        self._config.overrideroot,
                        "_".join([dr + pocketsuffix[pocket],
                                  comps[0],
                                  "binary-"+arch]))
                    if not os.path.exists(arch_path):
                        # Create an empty file if we don't have one so that
                        # apt-ftparchive will dtrt.
                        open(arch_path, "w").close()
                    archs.append(arch)
                self.debug("Generating apt config for %s%s" % (
                    dr, pocketsuffix[pocket]))
                # Replace those tokens
                cnf.write(stanza_template % {
                    "LISTPATH": self._config.overrideroot,
                    "DISTRORELEASE": dr + pocketsuffix[pocket],
                    "DISTRORELEASEBYFILE": dr + pocketsuffix[pocket],
                    "DISTRORELEASEONDISK": dr + pocketsuffix[pocket],
                    "ARCHITECTURES": " ".join(archs + ["source"]),
                    "SECTIONS": " ".join(comps),
                    "EXTENSIONS": ".deb",
                    "CACHEINSERT": "",
                    "DISTS": os.path.basename(self._config.distsroot),
                    "HIDEEXTRA": ""
                    })
                dr_full_name = dr + pocketsuffix[pocket]
                if (dr_full_name in self._di_release_components and
                    len(archs) > 0):
                    for component in self._di_release_components[dr_full_name]:
                        cnf.write(stanza_template % {
                            "LISTPATH": self._config.overrideroot,
                            "DISTRORELEASEONDISK": "%s%s/%s" % (dr,
                                                          pocketsuffix[pocket],
                                                          component),
                            "DISTRORELEASEBYFILE": "%s%s_%s" % (dr,
                                                          pocketsuffix[pocket],
                                                          component),
                            "DISTRORELEASE": "%s%s.%s" % (dr,
                                                          pocketsuffix[pocket],
                                                          component),
                            "ARCHITECTURES": " ".join(archs),
                            "SECTIONS": "debian-installer",
                            "EXTENSIONS": ".udeb",
                            "CACHEINSERT": "debian-installer-",
                            "DISTS": os.path.basename(self._config.distsroot),
                            "HIDEEXTRA": "// "
                            })

                def safe_mkdir(path):
                    if not os.path.exists(path):
                        os.makedirs(path)


                for comp in comps:
                    component_path = os.path.join(self._config.distsroot,
                                                  dr + pocketsuffix[pocket],
                                                  comp)
                    base_paths = [component_path]
                    if dr_full_name in self._di_release_components:
                        if comp in self._di_release_components[dr_full_name]:
                            base_paths.append(os.path.join(component_path,
                                                           "debian-installer"))
                    for base_path in base_paths:
                        if "debian-installer" not in base_path:
                            safe_mkdir(os.path.join(base_path, "source"))
                        for arch in archs:
                            safe_mkdir(os.path.join(base_path, "binary-"+arch))
        # And now return that string.
        s = cnf.getvalue()
        cnf.close()

        return s

    def unpublishDeathRow(self, condemnedsources, condemnedbinaries,
                          livesources, livebinaries):
        """Take the list of publishing records provided and unpublish them.
        You should only pass in entries you want to be unpublished because
        this will result in the files being removed if they're not otherwise
        in use.
        """
        livefiles = set()
        condemnedfiles = set()
        details = {}

        # XXX: the duplication below begs creation of a method
        #   -- kiko, 2005-09-23
        for p in livesources:
            fn = p.libraryfilealiasfilename.encode('utf-8')
            sn = p.sourcepackagename.encode('utf-8')
            cn = p.componentname.encode('utf-8')
            filename = self._pathfor(cn, sn, fn)
            details.setdefault(filename, [cn, sn, fn])
            livefiles.add(filename)
        for p in livebinaries:
            fn = p.libraryfilealiasfilename.encode('utf-8')
            sn = p.sourcepackagename.encode('utf-8')
            cn = p.componentname.encode('utf-8')
            filename = self._pathfor(cn, sn, fn)
            details.setdefault(filename, [cn, sn, fn])
            livefiles.add(filename)

        for p in condemnedsources:
            fn = p.libraryfilealiasfilename.encode('utf-8')
            sn = p.sourcepackagename.encode('utf-8')
            cn = p.componentname.encode('utf-8')
            filename = self._pathfor(cn, sn, fn)
            details.setdefault(filename, [cn, sn, fn])
            condemnedfiles.add(filename)

        for p in condemnedbinaries:
            fn = p.libraryfilealiasfilename.encode('utf-8')
            sn = p.sourcepackagename.encode('utf-8')
            cn = p.componentname.encode('utf-8')
            filename = self._pathfor(cn, sn, fn)
            details.setdefault(filename, [cn, sn, fn])
            condemnedfiles.add(filename)

        for f in condemnedfiles - livefiles:
            try:
                self._diskpool.removeFile(details[f][0],
                                          details[f][1],
                                          details[f][2])
            except NotInPool:
                # It's safe for us to let this slide because it means that
                # the file is already gone.
                pass
            except:
                # XXX dsilvers 2004-11-16: This depends on a logging
                # infrastructure. I need to decide on one...
                # Do something to log the failure to remove
                self._logger.exception("Removing file generated exception")
                pass

    def _writeSumLine(self, distrorelease_name, out_file, file_name, sum_form):
        """Write out a checksum line to the given file for the given
        filename in the given form.
        """
        full_name = os.path.join(self._config.distsroot,
                                 distrorelease_name, file_name)
        if not os.path.exists(full_name):
            # The file we were asked to write out doesn't exist.
            # Most likely we have an incomplete archive (E.g. no sources
            # for a given distrorelease). This is a non-fatal issue
            self.debug("Failed to find " + full_name)
            return
        in_file = open(full_name,"r")
        contents = in_file.read()
        in_file.close()
        length = len(contents)
        checksum = sum_form(contents).hexdigest()
        out_file.write(" %s % 16d %s\n" % (checksum, length, file_name))

    def _writeDistroRelease(self, distribution, distrorelease,
                            full_name, pocket):
        """Write out the Release files for the provided distrorelease."""
        all_components = set()
        all_architectures = set()
        all_files = set()
        release_files_needed = self._release_files_needed[full_name]
        for component, architectures in release_files_needed.items():
            all_components.add(component)
            for architecture in architectures:
                self.debug("Writing Release file for %s/%s/%s" % (
                    full_name, component, architecture))
                if architecture != "source":
                    # Strip "binary-" off the front of the architecture before
                    # noting it in all_architectures
                    clean_architecture = architecture[7:]
                    all_architectures.add(clean_architecture)
                    file_stub = "Packages"

                    # Set up the debian-installer paths, which are nested
                    # inside the component
                    di_path = os.path.join(component, "debian-installer",
                                           architecture)
                    di_file_stub = os.path.join(di_path, file_stub)
                    for suffix in ('', '.gz', '.bz2'):
                        all_files.add(di_file_stub + suffix)
                else:
                    file_stub = "Sources"
                    clean_architecture = architecture

                # Now, grab the actual (non-di) files inside each of
                # the suite's architectures
                file_stub = os.path.join(component, architecture, file_stub)

                for suffix in ('', '.gz', '.bz2'):
                    all_files.add(file_stub + suffix)

                all_files.add(os.path.join(component, architecture, "Release"))

                f = open(os.path.join(self._config.distsroot, full_name,
                                      component, architecture, "Release"), "w")

                contents = """Archive: %s
Version: %s
Component: %s
Origin: %s
Label: %s
Architecture: %s
""" % (full_name, distrorelease.version, component, distribution.displayname,
       distribution.displayname, clean_architecture)
                f.write(contents)
                f.close()

        drsummary = "%s %s " % (distribution.displayname,
                                distrorelease.displayname)

        if pocket == PackagePublishingPocket.RELEASE:
            drsummary += distrorelease.version
        else:
            drsummary += pocket.name.capitalize()
                
        f = open(os.path.join(self._config.distsroot, full_name, "Release"),
                 "w")
        f.write("""Origin: %s
Label: %s
Suite: %s
Version: %s
Codename: %s
Date: %s
Architectures: %s
Components: %s
Description: %s
""" % (distribution.displayname, distribution.displayname,
       full_name, distrorelease.version, distrorelease.name,
       datetime.utcnow().strftime("%a, %d %b %Y %k:%M:%S UTC"),
       " ".join(all_architectures),
       " ".join(reorder_components(all_components)), drsummary))
        f.write("MD5Sum:\n")
        all_files = sorted(list(all_files), key=os.path.dirname)
        for file_name in all_files:
            self._writeSumLine(full_name, f, file_name, md5)
        f.write("SHA1:\n")
        for file_name in all_files:
            self._writeSumLine(full_name, f, file_name, sha)
        f.close()

    def writeReleaseFiles(self, full_run=False, dirty_pockets=None):
        """Write out the Release files for the provided distribution.

        If full_run is specified, we include all pockets of all releases.
        
        Otherwise, if dirty_pockets is specified, we include only pockets
        flagged as true in dirty_pockets (which must be a nested dictionary
        of booleans by distrorelease.name then pocket).

        If neither optional argument is specified, we include all pockets
        which are not release pockets for released distros.
        """
        for distrorelease in self.distro:
            for pocket, suffix in pocketsuffix.items():

                # Check if we've worked in this pocket; if not (and
                # full_run is not set), skip generation of release files.
                if dirty_pockets is not None:
                    release_pockets = dirty_pockets.get(distrorelease.name, {})
                    if (not full_run and
                        not release_pockets.get(pocket, False)):
                        self.debug("Skipping release files for %s/%s" %
                                   (distrorelease.name, pocket.name))
                        continue
                
                if ((not full_run) and suffix == ''
                    and distrorelease.releasestatus not in (
                    DistributionReleaseStatus.FROZEN,
                    DistributionReleaseStatus.DEVELOPMENT,
                    DistributionReleaseStatus.EXPERIMENTAL)):
                    # We're not doing a full run, the pocket is the release
                    # pocket and the distrorelease is now 'stable' so we
                    # should skip writing out a Release file for it.
                    continue

                full_distrorelease_name = distrorelease.name + suffix

                if full_distrorelease_name in self._release_files_needed:
                    self._writeDistroRelease(self.distro,
                                             distrorelease,
                                             full_distrorelease_name,
                                             pocket)

    def writeIndexes(self, full_run=False, dirty_pockets=None):
        """Write Index files (Packages & Sources) using LP information.

        Iterates over all distroreleases and its pockets.
        Respect full_run (careful mode) and dirty_pockets.
        """
        for distrorelease in self.distro:
            for pocket, suffix in pocketsuffix.items():
                if dirty_pockets is not None:
                    release_pockets = dirty_pockets.get(distrorelease.name, {})
                    if (not full_run and
                        not release_pockets.get(pocket, False)):
                        self.debug("Skipping release files for %s/%s" %
                                   (distrorelease.name, pocket.name))
                        continue

                if ((not full_run) and suffix == ''
                    and distrorelease.releasestatus not in (
                    DistributionReleaseStatus.FROZEN,
                    DistributionReleaseStatus.DEVELOPMENT,
                    DistributionReleaseStatus.EXPERIMENTAL)):
                    continue

                for component in distrorelease.components:
                    self._writeComponentIndexes(
                        distrorelease, pocket, component)

    def _writeComponentIndexes(self, distrorelease, pocket, component):
        """Write Index files for single distrorelease + pocket + component.

        Iterates over all supported architectures and 'sources', no
        support for installer-* yet.
        Write contents using LP info to an extra plain file (Packages.lp
        and Sources.lp .
        """
        full_name = distrorelease.name + pocketsuffix[pocket]

        self.debug("Generate Index for %s/%s" % (full_name, component.name))

        source_index_path = os.path.join(
            self._config.distsroot, full_name, component.name,
            'source', "Sources.lp")
        source_index = open(source_index_path, "w")
        self.debug("Generating Sources")
        for spp in distrorelease.getSourcePackagePublishing(
            PackagePublishingStatus.PUBLISHED, pocket=pocket,
            component=component):
            source_index.write(spp.stanza().encode('utf-8'))

        source_index.close()

        for arch in distrorelease.architectures:
            arch_path = 'binary-%s' % arch.architecturetag
            self.debug("Generating Packages for %s" % arch_path)
            package_index_path = os.path.join(
                self._config.distsroot, full_name, component.name,
                arch_path, "Packages.lp")
            package_index = open(package_index_path, "w")

            for bpp in distrorelease.getBinaryPackagePublishing(
                archtag=arch.architecturetag, pocket=pocket,
                component=component):
                package_index.write(bpp.stanza().encode('utf-8'))

            package_index.close()

    def createEmptyPocketRequests(self):
        """Write out empty file lists etc for pockets we want to have
        Packages or Sources for but lack anything in them currently.
        """
        all_pockets = [suffix for _, suffix in pocketsuffix.items()]
        for distrorelease in self.distro:
            components = self._config.componentsForRelease(distrorelease.name)
            arch_tags = self._config.archTagsForRelease(distrorelease.name)
            pockets = all_pockets
            for suffix in pockets:
                full_distrorelease_name = distrorelease.name + suffix
                for comp in components:
                    if suffix == "":
                        # organize distrorelease and component pair as
                        # debian-installer -> distrorelease_component
                        # internal map. Only the main pocket actually
                        # needs these, though.
                        self._di_release_components.setdefault(
                            full_distrorelease_name, set()).add(comp)

                        f_touch(self._config.overrideroot,
                                ".".join(["override",
                                          full_distrorelease_name,
                                          comp,
                                          "debian-installer"]))

                    # Touch the source file lists and override files
                    f_touch(self._config.overrideroot,
                            ".".join(["override",
                                      full_distrorelease_name, comp]))
                    f_touch(self._config.overrideroot,
                            ".".join(["override",
                                      full_distrorelease_name, "extra", comp]))
                    f_touch(self._config.overrideroot,
                            ".".join(["override",
                                      full_distrorelease_name, comp, "src"]))

                    dr_comps = self._release_files_needed.setdefault(
                        full_distrorelease_name, {})

                    f_touch(self._config.overrideroot,
                            "_".join([full_distrorelease_name,
                                      comp, "source"]))
                    dr_comps.setdefault(comp, set()).add("source")

                    for arch in arch_tags:
                        # organize dr/comp/arch into temporary binary
                        # archive map for the architecture in question.
                        dr_special = self._release_files_needed.setdefault(
                            full_distrorelease_name, {})
                        dr_special.setdefault(comp, set()).add("binary-"+arch)

                        # Touch more file lists for the archs.
                        f_touch(self._config.overrideroot,
                                "_".join([full_distrorelease_name,
                                          comp,
                                          "binary-"+arch]))
                        f_touch(self._config.overrideroot,
                                "_".join([full_distrorelease_name,
                                          comp,
                                          "debian-installer",
                                          "binary-"+arch]))

