import logging
from datetime import datetime

from pylons import config
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Boolean, DateTime, Integer, Unicode, UnicodeText

from adhocracy.model import meta

log = logging.getLogger(__name__)


message_table = Table(
    'message', meta.data,
    Column('id', Integer, primary_key=True),
    Column('subject', Unicode(140), nullable=False),
    Column('body', UnicodeText(), nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('sender_email', Unicode(255), nullable=False),
    Column('include_footer', Boolean, default=True, nullable=False),
    Column('sender_name', Unicode(255), nullable=True),
)


class Message(meta.Indexable):

    def __init__(self, subject, body, creator, sender_email, sender_name,
                 include_footer=True):
        self.subject = subject
        self.body = body
        self.creator = creator
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.include_footer = include_footer

    @classmethod
    def create(cls, subject, body, creator, sender_email, sender_name,
               include_footer=True):
        message = cls(subject, body, creator, sender_email, sender_name,
                      include_footer)
        meta.Session.add(message)
        meta.Session.flush()
        return message


message_recipient_table = Table(
    'message_recipient', meta.data,
    Column('id', Integer, primary_key=True),
    Column('message_id', Integer, ForeignKey('message.id'), nullable=False),
    Column('recipient_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('email_sent', Boolean, default=False),
)


class MessageRecipient(object):

    def __init__(self, message, recipient):
        self.message = message
        self.recipient = recipient

    @classmethod
    def create(cls, message, recipient, notify=False):
        recipient = cls(message, recipient)
        meta.Session.add(recipient)
        meta.Session.flush()
        if notify:
            recipient.notify()
        return recipient

    def notify(self, force_resend=False):

        if (self.recipient.is_email_activated() and
           self.recipient.email_messages):

            from adhocracy.lib import mail
            from adhocracy.lib.message import render_body

            body = render_body(self.message.body, self.recipient,
                               self.message.include_footer)

            mail.to_user(self.recipient,
                         self.message.subject,
                         body,
                         headers={},
                         decorate_body=False,
                         email_from=self.message.sender_email,
                         name_from=self.message.sender_name)
