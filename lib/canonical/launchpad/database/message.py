# Copyright 2009 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

# pylint: disable-msg=E0611,W0212

__metaclass__ = type
__all__ = [
    'DirectEmailAuthorization',
    'Message',
    'MessageChunk',
    'MessageJob',
    'MessageJobAction',
    'MessageSet',
    'UserToUserEmail',
    ]


import email

from email.Header import make_header, decode_header
from email.Utils import parseaddr, make_msgid, parsedate_tz, mktime_tz
from cStringIO import StringIO as cStringIO
from datetime import datetime
from operator import attrgetter

from canonical.database.enumcol import EnumCol
from lazr.enum import DBEnumeratedType, DBItem
from zope.component import getUtility
from zope.interface import implements
from zope.security.proxy import isinstance as zisinstance

from sqlobject import ForeignKey, StringCol, IntCol
from sqlobject import SQLMultipleJoin, SQLRelatedJoin
from storm.locals import And, DateTime, Int, Reference, Store, Storm, Unicode

import pytz

from canonical.config import config
from canonical.encoding import guess as ensure_unicode
from canonical.launchpad.helpers import get_filename_from_message_id
from lp.services.job.model.job import Job
from canonical.launchpad.interfaces import (
    ILibraryFileAliasSet, IPersonSet, NotFoundError, PersonCreationRationale,
    UnknownSender)
from canonical.launchpad.interfaces.message import (
    IDirectEmailAuthorization, IMessage, IMessageChunk, IMessageJob,
    IMessageSet, IUserToUserEmail, InvalidEmailMessage)
from canonical.launchpad.mail import signed_message_from_string
from lp.registry.interfaces.person import validate_public_person
from lazr.config import as_timedelta

from canonical.database.sqlbase import SQLBase
from canonical.database.constants import UTC_NOW
from canonical.database.datetimecol import UtcDateTimeCol

# this is a hard limit on the size of email we will be willing to store in
# the database.
MAX_EMAIL_SIZE = 10 * 1024 * 1024


def utcdatetime_from_field(field_value):
    """Turn an RFC 2822 Date: header value into a Python datetime (UTC).

    :param field_value: The value of the Date: header
    :type field_value: string
    :return: The corresponding datetime (UTC)
    :rtype: `datetime.datetime`
    :raise `InvalidEmailMessage`: when the date string cannot be converted.
    """
    try:
        date_tuple = parsedate_tz(field_value)
        timestamp = mktime_tz(date_tuple)
        return datetime.fromtimestamp(timestamp, tz=pytz.timezone('UTC'))
    except (TypeError, ValueError, OverflowError):
        raise InvalidEmailMessage('Invalid date %s' % field_value)


class Message(SQLBase):
    """A message. This is an RFC822-style message, typically it would be
    coming into the bug system, or coming in from a mailing list.
    """

    implements(IMessage)

    _table = 'Message'
    _defaultOrder = '-id'
    datecreated = UtcDateTimeCol(notNull=True, default=UTC_NOW)
    subject = StringCol(notNull=False, default=None)
    owner = ForeignKey(
        dbName='owner', foreignKey='Person',
        storm_validator=validate_public_person, notNull=False)
    parent = ForeignKey(foreignKey='Message', dbName='parent',
        notNull=False, default=None)
    rfc822msgid = StringCol(notNull=True)
    bugs = SQLRelatedJoin('Bug', joinColumn='message', otherColumn='bug',
        intermediateTable='BugMessage')
    chunks = SQLMultipleJoin('MessageChunk', joinColumn='message')
    raw = ForeignKey(foreignKey='LibraryFileAlias', dbName='raw',
                     default=None)
    bugattachments = SQLMultipleJoin('BugAttachment', joinColumn='message')

    def __iter__(self):
        """See IMessage.__iter__"""
        return iter(self.chunks)

    @property
    def followup_title(self):
        """See IMessage."""
        if self.title.lower().startswith('re: '):
            return self.title
        return 'Re: '+self.title

    @property
    def title(self):
        """See IMessage."""
        return self.subject

    @property
    def has_new_title(self):
        """See IMessage."""
        if self.parent is None:
            return True
        return self.title.lower().lstrip('re:').strip() != \
        self.parent.title.lower().lstrip('re:').strip()

    @property
    def sender(self):
        """See IMessage."""
        return self.owner

    @property
    def text_contents(self):
        """See IMessage."""
        bits = [unicode(chunk) for chunk in self if chunk.content]
        return '\n\n'.join(bits)

    # XXX flacoste 2006-09-08: Bogus attribute only present so that
    # verifyObject doesn't fail. That attribute is part of the
    # interface because it is used as a UI field in MessageAddView
    content = None


