
# Zope interfaces
from zope.interface import implements
from zope.component import ComponentLookupError
from zope.app.security.interfaces import IUnauthenticatedPrincipal

# SQL imports
from sqlobject import DateTimeCol, ForeignKey, IntCol, StringCol, BoolCol
from sqlobject import MultipleJoin, RelatedJoin, AND, LIKE
from canonical.database.sqlbase import SQLBase, quote

# canonical imports
import canonical.launchpad.interfaces as interfaces
from canonical.launchpad.interfaces import *
from canonical.launchpad.database import *

class RosettaLanguages(object):
    implements(interfaces.ILanguages)

    def __iter__(self):
        return iter(RosettaLanguage.select(orderBy='englishName'))

    def __getitem__(self, code):
        try:
            return RosettaLanguage.byCode(code)
        except SQLObjectNotFound:
            raise KeyError, code

    def keys(self):
        return [language.code for language in RosettaLanguage.select()]


class RosettaSchemas(object):
    implements(interfaces.ISchemas)

    def __getitem__(self, name):
        try:
            schema = RosettaSchema.byName(name)
        except SQLObjectNotFound:
            raise KeyError, name
        else:
            return schema

    def keys(self):
        return [schema.name for schema in RosettaSchema.select()]

class RosettaSchema(SQLBase):
    implements(interfaces.ISchema)

    _table = 'Schema'

    _columns = [
        ForeignKey(name='owner', foreignKey='Person',
            dbName='owner', notNull=True),
        StringCol(name='name', dbName='name', notNull=True, alternateID=True),
        StringCol(name='title', dbName='title', notNull=True),
        StringCol(name='description', dbName='description', notNull=True),
#        BoolCol(name='extensible', dbName='extensible', notNull=True),
    ]

    _labelsJoin = MultipleJoin('RosettaLabel', joinColumn='schema')

    def labels(self):
        return iter(self._labelsJoin)

    def label(self, name):
        '''SELECT * FROM Label WHERE
            Label.schema = id AND
            Label.name = name;'''
        results = RosettaLabel.select('''
            Label.schema = %d AND
            Label.name = %s''' %
            (self.id, quote(name)))

        if results.count() == 0:
            raise KeyError, name
        else:
            return results[0]


class RosettaLabel(SQLBase):
    implements(interfaces.ILabel)

    _table = 'Label'

    _columns = [
        ForeignKey(name='schema', foreignKey='RosettaSchema', dbName='schema',
            notNull=True),
        StringCol(name='name', dbName='name', notNull=True),
        StringCol(name='title', dbName='title', notNull=True),
        StringCol(name='description', dbName='description', notNull=True),
    ]

    _personsJoin = RelatedJoin('Person', joinColumn='label',
        otherColumn='person', intermediateTable='PersonLabel')

    def persons(self):
        for person in self._personsJoin:
            yield person[0]


class RosettaCategory(RosettaLabel):
    implements(interfaces.ICategory)

    _effortPOTemplatesJoin = MultipleJoin('RosettaTranslationEffortPOTemplate',
        joinColumn='category')

    def poTemplates(self):
        # XXX: We assume that template will have always a row because the
        # database's referencial integrity
        for effortPOTemplate in self._effortPOTemplatesJoin:
            template = RosettaPOTemplate.selectBy(id=effortPOTemplate.poTemplate)
            yield template[0]

    def poTemplate(self, name):
        for template in self.poTemplates():
            if template.name == name:
                return template

        raise KeyError, name

    def messageCount(self):
        count = 0
        for t in self.poTemplates():
            count += len(t)
        return count

    def currentCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.currentCount(language)
        return count

    def updatesCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.updatesCount(language)
        return count

    def rosettaCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.rosettaCount(language)
        return count


class RosettaTranslationEfforts(object):
    implements(interfaces.ITranslationEfforts)

    def __iter__(self):
        return iter(RosettaTranslationEffort.select())

    def __getitem__(self, name):
        ret = RosettaTranslationEffort.selectBy(name=name)

        if ret.count() == 0:
            raise KeyError, name
        else:
            return ret[0]

    def new(self, name, title, shortDescription, description, owner, project):
        if RosettaTranslationEffort.selectBy(name=name).count():
            raise KeyError, "There is already a translation effort with that name"

        return RosettaTranslationEffort(name=name,
                              title=title,
                              shortDescription=shortDescription,
                              description=description,
                              owner=owner, project=project)

    def search(self, query):
        query = quote('%%' + query + '%%')
        #query = quote(query)
        return RosettaTranslationEffort.select('''title ILIKE %s  OR description ILIKE %s''' %
            (query, query))


