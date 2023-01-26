from dataclasses import dataclass
from exceptions import (
    UnableRetrieveEmailsException, UnableRetrieveSubjectException
)
from models import EmailSubject, Expense
from datetime import datetime
from email.header import decode_header
import email
import imaplib
import logging


logging.basicConfig(level = logging.INFO)


@dataclass
class OutlookEmail:
    email_address: str
    token: str

    def login(self):
        self.server = imaplib.IMAP4_SSL('imap-mail.outlook.com')
        self.server.login(self.email_address, self.token)

    def get_unseen_emails(self, inbox_name: str) -> list[EmailSubject]:
        self.server.select(inbox_name, readonly=True)
        messages: list[EmailSubject] = []
        status, b_messages = self.server.search(None, 'UnSeen')
        if status != 'OK':
            raise UnableRetrieveEmailsException
        for message_id in b_messages[0].split():
            messages.append(EmailSubject(
                id=message_id,
                subject=self.get_clean_subject(message_id=message_id)
            ))
        return messages

    def get_clean_subject(self, message_id) -> str:
        status, message = self.server.fetch(message_id, '(RFC822)')
        encoding = 'utf-8'
        if status != 'OK':
            raise UnableRetrieveSubjectException
        try:
            subject = email.message_from_bytes(message[0][1])['Subject']
            subject_to_decode, encoding = decode_header(subject)[0]
        except Exception as ex:
            logging.error(ex)
            return f'Unreadable message [{message_id}]'
        subject_decoded = (
            subject_to_decode
            if type(subject_to_decode) is str
            else subject_to_decode.decode(encoding)
        )
        logging.info(subject_decoded)
        return subject_decoded

    def get_email_content(self, email_id: str) -> str:
        return ''

    def get_clean_expense(self, email_content: str) -> Expense:
        return Expense(datetime.now(), 2, '')