def get_parent_msgids(parsed_message):
    """Returns a list of message ids the mail was a reply to.

        >>> get_parent_msgids({'In-Reply-To': '<msgid1>'})
        ['<msgid1>']

        >>> get_parent_msgids({'References': '<msgid1> <msgid2>'})
        ['<msgid1>', '<msgid2>']

        >>> get_parent_msgids({'In-Reply-To': '<msgid1> <msgid2>'})
        ['<msgid1>', '<msgid2>']

        >>> get_parent_msgids({'In-Reply-To': '', 'References': ''})
        []

        >>> get_parent_msgids({})
        []
    """
    for name in ['In-Reply-To', 'References']:
        if parsed_message.has_key(name):
            return parsed_message.get(name).split()

    return []


class MessageSet:
    implements(IMessageSet)

    def get(self, rfc822msgid):
        messages = list(Message.selectBy(rfc822msgid=rfc822msgid))
        if len(messages) == 0:
            raise NotFoundError(rfc822msgid)
        return messages

    def fromText(self, subject, content, owner=None, datecreated=None,
        rfc822msgid=None):
        """See IMessageSet."""
        if datecreated is None:
            datecreated = UTC_NOW
        if rfc822msgid is None:
            rfc822msgid = make_msgid("launchpad")

        message = Message(
            subject=subject, rfc822msgid=rfc822msgid, owner=owner,
            datecreated=datecreated)
        MessageChunk(message=message, sequence=1, content=content)
        # XXX 2008-05-27 jamesh:
        # Ensure that BugMessages get flushed in same order as they
        # are created.
        Store.of(message).flush()
        return message

    def _decode_header(self, header):
        r"""Decode an RFC 2047 encoded header.

            >>> MessageSet()._decode_header('=?iso-8859-1?q?F=F6=F6_b=E4r?=')
            u'F\xf6\xf6 b\xe4r'

        If the header isn't encoded properly, the characters that can't
        be decoded are replaced with unicode question marks.

            >>> MessageSet()._decode_header('=?utf-8?q?F=F6=F6_b=E4r?=')
            u'F\ufffd\ufffd'
        """
        # Unfold the header before decoding it.
        header = ''.join(header.splitlines())

        bits = email.Header.decode_header(header)
        # Re-encode the header parts using utf-8, replacing undecodable
        # characters with question marks.
        re_encoded_bits = []
        for bytes, charset in bits:
            if charset is None:
                charset = 'us-ascii'
            # 2008-09-26 gary:
            # The RFC 2047 encoding names and the Python encoding names are
            # not always the same. A safer and more correct approach would use
            #   bytes.decode(email.Charset.Charset(charset).input_codec,
            #                'replace')
            # or similar, rather than
            #   bytes.decode(charset, 'replace')
            # That said, this has not bitten us so far, and is only likely to
            # cause problems in unusual encodings that we are hopefully
            # unlikely to encounter in this part of the code.
            re_encoded_bits.append(
                (bytes.decode(charset, 'replace').encode('utf-8'), 'utf-8'))

        return unicode(email.Header.make_header(re_encoded_bits))

    def fromEmail(self, email_message, owner=None, filealias=None,
                  parsed_message=None, create_missing_persons=False,
                  fallback_parent=None, date_created=None):
        """See IMessageSet.fromEmail."""
        # It does not make sense to handle Unicode strings, as email
        # messages may contain chunks encoded in differing character sets.
        # Passing Unicode in here indicates a bug.
        if not zisinstance(email_message, str):
            raise TypeError(
                'email_message must be a normal string.  Got: %r'
                % email_message)

        # Parse the raw message into an email.Message.Message instance,
        # if we haven't been given one already.
        if parsed_message is None:
            parsed_message = email.message_from_string(email_message)

        # We could easily generate a default, but a missing message-id
        # almost certainly means a developer is using this method when
        # they shouldn't (by creating emails by hand and passing them here),
        # which is broken because they will almost certainly have Unicode
        # errors.
        rfc822msgid = parsed_message.get('message-id')
        if not rfc822msgid:
            raise InvalidEmailMessage('Missing Message-Id')

        # make sure we don't process anything too long
        if len(email_message) > MAX_EMAIL_SIZE:
            raise InvalidEmailMessage('Msg %s size %d exceeds limit %d' % (
                rfc822msgid, len(email_message), MAX_EMAIL_SIZE))

        # Handle duplicate Message-Id
        # XXX kiko 2005-08-03: shouldn't we be using DuplicateMessageId here?
        try:
            existing_msgs = self.get(rfc822msgid=rfc822msgid)
        except LookupError:
            pass
        else:
            # we are now allowing multiple msgs in the db with the same
            # rfc822 msg-id to allow for variations in headers and,
            # potentially, content. so we scan through the results to try
            # and find one that matches,
            for existing in existing_msgs:
                existing_raw = existing.raw.read()
                if email_message == existing_raw:
                    return existing
                # ok, this is an interesting situation. we have a new
                # message with the same rfc822 msg-id as an existing message
                # in the database, but the message headers and/or content
                # are different. For the moment, we have chosen to allow
                # this, but in future we may want to flag it in some way

        # Stuff a copy of the raw email into the Librarian, if it isn't
        # already in there.
        file_alias_set = getUtility(ILibraryFileAliasSet) # Reused later
        if filealias is None:
            # We generate a filename to avoid people guessing the URL.
            # We don't want URLs to private bug messages to be guessable
            # for example.
            raw_filename = get_filename_from_message_id(
                parsed_message['message-id'])
            raw_email_message = file_alias_set.create(
                    raw_filename, len(email_message),
                    cStringIO(email_message), 'message/rfc822')
        else:
            raw_email_message = filealias

        # Find the message subject
        subject = self._decode_header(parsed_message.get('subject', ''))
        subject = subject.strip()

        if owner is None:
            # Try and determine the owner. We raise a NotFoundError
            # if the sender does not exist, unless we were asked to
            # create_missing_persons.
            person_set = getUtility(IPersonSet)
            from_hdr = self._decode_header(
                parsed_message.get('from', '')).strip()
            replyto_hdr = self._decode_header(
                parsed_message.get('reply-to', '')).strip()
            from_addrs = [from_hdr, replyto_hdr]
            from_addrs = [parseaddr(addr) for addr in from_addrs if addr]
            if len(from_addrs) == 0:
                raise InvalidEmailMessage('No From: or Reply-To: header')
            for from_addr in from_addrs:
                owner = person_set.getByEmail(from_addr[1].lower().strip())
                if owner is not None:
                    break
            if owner is None:
                if not create_missing_persons:
                    raise UnknownSender(from_addrs[0][1])
                # autocreate a person
                sendername = ensure_unicode(from_addrs[0][0].strip())
                senderemail = from_addrs[0][1].lower().strip()
                # XXX: Guilherme Salgado 2006-08-31 bug=62344:
                # It's hard to define what rationale to use here, and to
                # make things worst, it's almost impossible to provide a
                # meaningful comment having only the email message.
                owner = person_set.ensurePerson(
                    senderemail, sendername,
                    PersonCreationRationale.FROMEMAILMESSAGE)
                if owner is None:
                    raise UnknownSender(senderemail)

        # Get the parent of the message, if available in the db. We'll
        # go through all the message's parents until we find one that's
        # in the db.
        parent = None
        for parent_msgid in reversed(get_parent_msgids(parsed_message)):
            try:
                # we assume it's the first matching message
                parent = self.get(parent_msgid)[0]
                break
            except NotFoundError:
                pass
        else:
            parent = fallback_parent

        # figure out the date of the message
        if date_created is not None:
            datecreated = date_created
        else:
            datecreated = utcdatetime_from_field(parsed_message['date'])

        # make sure we don't create an email with a datecreated in the
        # future. also make sure we don't create an ancient one
        now = datetime.now(pytz.timezone('UTC'))
        thedistantpast = datetime(1990, 1, 1, tzinfo=pytz.timezone('UTC'))
        if datecreated < thedistantpast or datecreated > now:
            datecreated = UTC_NOW

        # DOIT
        message = Message(subject=subject, owner=owner,
            rfc822msgid=rfc822msgid, parent=parent,
            raw=raw_email_message, datecreated=datecreated)

        sequence = 1

        # Don't store the preamble or epilogue -- they are only there
        # to give hints to non-MIME aware clients
        #
        # Determine the encoding to use for non-multipart messages, and the
        # preamble and epilogue of multipart messages. We default to
        # iso-8859-1 as it seems fairly harmless to cope with old, broken
        # mail clients (The RFCs state US-ASCII as the default character
        # set).
        # default_charset = (parsed_message.get_content_charset() or
        #                    'iso-8859-1')
        #
        # XXX: kiko 2005-09-23: Is default_charset only useful here?
        #
        # if getattr(parsed_message, 'preamble', None):
        #     # We strip a leading and trailing newline - the email parser
        #     # seems to arbitrarily add them :-/
        #     preamble = parsed_message.preamble.decode(
        #             default_charset, 'replace')
        #     if preamble.strip():
        #         if preamble[0] == '\n':
        #             preamble = preamble[1:]
        #         if preamble[-1] == '\n':
        #             preamble = preamble[:-1]
        #         MessageChunk(
        #             message=message, sequence=sequence, content=preamble
        #             )
        #         sequence += 1

        for part in parsed_message.walk():
            mime_type = part.get_content_type()

            # Skip the multipart section that walk gives us. This part
            # is the entire message.
            if part.is_multipart():
                continue

            # Decode the content of this part.
            content = part.get_payload(decode=True)

            # Store the part as a MessageChunk
            #
            # We want only the content type text/plain as "main content".
            # Exceptions to this rule:
            # - if the content disposition header explicitly says that
            #   this part is an attachment, text/plain content is stored
            #   as a blob,
            # - if the content-disposition header provides a filename,
            #   text/plain content is stored as a blob.
            content_disposition = part.get('Content-disposition', '').lower()
            no_attachment = not content_disposition.startswith('attachment')
            if (mime_type == 'text/plain' and no_attachment
                and part.get_filename() is None):

                # Get the charset for the message part. If one isn't
                # specified, default to latin-1 to prevent
                # UnicodeDecodeErrors.
                charset = part.get_content_charset()
                if charset is None:
                    charset = 'latin-1'

                content = content.decode(charset, 'replace')

                if content.strip():
                    MessageChunk(
                        message=message, sequence=sequence,
                        content=content)
                    sequence += 1
            else:
                filename = part.get_filename() or 'unnamed'
                # Note we use the Content-Type header instead of
                # part.get_content_type() here to ensure we keep
                # parameters as sent. If Content-Type is None we default
                # to application/octet-stream.
                if part['content-type'] is None:
                    content_type = 'application/octet-stream'
                else:
                    content_type = part['content-type']

                if len(content) > 0:
                    blob = file_alias_set.create(
                        name=filename,
                        size=len(content),
                        file=cStringIO(content),
                        contentType=content_type
                        )
                    MessageChunk(message=message, sequence=sequence,
                                 blob=blob)
                    sequence += 1

        # Don't store the epilogue
        # if getattr(parsed_message, 'epilogue', None):
        #     epilogue = parsed_message.epilogue.decode(
        #             default_charset, 'replace')
        #     if epilogue.strip():
        #         if epilogue[0] == '\n':
        #             epilogue = epilogue[1:]
        #         if epilogue[-1] == '\n':
        #             epilogue = epilogue[:-1]
        #         MessageChunk(
        #             message=message, sequence=sequence, content=epilogue
        #             )

        # XXX 2008-05-27 jamesh:
        # Ensure that BugMessages get flushed in same order as they
        # are created.
        Store.of(message).flush()
        return message

    @staticmethod
    def _parentToChild(messages):
        """Return a mapping from parent to child and list of root messages."""
        result = {}
        roots = []
        for message in messages:
            if message.parent is None:
                roots.append(message)
            else:
                result.setdefault(message.parent, []).append(message)
            result.setdefault(message, [])
        return result, roots

    @classmethod
    def threadMessages(klass, messages):
        """See `IMessageSet`."""
        result, roots = klass._parentToChild(messages)
        def get_children(node):
            children = []
            for child in result[node]:
                children.append((child, get_children(child)))
            return children
        threads = []
        for root in roots:
            threads.append((root, get_children(root)))
        return threads

    @classmethod
    def flattenThreads(klass, threaded_messages, _depth=0):
        """See `IMessageSet`."""
        for message, children in threaded_messages:
            yield (_depth, message)
            for depth, message in klass.flattenThreads(children, _depth + 1):
                yield depth, message