class RosettaTranslationEffort(SQLBase):
    implements(interfaces.ITranslationEffort)

    _table = 'TranslationEffort'

    _columns = [
        ForeignKey(name='owner', foreignKey='Person', dbName='owner',
            notNull=True),
        ForeignKey(name='project', foreignKey='Project',
            dbName='project', notNull=True),
        ForeignKey(name='categoriesSchema', foreignKey='RosettaSchema',
            dbName='categories', notNull=False),
        StringCol(name='name', dbName='name', notNull=True, unique=True),
        StringCol(name='title', dbName='title', notNull=True),
        StringCol(name='shortDescription', dbName='shortdesc', notNull=True),
        StringCol(name='description', dbName='description', notNull=True),
    ]

    def categories(self):
        '''SELECT * FROM Label
            WHERE schema=self.categories'''
        return iter(RosettaCategory.selectBy(schema=self.categories))

    def category(self, name):
        ret = RosettaCategory.selectBy(name=name, schema=self.categories)

        if ret.count() == 0:
            raise KeyError, name
        else:
            return ret[0]

    def messageCount(self):
        count = 0
        for c in self.categories():
            count += c.messageCount()
        return count

    def currentCount(self, language):
        count = 0
        for c in self.categories():
            count += c.currentCount(language)
        return count

    def updatesCount(self, language):
        count = 0
        for c in self.categories():
            count += c.updatesCount(language)
        return count

    def rosettaCount(self, language):
        count = 0
        for c in self.categories():
            count += c.rosettaCount(language)
        return count


class RosettaTranslationEffortPOTemplate(SQLBase):
    implements(interfaces.ITranslationEffortPOTemplate)

    _table = 'TranslationEffortPOTemplate'

    _columns = [
        ForeignKey(name='translationEffort',
            foreignKey='RosettaTranslationEffort', dbName='translationeffort',
            notNull=True),
        ForeignKey(name='poTemplate', foreignKey='RosettaPOTemplate',
            dbName='potemplate', notNull=True),
        ForeignKey(name='category', foreignKey='RosettaCategory',
            dbName='category', notNull=False),
        IntCol(name='priority', dbName='priority', notNull=True),
    ]

class RosettaLanguage(SQLBase):
    implements(interfaces.ILanguage)

    _table = 'Language'

    _columns = [
        StringCol(name='code', dbName='code', notNull=True, unique=True,
            alternateID=True),
        StringCol(name='nativeName', dbName='nativename'),
        StringCol(name='englishName', dbName='englishname'),
        IntCol(name='pluralForms', dbName='pluralforms'),
        StringCol(name='pluralExpression', dbName='pluralexpression'),
    ]

    def translateLabel(self):
        try:
            schema = RosettaSchema.byName('translation-languages')
        except SQLObjectNotFound:
            raise RuntimeError("Launchpad installation is broken, " + \
                    "the DB is missing essential data.")
        return RosettaLabel.selectBy(schemaID=schema.id, name=self.code)

    def translators(self):
        return self.translateLabel().persons()


class RosettaBranch(SQLBase):
    implements(interfaces.IBranch)

    _table = 'Branch'

    _columns = [
        StringCol(name='title', dbName='title'),
        StringCol(name='description', dbName='description')
    ]


