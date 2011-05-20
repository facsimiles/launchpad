# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=E0611,W0212

"""SQLBase implementation of IQuestionMessage."""

__metaclass__ = type

__all__ = [
    'QuestionMessage',
    ]

from lazr.delegates import delegates
from sqlobject import ForeignKey
from zope.interface import implements

from canonical.database.enumcol import EnumCol
from canonical.database.sqlbase import SQLBase
from lp.services.messages.interfaces.message import IMessage
from lp.answers.enums import (
    QuestionAction,
    QuestionStatus,
    )
from lp.answers.interfaces.questionmessage import IQuestionMessage
from lp.services.propertycache import cachedproperty


class QuestionMessage(SQLBase):
    """A table linking questions and messages."""

    implements(IQuestionMessage)

    delegates(IMessage, context='message')

    _table = 'QuestionMessage'

    question = ForeignKey(
        dbName='question', foreignKey='Question', notNull=True)
    message = ForeignKey(dbName='message', foreignKey='Message', notNull=True)

    action = EnumCol(
        schema=QuestionAction, notNull=True, default=QuestionAction.COMMENT)

    new_status = EnumCol(
        schema=QuestionStatus, notNull=True, default=QuestionStatus.OPEN)

    def __iter__(self):
        """See IMessage."""
        # Delegates do not proxy __ methods, because of the name mangling.
        return iter(self.chunks)

    @cachedproperty
    def index(self):
        return list(self.question.messages).index(self)

    @cachedproperty
    def display_index(self):
        # Return the index + 1 so that messages appear 1-indexed in the UI.
        return self.index + 1

    @property
    def visible(self):
        """See `IQuestionMessage.`"""
        return self.message.visible