class MessageChunk(SQLBase):
    """One part of a possibly multipart Message"""
    implements(IMessageChunk)

    _table = 'MessageChunk'
    _defaultOrder = 'sequence'

    message = ForeignKey(
        foreignKey='Message', dbName='message', notNull=True)

    sequence = IntCol(notNull=True)

    content = StringCol(notNull=False, default=None)

    blob = ForeignKey(
        foreignKey='LibraryFileAlias', dbName='blob', notNull=False,
        default=None
        )

    def __unicode__(self):
        """Return a text representation of this chunk.

        This is either the content, or a link to the blob in a format
        suitable for use in a text only environment, such as an email
        """
        if self.content:
            return self.content
        else:
            blob = self.blob
            return (
                "Attachment: %s\n"
                "Type:       %s\n"
                "URL:        %s" % (blob.filename, blob.mimetype, blob.url)
                )


class UserToUserEmail(Storm):
    """See `IUserToUserEmail`."""

    implements(IUserToUserEmail)

    __storm_table__ = 'UserToUserEmail'

    id = Int(primary=True)

    sender_id = Int(name='sender')
    sender = Reference(sender_id, 'Person.id')

    recipient_id = Int(name='recipient')
    recipient = Reference(recipient_id, 'Person.id')

    date_sent = DateTime(allow_none=False)

    subject = Unicode(allow_none=False)

    message_id = Unicode(allow_none=False)

    def __init__(self, message):
        """Create a new user-to-user email entry.

        :param message: the message being sent
        :type message: `email.message.Message`
        """
        super(UserToUserEmail, self).__init__()
        person_set = getUtility(IPersonSet)
        # Find the person who is sending this message.
        realname, address = parseaddr(message['from'])
        assert address, 'Message has no From: field'
        sender = person_set.getByEmail(address)
        assert sender is not None, 'No person for sender email: %s' % address
        # Find the person who is the recipient.
        realname, address = parseaddr(message['to'])
        assert address, 'Message has no To: field'
        recipient = person_set.getByEmail(address)
        assert recipient is not None, (
            'No person for recipient email: %s' % address)
        # Convert the date string into a UTC datetime.
        date = message['date']
        assert date is not None, 'Message has no Date: field'
        self.date_sent = utcdatetime_from_field(date)
        # Find the subject and message-id.
        message_id = message['message-id']
        assert message_id is not None, 'Message has no Message-ID: field'
        subject = message['subject']
        assert subject is not None, 'Message has no Subject: field'
        # Initialize.
        self.sender = sender
        self.recipient = recipient
        self.message_id = unicode(message_id, 'ascii')
        self.subject = unicode(make_header(decode_header(subject)))
        # Add the object to the store of the sender.  Our StormMigrationGuide
        # recommends against this saying "Note that the constructor should not
        # usually add the object to a store -- leave that for a FooSet.new()
        # method, or let it be inferred by a relation."
        #
        # On the other hand, we really don't need a UserToUserEmailSet for any
        # other purpose.  There isn't any other relationship that can be
        # inferred, so in this case I think it makes fine sense for the
        # constructor to add self to the store.  Also, this closely mimics
        # what the SQLObject compatibility layer does.
        Store.of(sender).add(self)