class RosettaPOMessageSet(SQLBase):
    implements(interfaces.IEditPOTemplateOrPOFileMessageSet)

    _table = 'POMsgSet'

    _columns = [
        ForeignKey(name='poTemplate', foreignKey='RosettaPOTemplate', dbName='potemplate', notNull=True),
        ForeignKey(name='poFile', foreignKey='RosettaPOFile', dbName='pofile', notNull=False),
        ForeignKey(name='primeMessageID_', foreignKey='RosettaPOMessageID', dbName='primemsgid', notNull=True),
        IntCol(name='sequence', dbName='sequence', notNull=True),
        BoolCol(name='isComplete', dbName='iscomplete', notNull=True),
        BoolCol(name='fuzzy', dbName='fuzzy', notNull=True),
        BoolCol(name='obsolete', dbName='obsolete', notNull=True),
        StringCol(name='commentText', dbName='commenttext', notNull=False),
        StringCol(name='fileReferences', dbName='filereferences', notNull=False),
        StringCol(name='sourceComment', dbName='sourcecomment', notNull=False),
        StringCol(name='flagsComment', dbName='flagscomment', notNull=False),
    ]

    def __init__(self, **kw):
        SQLBase.__init__(self, **kw)

        poFile = None

        if kw.has_key('poFile'):
            poFile = kw['poFile']

        if poFile is None:
            # this is a IPOTemplateMessageSet
            directlyProvides(self, interfaces.IPOTemplateMessageSet)
        else:
            # this is a IPOFileMessageSet
            directlyProvides(self, interfaces.IEditPOFileMessageSet)

    def flags(self):
        if self.flagsComment is None:
            return ()
        else:
            return [ flag for flag in
                self.flagsComment.replace(' ', '').split(',') if flag != '' ]

    def messageIDs(self):
        return RosettaPOMessageID.select('''
            POMsgIDSighting.pomsgset = %d AND
            POMsgIDSighting.pomsgid = POMsgID.id AND
            POMsgIDSighting.inlastrevision = TRUE
            ''' % self.id, clauseTables=('POMsgIDSighting',),
            orderBy='POMsgIDSighting.pluralform')

    def getMessageIDSighting(self, pluralForm, allowOld=False):
        """Return the message ID sighting that is current and has the
        plural form provided."""
        if allowOld:
            results = RosettaPOMessageIDSighting.selectBy(
                poMessageSetID=self.id,
                pluralForm=pluralForm)
        else:
            results = RosettaPOMessageIDSighting.selectBy(
                poMessageSetID=self.id,
                pluralForm=pluralForm,
                inLastRevision=True)

        if results.count() == 0:
            raise KeyError, pluralForm
        else:
            assert results.count() == 1

            return results[0]

    def pluralForms(self):
        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")

        # we need to check a pot-set, if one exists, to find whether this set
        # *does* have plural forms, by looking at the number of message ids.
        # It's usually not safe to look at the message ids of this message set,
        # because if it's a po-set it may be incorrect; but if a pot-set can't
        # be found, then self is our best guess.
        try:
            potset = self.templateMessageSet()
        except KeyError:
            # set is obsolete... try to get the count from self, although
            # that's not 100% reliable
            # when/if we split tables, this shouldn't be necessary
            potset = self
        if potset.messageIDs().count() > 1:
            # has plurals
            return self.poFile.pluralForms
        else:
            # message set is singular
            return 1

    def templateMessageSet(self):
        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")

        potset = RosettaPOMessageSet.select('''
            poTemplate = %d AND
            poFile IS NULL AND
            primemsgid = %d
            ''' % (self.poTemplate.id, self.primeMessageID_.id))
        if potset.count() == 0:
            raise KeyError, self.primeMessageID_.msgid
        assert potset.count() == 1
        return potset[0]

    def translations(self):
        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")

        pluralforms = self.pluralForms()
        if pluralforms is None:
            raise RuntimeError(
                "Don't know the number of plural forms for this PO file!")

        results = list(RosettaPOTranslationSighting.select(
            'pomsgset = %d AND active = TRUE' % self.id,
            orderBy='pluralForm'))

        translations = []

        for form in range(pluralforms):
            if results and results[0].pluralForm == form:
                translations.append(results.pop(0).poTranslation.translation)
            else:
                translations.append(None)

        return translations

    def translationsForLanguage(self, language):
        if self.poFile is not None:
            raise RuntimeError(
                "This method cannot be used with PO file message sets!")

        # Find the number of plural forms.

        # XXX: Not sure if falling back to the languages table is the right
        # thing to do.
        languages = getUtility(interfaces.ILanguages)

        try:
            pofile = self.poTemplate.poFile(language)
            pluralforms = pofile.pluralForms
        except KeyError:
            pofile = None
            pluralforms = languages[language].pluralForms

        if self.messageIDs().count() == 1:
            pluralforms = 1

        if pluralforms == None:
            raise RuntimeError(
                "Don't know the number of plural forms for this PO file!")

        if pofile is None:
            return [None] * pluralforms

        # Find the sibling message set.

        results = RosettaPOMessageSet.select('''pofile = %d AND primemsgid = %d'''
            % (pofile.id, self.primeMessageID_.id))

        if not (0 <= results.count() <= 1):
            raise AssertionError("Duplicate message ID in PO file.")

        if results.count() == 0:
            return [None] * pluralforms

        translation_set = results[0]

        results = list(RosettaPOTranslationSighting.select(
            'pomsgset = %d AND active = TRUE' % translation_set.id,
            orderBy='pluralForm'))

        translations = []

        for form in range(pluralforms):
            if results and results[0].pluralForm == form:
                translations.append(results.pop(0).poTranslation.translation)
            else:
                translations.append(None)

        return translations

    def getTranslationSighting(self, pluralForm, allowOld=False):
        """Return the translation sighting that is committed and has the
        plural form specified."""
        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")
        if allowOld:
            translations = RosettaPOTranslationSighting.selectBy(
                poMessageSetID=self.id,
                pluralForm=pluralForm)
        else:
            translations = RosettaPOTranslationSighting.selectBy(
                poMessageSetID=self.id,
                inLastRevision=True,
                pluralForm=pluralForm)
        if translations.count() == 0:
            raise IndexError, pluralForm
        else:
            return translations[0]

    def translationSightings(self):
        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")
        return RosettaPOTranslationSighting.selectBy(
            poMessageSetID=self.id)

    # IEditPOMessageSet

    def makeMessageIDSighting(self, text, pluralForm, update=False):
        """Create a new message ID sighting for this message set."""

        if type(text) is unicode:
            text = text.encode('utf-8')

        try:
            messageID = RosettaPOMessageID.byMsgid(text)
        except SQLObjectNotFound:
            messageID = RosettaPOMessageID(msgid=text)

        existing = RosettaPOMessageIDSighting.selectBy(
            poMessageSetID=self.id,
            poMessageID_ID=messageID.id,
            pluralForm=pluralForm)

        if existing.count():
            assert existing.count() == 1

            if not update:
                raise KeyError(
                    "There is already a message ID sighting for this "
                    "message set, text, and plural form")

            existing = existing[0]
            # XXX: Do we always want to set inLastRevision to True?
            existing.set(dateLastSeen = nowUTC, inLastRevision = True)

            return existing

        return RosettaPOMessageIDSighting(
            poMessageSet=self,
            poMessageID_=messageID,
            dateFirstSeen=nowUTC,
            dateLastSeen=nowUTC,
            inLastRevision=True,
            pluralForm=pluralForm)

    def makeTranslationSighting(self, person, text, pluralForm,
                              update=False, fromPOFile=False):
        """Create a new translation sighting for this message set."""

        if self.poFile is None:
            raise RuntimeError(
                "This method cannot be used with PO template message sets!")

        # First get hold of a RosettaPOTranslation for the specified text.
        try:
            translation = RosettaPOTranslation.byTranslation(text)
        except SQLObjectNotFound:
            translation = RosettaPOTranslation(translation=text)

        # Now get hold of any existing translation sightings.

        results = RosettaPOTranslationSighting.selectBy(
            poMessageSetID=self.id,
            poTranslationID=translation.id,
            pluralForm=pluralForm,
            personID=person.id)

        if results.count():
            # A sighting already exists.

            assert results.count() == 1

            if not update:
                raise KeyError(
                    "There is already a translation sighting for this "
                    "message set, text, plural form and person.")

            sighting = results[0]
            sighting.set(
                dateLastActive = nowUTC,
                active = True,
                # XXX: Ugly!
                inLastRevision = sighting.inLastRevision or fromPOFile)
        else:
            # No sighting exists yet.

            # XXX: This should use dbschema constants.
            if fromPOFile:
                origin = 1
            else:
                origin = 2

            sighting = RosettaPOTranslationSighting(
                poMessageSet=self,
                poTranslation=translation,
                dateFirstSeen= nowUTC,
                dateLastActive= nowUTC,
                inLastRevision=fromPOFile,
                pluralForm=pluralForm,
                active=True,
                person=person,
                origin=origin,
                # XXX: FIXME
                license=1)

        # Make all other sightings inactive.

        self._connection.query(
            '''
            UPDATE POTranslationSighting SET active = FALSE
            WHERE
                pomsgset = %d AND
                pluralform = %d AND
                id <> %d
            ''' % (self.id, pluralForm, sighting.id))

        return sighting


