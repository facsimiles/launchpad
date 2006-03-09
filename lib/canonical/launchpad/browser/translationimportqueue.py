# Copyright 2005 Canonical Ltd.  All rights reserved.

"""Browser views for ITranslationImportQueue."""

__metaclass__ = type

__all__ = [
    'TranslationImportQueueEntryNavigation',
    'TranslationImportQueueEntryURL',
    'TranslationImportQueueEntryView',
    'TranslationImportQueueContextMenu',
    'TranslationImportQueueNavigation',
    'TranslationImportQueueView',
    ]

from zope.component import getUtility
from zope.interface import implements
from zope.app.form.browser.widget import renderElement

from canonical.launchpad.interfaces import (
    ITranslationImportQueueEntry, ITranslationImportQueue, ICanonicalUrlData,
    ILaunchpadCelebrities, IEditTranslationImportQueueEntry, IPOTemplateSet,
    NotFoundError, UnexpectedFormData)
from canonical.launchpad.webapp import (
    GetitemNavigation, LaunchpadView, ContextMenu, Link, canonical_url)
from canonical.launchpad.webapp.generalform import GeneralFormView
from canonical.lp.dbschema import RosettaImportStatus
from canonical.lp.z3batching import Batch
from canonical.lp.batching import BatchNavigator

class TranslationImportQueueEntryNavigation(GetitemNavigation):

    usedfor = ITranslationImportQueueEntry


class TranslationImportQueueEntryURL:
    implements(ICanonicalUrlData)

    def __init__(self, context):
        self.context = context

    @property
    def path(self):
        translation_import_queue  = self.context
        return str(translation_import_queue.id)

    @property
    def inside(self):
        return getUtility(ITranslationImportQueue)