class MessageJobAction(DBEnumeratedType):
    """MessageJob action

    The action that a job should perform.
    """

    CREATE_MERGE_PROPOSAL = DBItem(1, """
        Create a merge proposal.

        Create a merge proposal from a message which must contain a merge
        directive.
        """)


class MessageJob(Storm):
    """A job for processing messages."""

    implements(IMessageJob)
    # XXX: AaronBentley 2009-02-05 bug=325883: This table is poorly named.
    __storm_table__ = 'MergeDirectiveJob'

    id = Int(primary=True)

    jobID = Int('job', allow_none=False)
    job = Reference(jobID, Job.id)

    message_bytesID = Int('merge_directive', allow_none=False)
    message_bytes = Reference(message_bytesID, 'LibraryFileAlias.id')

    action = EnumCol(enum=MessageJobAction)

    def __init__(self, message_bytes, action):
        Storm.__init__(self)
        self.job = Job()
        self.message_bytes = message_bytes
        self.action = action

    def destroySelf(self):
        """See `IMessageJob`."""
        self.job.destroySelf()
        Store.of(self).remove(self)

    def sync(self):
        """Update the database with all changes for this object."""
        store = Store.of(self)
        store.flush()
        store.autoreload(self)

    def getMessage(self):
        """See `IMessageJob`."""
        return signed_message_from_string(self.message_bytes.read())