class RosettaPOMessageID(SQLBase):
    implements(interfaces.IPOMessageID)

    _table = 'POMsgID'

    _columns = [
        StringCol(name='msgid', dbName='msgid', notNull=True, unique=True,
            alternateID=True)
    ]


class RosettaPOTranslation(SQLBase):
    implements(interfaces.IPOTranslation)

    _table = 'POTranslation'

    _columns = [
        StringCol(name='translation', dbName='translation', notNull=True,
            unique=True, alternateID=True)
    ]


class SourceSource(SQLBase): 
    #, importd.Job.Job):
    #from canonical.soyuz.sql import SourcePackage, Branch
    """SourceSource table!"""

    _table = 'SourceSource'
    _columns = [
        StringCol('name', dbName='name', notNull=True),
        StringCol('title', dbName='title', notNull=True),
        StringCol('description', dbName='description', notNull=True),
        ForeignKey(name='product', foreignKey='SoyuzProduct', dbName='product',
                   default=1),
        StringCol('cvsroot', dbName='cvsroot', default=None),
        StringCol('cvsmodule', dbName='cvsmodule', default=None),
        ForeignKey(name='cvstarfile', foreignKey='LibraryFileAlias',
                   dbName='cvstarfile', default=None),
        StringCol('cvstarfileurl', dbName='cvstarfileurl', default=None),
        StringCol('cvsbranch', dbName='cvsbranch', default=None),
        StringCol('svnrepository', dbName='svnrepository', default=None),
        StringCol('releaseroot', dbName='releaseroot', default=None),
        StringCol('releaseverstyle', dbName='releaseverstyle', default=None),
        StringCol('releasefileglob', dbName='releasefileglob', default=None),
        ForeignKey(name='releaseparentbranch', foreignKey='Branch',
                   dbName='releaseparentbranch', default=None),
        ForeignKey(name='sourcepackage', foreignKey='SourcePackage',
                   dbName='sourcepackage', default=None),
        ForeignKey(name='branch', foreignKey='Branch',
                   dbName='branch', default=None),
        DateTimeCol('lastsynced', dbName='lastsynced', default=None),
        DateTimeCol('frequency', dbName='syncinterval', default=None),
        # WARNING: syncinterval column type is "interval", not "integer"
        # WARNING: make sure the data is what buildbot expects

        #IntCol('rcstype', dbName='rcstype', default=RCSTypeEnum.cvs,
        #       notNull=True),
        
        # FIXME: use 'RCSTypeEnum.cvs' rather than '1'
        IntCol('rcstype', dbName='rcstype', default=1,
               notNull=True),

        StringCol('hosted', dbName='hosted', default=None),
        StringCol('upstreamname', dbName='upstreamname', default=None),
        DateTimeCol('processingapproved', dbName='processingapproved',
                    notNull=False, default=None),
        DateTimeCol('syncingapproved', dbName='syncingapproved', notNull=False,
                    default=None),

        # For when Rob approves it
        StringCol('newarchive', dbName='newarchive'),
        StringCol('newbranchcategory', dbName='newbranchcategory'),
        StringCol('newbranchbranch', dbName='newbranchbranch'),
        StringCol('newbranchversion', dbName='newbranchversion'),

        # Temporary keybuk stuff
        StringCol('package_distro', dbName='packagedistro', default=None),
        StringCol('package_files_collapsed', dbName='packagefiles_collapsed',
                default=None),

        ForeignKey(name='owner', foreignKey='Person', dbName='owner',
                   notNull=True),
        StringCol('currentgpgkey', dbName='currentgpgkey', default=None),
    ]

