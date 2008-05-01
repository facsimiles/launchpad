__metaclass__ = type

__all__ = [
    'CodeReviewMessageAddView',
    'CodeReviewMessageView',
    ]

from zope.interface import Interface
from zope.schema import Text

from canonical.launchpad import _
from canonical.launchpad.interfaces import ICodeReviewMessage
from canonical.launchpad.webapp import (
    action, canonical_url, LaunchpadFormView,
    LaunchpadView)


class CodeReviewMessageView(LaunchpadView):
    """Standard view of a CodeReviewMessage"""

    @property
    def reply_link(self):
        return canonical_url(self.context, view_name='+reply')


class IEditCodeReviewMessage(Interface):

    comment = Text(
        title=_('Comment'), required=False, description=_(
        "This will be rendered as help text"))


class CodeReviewMessageAddView(LaunchpadFormView):

    schema = IEditCodeReviewMessage

    @property
    def is_reply(self):
        return ICodeReviewMessage.providedBy(self.context)

    @action('Add')
    def add_action(self, action, data):
        """Create the comment..."""
        message = self.context.branch_merge_proposal.createMessage(
            self.user, '', data['comment'], parent=self.context)
        self.next_url = canonical_url(message)