class DirectEmailAuthorization:
    """See `IDirectEmailAuthorization`."""

    implements(IDirectEmailAuthorization)

    def __init__(self, sender):
        """Create a `UserContactBy` instance.

        :param sender: The sender we're checking.
        :type sender: `IPerson`
        :param after: The cutoff date for throttling.  Primarily used only for
            testing purposes.
        :type after: `datetime.datetime`
        """
        self.sender = sender

    def _getThrottlers(self, after):
        """Return a result set of entries affecting throttling decisions.

        :param after: Explicit cut off date.
        :type after: `datetime.datetime`
        """
        return Store.of(self.sender).find(
            UserToUserEmail,
            And(UserToUserEmail.sender == self.sender,
                UserToUserEmail.date_sent >= after))

    def _isAllowedAfter(self, after):
        """Like .is_allowed but used with an explicit cutoff date.

        For testing purposes only.

        :param after: Explicit cut off date.
        :type after: `datetime.datetime`
        :return: True if email is allowed
        :rtype: bool
        """
        # Count the number of messages from the sender since the throttle
        # date.
        store = Store.of(self.sender)
        messages_sent = self._getThrottlers(after).count()
        return messages_sent < config.launchpad.user_to_user_max_messages

    @property
    def is_allowed(self):
        """See `IDirectEmailAuthorization`."""
        # Users are only allowed to send X number of messages in a certain
        # period of time.  Both the number of messages and the time period
        # are configurable.
        now = datetime.now(pytz.timezone('UTC'))
        after = now - as_timedelta(
            config.launchpad.user_to_user_throttle_interval)
        return self._isAllowedAfter(after)

    @property
    def throttle_date(self):
        """See `IDirectEmailAuthorization`."""
        now = datetime.now(pytz.timezone('UTC'))
        after = now - as_timedelta(
            config.launchpad.user_to_user_throttle_interval)
        throttlers = self._getThrottlers(after)
        # We now have the set of emails that would throttle delivery.  If the
        # configuration variable has changed, this could produce more or less
        # than the now-allowed number of throttlers.  We should never get here
        # if it's less because the contact would have been allowed.
        #
        # If it's more, then we really want to count back from the sorted end,
        # because when /that/ contact record expires, they'll be able to
        # resend.  Here are two examples.
        #
        # affecters = A B C
        # max allowed = 3
        # index = len(affecters) - 3 == 0 == A
        # when A's date < the interval, they can try again
        #
        # affecters = A B C D E F G
        # max allowed (now) = 3
        # index = len(affecters) - 3 = 4 == E (counting from zero)
        # when E's date < than the interval, they can try again
        affecters = sorted(throttlers, key=attrgetter('date_sent'))
        max_throttlers = config.launchpad.user_to_user_max_messages
        expiry = len(affecters) - max_throttlers
        if expiry < 0:
            # There were fewer affecters than are now allowed, so they can
            # retry immediately.  Remember that the caller adds the interval
            # back, so this would give us 'now'.
            return after
        return affecters[expiry].date_sent

    @property
    def message_quota(self):
        """See `IDirectEmailAuthorization`."""
        return config.launchpad.user_to_user_max_messages

    def record(self, message):
        """See `IDirectEmailAuthorization`."""
        contact = UserToUserEmail(message)
        Store.of(self.sender).add(contact)