class Person(SQLBase):
    """A Person."""

    implements(IPerson)

    _columns = [
        StringCol('displayname', default=None),
        StringCol('givenname', default=None),
        StringCol('familyname', default=None),
        StringCol('password', default=None),
        ForeignKey(name='teamowner', foreignKey='Person', dbName='teamowner'),
        StringCol('teamdescription', default=None),
        IntCol('karma'),
        DateTimeCol('karmatimestamp')
    ]

    _emailsJoin = MultipleJoin('RosettaEmailAddress', joinColumn='person')

    def emails(self):
        return iter(self._emailsJoin)

    # XXX: not implemented
    def maintainedProjects(self):
        '''SELECT Project.* FROM Project
            WHERE Project.owner = self.id
            '''

    # XXX: not implemented
    def translatedProjects(self):
        '''SELECT Project.* FROM Project, Product, POTemplate, POFile
            WHERE
                POFile.owner = self.id AND
                POFile.template = POTemplate.id AND
                POTemplate.product = Product.id AND
                Product.project = Project.id
            ORDER BY ???
            '''

    def translatedTemplates(self):
        '''
        SELECT * FROM POTemplate WHERE
            id IN (SELECT potemplate FROM pomsgset WHERE
                id IN (SELECT pomsgset FROM POTranslationSighting WHERE
                    origin = 2
                ORDER BY datefirstseen DESC))
        '''
        return POTemplate.select('''
            id IN (SELECT potemplate FROM pomsgset WHERE
                id IN (SELECT pomsgset FROM POTranslationSighting WHERE
                    origin = 2
                ORDER BY datefirstseen DESC))
            ''')

    _labelsJoin = RelatedJoin('Label', joinColumn='person',
        otherColumn='label', intermediateTable='PersonLabel')

    def languages(self):
        languages = getUtility(interfaces.ILanguages)
        try:
            schema = Schema.byName('translation-languages')
        except SQLObjectNotFound:
            raise RuntimeError("Launchpad installation is broken, " + \
                    "the DB is missing essential data.")

        for label in self._labelsJoin:
            if label.schema == schema:
                yield languages[label.name]

    def addLanguage(self, language):
        try:
            schema = Schema.byName('translation-languages')
        except SQLObjectNotFound:
            raise RuntimeError("Launchpad installation is broken, " + \
                    "the DB is missing essential data.")
        label = Label.selectBy(schemaID=schema.id, name=language.code)
        if label.count() < 1:
            # The label for this language does not exists yet into the
            # database, we should create it.
            label = Label(
                        schemaID=schema.id,
                        name=language.code,
                        title='Translates into ' + language.englishName,
                        description='A person with this label says that ' + \
                                    'knows how to translate into ' + \
                                    language.englishName)
        else:
            label = label[0]
        # This method comes from the RelatedJoin
        self.addLabel(label)

    def removeLanguage(self, language):
        try:
            schema = Schema.byName('translation-languages')
        except SQLObjectNotFound:
            raise RuntimeError("Launchpad installation is broken, " + \
                    "the DB is missing essential data.")
        label = Label.selectBy(schemaID=schema.id, name=language.code)[0]
        # This method comes from the RelatedJoin
        self.removeLabel(label)