class TranslationImportQueueEntryView(GeneralFormView):
    """The view part of the admin interface for the translation import queue.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.initialize()
        GeneralFormView.__init__(self, context, request)

    def initialize(self):
        """Set the fields that will be shown based on the 'context' values.

        If the context comes from a productseries, the sourcepackagename
        chooser is hidden.
        If the 'context.path' field ends with the string '.pot', it means that
        the context is related with a '.pot' file, so we hide the language and
        variant fields as they are useless here.
        """
        self.fieldNames = ['sourcepackagename', 'potemplatename', 'path',
            'language', 'variant']

        if (self.context.productseries is not None and
            'sourcepackagename' in self.fieldNames):
            self.fieldNames.remove('sourcepackagename')

        if self.context.path.endswith('.pot'):
            if 'language' in self.fieldNames:
                self.fieldNames.remove('language')
            if 'variant' in self.fieldNames:
                self.fieldNames.remove('variant')

    def process(self, potemplatename, path=None, sourcepackagename=None,
        language=None, variant=None):
        """Process the form we got from the submission."""
        translationimportqueue_set = getUtility(ITranslationImportQueue)

        if path and self.context.path != path:
            # The Rosetta Expert decided to change the path of the file.
            self.context.path = path

        if (sourcepackagename is not None and
            self.context.sourcepackagename is not None):
            # Got another sourcepackagename from the form, we will use it.
            destination_sourcepackagename = sourcepackagename
        else:
            destination_sourcepackagename = self.context.sourcepackagename

        potemplate_set = getUtility(IPOTemplateSet)
        if self.context.productseries is None:
            potemplate_subset = potemplate_set.getSubset(
                distrorelease=self.context.distrorelease,
                sourcepackagename=destination_sourcepackagename)
        else:
            potemplate_subset = potemplate_set.getSubset(
                productseries=self.context.productseries)
        try:
            potemplate = potemplate_subset[potemplatename.name]
        except NotFoundError:
            # The POTemplate does not exist. In this case we don't care if
            # the file is a .pot or a .po file, we can use either as the base
            # template.
            potemplate = potemplate_subset.new(
                potemplatename,
                self.context.path,
                self.context.importer)

            # Point to the right path.
            potemplate.path = self.context.path

            if language is None:
                # We can remove the element from the queue as it was a direct
                # import into an IPOTemplate.
                translationimportqueue_set.remove(self.context)
                return 'You associated the queue item with a PO Template.'

        if language is None:
            self.context.potemplate = potemplate
        else:
            # We are hadling an IPOFile import.
            pofile = potemplate.getOrCreatePOFile(language.code, variant,
                self.context.importer)
            self.context.pofile = pofile

        self.context.status = RosettaImportStatus.APPROVED

        return 'You associated the queue item with a PO File.'

    def nextURL(self):
        """Return the URL of the main import queue at 'rosetta/imports'."""
        translationimportqueue_set = getUtility(ITranslationImportQueue)
        return canonical_url(translationimportqueue_set)


class TranslationImportQueueNavigation(GetitemNavigation):

    usedfor = ITranslationImportQueue


class TranslationImportQueueContextMenu(ContextMenu):
    usedfor = ITranslationImportQueue
    links = ['overview']

    def overview(self):
        text = 'Import queue'
        return Link('', text)


class TranslationImportQueueView(LaunchpadView):
    """View class used for Translation Import Queue management."""

    def initialize(self):
        """Useful initialization for this view class."""
        self.form = self.request.form

        # Setup the batching for this page.
        start = int(self.request.get('batch_start', 0))
        self.batch = Batch(self.context.getAllEntries(), start, size=50)
        self.batchnav = BatchNavigator(self.batch, self.request)

        # Process the form.
        self.processForm()

    @property
    def has_entries(self):
        """Return whether there are things on the queue."""
        return len(self.context) > 0

    def processForm(self):
        """Block or remove entries from the queue based on the selection of
        the form.
        """
        if self.request.method != 'POST' or self.user is None:
            # The form was not submitted or the user is not logged in.
            return

        dispatch_table = {
            'handle_queue': self._handle_queue,
            }
        dispatch_to = [(key, method)
                        for key, method in dispatch_table.items()
                        if key in self.form
                      ]
        if len(dispatch_to) != 1:
            raise UnexpectedFormData(
                "There should be only one command in the form",
                dispatch_to)
        key, method = dispatch_to[0]
        method()

    def _handle_queue(self):
        """Handle a queue submission changing the status of its entries."""
        # The user must be logged in.
        assert self.user is not None

        for form_item in self.form:
            if not form_item.startswith('status-'):
                # We are not interested on this form_item.
                continue

            # It's an form_item to handle.
            try:
                common, id_string = form_item.split('-')
                # The id is an integer
                id = int(id_string)
            except ValueError:
                # We got an form_item with more than one '-' char or with an
                # id that is not a number, that means that someone is playing
                # badly with our system so it's safe to just ignore the
                # request.
                raise UnexpectedFormData(
                    'Ignored your request because it is broken.')
            # Get the entry we are working on.
            entry = self.context.get(id)
            new_status_name = self.form.get(form_item)
            if new_status_name == entry.status.name:
                # The entry's status didn't change we can jump to the next
                # entry.
                continue

            # The status changed.

            # XXX Carlos Perello Marin 20051124: We should not check the
            # permissions here but use the standard security system. Please, look
            # at https://launchpad.net/products/rosetta/+bug/4814 bug for more
            # details.
            celebrities = getUtility(ILaunchpadCelebrities)
            is_admin = (self.user.inTeam(celebrities.admin) or
                        self.user.inTeam(celebrities.rosetta_expert))
            is_owner = self.user.inTeam(entry.importer)

            # Only the importer, launchpad admins or Rosetta experts have
            # special permissions to change status.
            if new_status_name == 'deleted' and (is_admin or is_owner):
                entry.status = RosettaImportStatus.DELETED
            elif new_status_name == 'blocked' and is_admin:
                entry.status = RosettaImportStatus.BLOCKED
            elif (new_status_name == 'approved' and is_admin and
                  entry.import_into is not None):
                entry.status = RosettaImportStatus.APPROVED
            elif new_status_name == 'needs_review' and is_admin:
                entry.status = RosettaImportStatus.NEEDS_REVIEW
            else:
                # The user was not the importer or we are trying to set a
                # status that must not be set from this form. That means that
                # it's a broken request.
                raise UnexpectedFormData(
                    'Ignored the request to change the status from %s to %s.'
                        % (entry.status.name, new_status_name))

    def getStatusSelect(self, entry):
        """Return a select html tag with the possible status for entry

        :arg entry: An ITranslationImportQueueEntry.
        """
        assert helpers.check_permission('launchpad.Edit', entry), (
            'You can only change the status if you have rights to do it')

        if entry.status == RosettaImportStatus.APPROVED:
            # If the entry is approved, this status should appear and set as
            # selected.
            approved_html = renderElement('option', selected='yes',
                value=RosettaImportStatus.APPROVED.name,
                contents=RosettaImportStatus.APPROVED.title)
        elif (helpers.check_permission('launchpad.Admin', entry) and
              entry.import_into is not None):
            # The entry is not approved but if we are an admin and we know
            # where it's going to be imported, we can approve it.
            approved_html = renderElement('option',
                value=RosettaImportStatus.APPROVED.name,
                contents=RosettaImportStatus.APPROVED.title)
        else:
            # We should not add the approved status for this entry.
            approved_html = ''

        if entry.status == RosettaImportStatus.IMPORTED:
            # If the entry is imported, this status should appear and set as
            # selected.
            imported_html = renderElement('option', selected='yes',
                value=RosettaImportStatus.IMPORTED.name,
                contents=RosettaImportStatus.IMPORTED.title)
        else:
            # Only the import script should be able to set the status to
            # imported, and thus, we don't add it as an option to select.
            imported_html = ''

        if entry.status == RosettaImportStatus.DELETED:
            selected = 'yes'
        else:
            selected = 'no'

        deleted_html = renderElement('option', selected=selected,
            value=RosettaImportStatus.DELETED.name,
            contents=RosettaImportStatus.DELETED.title)

        if entry.status == RosettaImportStatus.FAILED:
            # If the entry is failed, this status should appear and set as
            # selected.
            failed_html = renderElement('option', selected='yes',
                value=RosettaImportStatus.FAILED.name,
                contents=RosettaImportStatus.FAILED.title)
        else:
            # Only the import script should be able to set the status to
            # failed, and thus, we don't add it as an option to select.
            failed_html = ''

        if entry.status == RosettaImportStatus.NEEDS_REVIEW:
            selected = 'yes'
        else:
            selected = 'no'

        needs_review_html = renderElement('option', selected=selected,
            value=RosettaImportStatus.NEEDS_REVIEW.name,
            contents=RosettaImportStatus.NEEDS_REVIEW.title)

        if entry.status == RosettaImportStatus.BLOCKED:
            # If the entry is blocked, this status should appear and set as
            # selected.
            blocked_html = renderElement('option', selected='yes',
                value=RosettaImportStatus.BLOCKED.name,
                contents=RosettaImportStatus.BLOCKED.title)
        elif helpers.check_permission('launchpad.Admin', entry):
            # The entry is not blocked but if we are an admin, we can block
            # it.
            blocked_html = renderElement('option',
                value=RosettaImportStatus.BLOCKED.name,
                contents=RosettaImportStatus.BLOCKED.title)
        else:
            # We should not add the blocked status for this entry.
            blocked_html = ''

        # Generate the final select html tag with the possible values.
        return renderElement('select', name='status-%d' % entry.id,
            contents='%s\n%s\n%s\n%s\n%s\n%s\n' % (
                approved_html, imported_html, deleted_html, failed_html,
                needs_review_html, blocked_html))
