"""SourceSource-related Interfaces for Launchpad

(c) Canonical Ltd 2004
"""

from zope.schema import Bool, Bytes, Choice, Datetime, Int, Text, \
                        TextLine, Password
from zope.interface import Interface, Attribute
from zope.i18nmessageid import MessageIDFactory
_ = MessageIDFactory('launchpad')

class ISourceSource(Interface):
    """A SourceSource job. This is a holdall for data about the upstream
    revision control system of an open source product, and whether or not
    we are able to syncronise our Arch repositories with that upstream
    revision control system. It allows for access to objects that model
    the SourceSource table."""
    #
    # XXX Mark Shuttleworth 03/10/04 Robert Collins please give a better
    #     description of each field below.
    #
    name = Attribute("The sourcesource unix name, a one-word lowercase \
        unique name for this sourcesource.")
    title = Attribute("The Title of this SourceSource")
    description = Attribute("A description of this SourceSource")
    product=Attribute ("a product backlink for this sourcesource")
    cvsroot = Attribute("The CVSRoot of this SourceSource")
    cvsmodule = Attribute("The CVS Module of this SourceSource")
    cvstarfile = Attribute("The TAR file name of the CVS repo tarball")
    cvstarfileurl = Attribute("The URL where we retrieved the CVS repo tarball")
    cvsbranch = Attribute("Branch From...")
    svnrepository = Attribute("Subversion repository, if this code is in\
                               subversion")
    releaseroot = Attribute("The root url where we look for releases???")
    releaseverstyle = Attribute("The version numbering style used for this product")
    releasefileglob = Attribute("The glob used to find releases")
    releaseparentbranch = Attribute("XXX Robert Collins please clarify")
    sourcepackage = Attribute("The source package this upstream is for")
    branch = Attribute("The Branch in the DB to which we sync.")
    lastsynced = Attribute("The timestamp of the last time we synced their \
                            upstream code into Arch.")
    syncinterval = Attribute("How much time to wait between syncs.")
    rcstype = Attribute("Enum of the type of upstream rcs this is")
    hosted = Attribute("Robert Collins - please explain")
    upstreamname = Attribute("The upstream name")
    processingapproved = Attribute("The time when processing was \
                                    approved???what processsing???")
    syncingapproved = Attribute("The timestamp when we decided to go into \
                                 sync mode for this branch.")
    newarchive = Attribute("the target archive")
    newbranchcategory = Attribute("the arch category to use")
    newbranchbranch = Attribute("branchto.. don't know what that is")
    newbranchversion = Attribute("the arch version to use when importing this \
                                  code to arch")
    packagedistro = Attribute("Keybuk please explain")
    packagefiles_collapsed = Attribute("Keybuk please explain me")
    owner = Attribute("The owner of this upstream source record.")
    currentgpgkeyd = Attribute("Robert please explain me")
    fileidreference = Attribute("Robert please explain me")
    autotested = Attribute("""This enum is defined in
                            dbschema.ImportTestStatus.""")
    datestarted = Attribute("The timestamp of the last import run start.")
    datefinished = Attribute("The timestamp of the last import run completion.")

    def syncCertified():
        """is the sourcesource sync enabled?"""
    def autoSyncEnabled():
        """is the sourcesource enabled for automatic syncronisation?"""
    
    def canChangeProduct():
        """is this sync allowed to have its product changed?"""
    
    def namesReviewed():
        """Return True if the product and project details have been reviewed
        and are still active."""
    
class ISourceSourceAdmin(Interface):
    """Administration of SourceSource jobs"""

    def changeProduct(product):
        """change the product this sync belongs to to be 'product'"""
    
    def certifyForSync():
        """enable this to sync"""

    def enableAutoSync():
        """enable this sourcesource for automatic syncronisation"""
    


class ISourceSourceSet(Interface):
    """An interface for the set of all SourceSource objects."""

    syncingapproved = Attribute("""Setting this will limit the Set to those
        with syncing approved.""")

    processingapproved = Attribute("""Setting this will limit the Set to those
        with processing approved.""")

    autotested = Attribute("""Setting this will limit the set to those which
        have been autotested.""")

    projecttext = Attribute("""Setting this will limit the set to those
        which are connected to projects and products that match this
        text.""")

    assigned = Attribute("""Setting this will limit the set to those which are
        connected to any product but the one named 'unassigned'.""")

    title = Attribute('Title')

    def __getitem__(sourcesourcename):
        """Return the specified sourcesource object."""

    def search(text=None, state=None):
        """Return the sourcesource objects matching the state and text given
        as arguments."""

    def filter(sync=None, process=None, tested=None, projecttext=None,
               assigned=None):
        """Return a subset of the sourcesources, filtered by the criteria
        given in the arguments."""