def personFromPrincipal(principal):
    """Adapt canonical.lp.placelessauth.interfaces.ILaunchpadPrincipal 
        to IPerson
    """
    if IUnauthenticatedPrincipal.providedBy(principal):
        # When Zope3 interfaces allow returning None for "cannot adapt"
        # we can return None here.
        ##return None
        raise ComponentLookupError
    return Person.get(principal.id)


class EmailAddress(SQLBase):
    implements(IEmailAddress)

    _table = 'EmailAddress'
    _columns = [
        StringCol('email', notNull=True, unique=True),
        IntCol('status', notNull=True),
        ForeignKey(
            name='person', dbName='person', foreignKey='Person',
            )
        ]


class ProjectSet:
    implements(IProjectSet)

    def __iter__(self):
        return iter(Project.select())

    def __getitem__(self, name):
        ret = Project.selectBy(name=name)

        if ret.count() == 0:
            raise KeyError, name
        else:
            return ret[0]

    def new(self, name, displayname, title, homepageurl, shortdesc, 
            description, owner):
        #
        # XXX Mark Shuttleworth 03/10/04 Should the "new" method to create
        #     a new project be on ProjectSet? or Project?
        #
        name = name.encode('ascii')
        displayname = displayname.encode('ascii')
        title = title.encode('ascii')
        if type(url) != NoneType:
            url = url.encode('ascii')
        description = description.encode('ascii')

        if Project.selectBy(name=name).count():
            raise KeyError, "There is already a project with that name"

        return Project(name = name,
                       displayname = displayname,
                       title = title,
                       shortdesc = shortdesc,
                       description = description,
                       homepageurl = url,
                       owner = owner,
                       datecreated = 'now')

    def search(self, query):
        query = quote('%%' + query + '%%')
        #query = quote(query)
        return Project.select(
            'title ILIKE %s OR description ILIKE %s' % (query, query))


