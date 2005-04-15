# Copyright 2004-2005 Canonical Ltd.  All rights reserved.

from zope.interface import Interface, Attribute

from canonical.launchpad.interfaces.rawfiledata import ICanAttachRawFileData
from canonical.launchpad.interfaces.rosettastats import IRosettaStats

__metaclass__ = type

__all__ = ('IPOTemplateSubset', 'IPOTemplateSet', 'IPOTemplate',
           'IEditPOTemplate')

class IPOTemplateSubset(Interface):
    """A subset of POTemplate."""

    sourcepackagename = Attribute(
        "The sourcepackagename associated with this subset of POTemplates.")

    distrorelease = Attribute(
        "The distrorelease associated with this subset of POTemplates.")

    productrelease = Attribute(
        "The productrelease associated with this subset of POTemplates.")

    title = Attribute("Title - use for launchpad pages")

    def __iter__():
        """Returns an iterator over all POTemplate for this subset."""

    def __getitem__(name):
        """Get a POTemplate by its name."""


class IPOTemplateSet(Interface):
    """A set of PO templates."""

    def __iter__():
        """Return an iterator over all PO templates."""

    def __getitem__(name):
        """Get a PO template by its name."""

    def getSubset(distrorelease=None, sourcepackagename=None,
                  productrelease=None):
        """Return a POTemplateSubset object depending on the given arguments.
        """

    def getTemplatesPendingImport():
        """Return a list of PO templates that have data to be imported."""


class IPOTemplate(IRosettaStats, ICanAttachRawFileData):
    """A PO template. For example 'nautilus/po/nautilus.pot'."""

    id = Attribute("The id of this POTemplate.")

    productrelease = Attribute("The PO template's product release.")

    priority = Attribute("The PO template priority.")

    potemplatename = Attribute("The PO template name.")

    name = Attribute("The POTemplateName.name, a short text name usually "
                     "derived from the template translation domain.")

    title = Attribute("The PO template's title.")

    description = Attribute("The PO template's description.")

    copyright = Attribute("The copyright information for this PO template.")

    license = Attribute("The license that applies to this PO template.")

    datecreated = Attribute("When this template was created.")

    path = Attribute("The path to the template in the source.")

    iscurrent = Attribute("Whether this template is current or not.")

    owner = Attribute("The owner of the template.")

    sourcepackagename = Attribute(
        "The name of the sourcepackage from where this PO template is.")

    sourcepackageversion = Attribute(
        "The version of the sourcepackage from where this PO template comes.")

    distrorelease = Attribute(
        "The distribution where this PO template belongs.")

    header = Attribute("The header of this .pot file.")

    binarypackagename = Attribute(
        "The name of the binarypackage where this potemplate's translations"
        " are installed.")

    languagepack = Attribute(
        "Flag to know if this potemplate belongs to a languagepack.")

    filename = Attribute(
        "The file name this PO Template had when last imported.")

    # A "current" messageset is one that was in the latest version of
    # the POTemplate parsed and recorded in the database. Current
    # MessageSets are indicated by having 'sequence > 0'

    def __len__():
        """Returns the number of Current IPOMessageSets in this template."""

    def __iter__():
        """Return an iterator over Current IPOMessageSets in this template."""

    def messageSet(key, onlyCurrent=False):
        """Extract one or several POTMessageSets from this template.

        If the key is a string or a unicode object, returns the
        IPOMsgSet in this template that has a primary message ID
        with the given text.

        If the key is a slice, returns the message IDs by sequence within the
        given slice.

        If onlyCurrent is True, then get only current message sets.
        """

    def __getitem__(key):
        """Same as messageSet(), with onlyCurrent=True
        """

    def getPOTMsgSetByID(id):
        """Return the POTMsgSet object related to this POTemplate with the id.

        If there is no POTMsgSet with that id and for that POTemplate, return
        None.
        """

    def filterMessageSets(current, translated, languages, slice):
        '''
        Return message sets from this PO template, filtered by various
        properties.

        current:
            Whether the message sets need be complete or not.
        translated:
            Wether the messages sets need be translated in the specified
            languages or not.
        languages:
            The languages used for testing translatedness.
        slice:
            The range of results to be selected, or None, for all results.
        '''

    def languages():
        """Return an iterator over languages that this template's messages are
        translated into.
        """

    def poFiles():
        """Return an iterator over the PO files that exist for this language."""

    def poFilesToImport():
        """Returns all PO files from this POTemplate that have a rawfile 
        pending of import into Rosetta."""

    def getPOFileByLang(language_code, variant=None):
        """Get the PO file of the given language and (potentially)
        variant. If no variant is specified then the translation
        without a variant is given.

        Raises KeyError if there is no such POFile."""

    def queryPOFileByLang(language_code, variant=None):
        """Return a PO file for this PO template in the given language, if
        it exists, or None if it does not."""

    def hasMessageID(msgid):
        """Check whether a message set with the given message ID exists within
        this template."""

    def hasPluralMessage():
        """Test whether this template has any message sets which are plural
        message sets."""

    def canEditTranslations(person):
        """Say if a person is able to edit existing translations.

        Return True or False depending if the user is allowed to edit those
        translations.

        At this moment, only translations from a distro release are locked.
        """

    # TODO provide a way to look through non-current message ids.


class IEditPOTemplate(IPOTemplate):
    """Edit interface for an IPOTemplate."""

    sourcepackagename = Attribute("""The name of the sourcepackage from where
        this PO template is.""")

    distrorelease = Attribute("""The distribution where this PO template
        belongs""")

    def expireAllMessages():
        """Mark all of our message sets as not current (sequence=0)"""

    #def makeMessageSet(messageid_text, pofile=None):
    #    """Add a message set to this template.  Primary message ID
    #    is 'messageid_text'.
    #    If one already exists, a KeyError is raised."""

    def getOrCreatePOFile(language_code, variant=None, owner=None):
        """Create and return a new po file in the given language. The
        variant is optional.

        Raises LanguageNotFound if the language does not exist in the
        database.
        """

    def createMessageSetFromMessageID(msgid):
        """Creates in the database a new message set.

        As a side-effect, creates a message ID sighting in the database for the
        new set's prime message ID.

        Returns the newly created message set.
        """

    def createMessageSetFromText(text):
        """Creates in the database a new message set.

        Similar to createMessageSetFromMessageID, but takes a text object
        (unicode or string) rather than a message ID.

        Returns the newly created message set.
        """