class Project(SQLBase):
    """A Project"""

    implements(IProject)

    _table = "Project"

    _columns = [
        ForeignKey(name='owner', foreignKey='Person', dbName='owner', \
            notNull=True),
        StringCol('name', notNull=True),
        StringCol('displayname', notNull=True),
        StringCol('title', notNull=True),
        StringCol('shortdesc', notNull=True),
        StringCol('description', notNull=True),
        # XXX: https://bugzilla.warthogs.hbd.com/bugzilla/show_bug.cgi?id=1968
        DateTimeCol('datecreated', notNull=True),
        StringCol('homepageurl', notNull=False, default=None),
        StringCol('wikiurl', notNull=False, default=None),
        StringCol('lastdoap', notNull=False, default=None)
    ]

    products = MultipleJoin('Product', joinColumn='project')
    _productsJoin = MultipleJoin('Product', joinColumn='project')

    def rosettaProducts(self):
        return iter(self._productsJoin)

    def getProduct(self, name):
        try:
            return Product.selectBy(projectID=self.id, name=name)[0]
        except IndexError:
            return None

    def poTemplate(self, name):
        # XXX: What does this have to do with Project?  This function never
        # uses self.  I suspect this belongs somewhere else.
        results = RosettaPOTemplate.selectBy(name=name)
        count = results.count()

        if count == 0:
            raise KeyError, name
        elif count == 1:
            return results[0]
        else:
            raise AssertionError("Too many results.")



class Product(SQLBase):
    """A Product."""

    implements(IProduct)

    _table = 'Product'

    _columns = [
        ForeignKey(
                name='project', foreignKey="Project", dbName="project",
                notNull=True
                ),
        ForeignKey(
                name='owner', foreignKey="Product", dbName="owner",
                notNull=True
                ),
        StringCol('name', notNull=True),
        StringCol('displayname', notNull=True),
        StringCol('title', notNull=True),
        StringCol('shortdesc', notNull=True),
        StringCol('description', notNull=True),
        DateTimeCol('datecreated', notNull=True),
        StringCol('homepageurl', notNull=False, default=None),
        StringCol('screenshotsurl', notNull=False, default=None),
        StringCol('wikiurl', notNull=False, default=None),
        StringCol('programminglang', notNull=False, default=None),
        StringCol('downloadurl', notNull=False, default=None),
        StringCol('lastdoap', notNull=False, default=None),
        ]

    _poTemplatesJoin = MultipleJoin('POTemplate', joinColumn='product')

    bugs = MultipleJoin('ProductBugAssignment', joinColumn='product')

    sourcesources = MultipleJoin('SourceSource', joinColumn='product')

    def poTemplates(self):
        return iter(self._poTemplatesJoin)

    def poTemplate(self, name):
        '''SELECT POTemplate.* FROM POTemplate WHERE
              POTemplate.product = id AND
              POTemplate.name = name;'''
        results = POTemplate.select('''
            POTemplate.product = %d AND
            POTemplate.name = %s''' %
            (self.id, quote(name)))

        if results.count() == 0:
            raise KeyError, name
        else:
            return results[0]

    def newPOTemplate(self, person, name, title):
        # XXX: we have to fill up a lot of other attributes
        if POTemplate.selectBy(
                productID=self.id, name=name).count():
            raise KeyError(
                  "This product already has a template named %s" % name)
        return POTemplate(name=name, title=title, product=self)

    def messageCount(self):
        count = 0
        for t in self.poTemplates():
            count += len(t)
        return count

    def currentCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.currentCount(language)
        return count

    def updatesCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.updatesCount(language)
        return count

    def rosettaCount(self, language):
        count = 0
        for t in self.poTemplates():
            count += t.rosettaCount(language)
        return count

