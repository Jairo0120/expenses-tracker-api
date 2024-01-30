from dataclasses import dataclass
from src.exceptions import (
    UnableRetrieveEmailsException, UnableRetrieveSubjectException,
)
from src.models import EmailMessage
from datetime import datetime, timedelta
from email.header import decode_header
import email
import imaplib
import logging


logging.basicConfig(level=logging.INFO)


@dataclass
class OutlookEmail:
    email_address: str
    token: str

    def login(self):
        self.server = imaplib.IMAP4_SSL('imap-mail.outlook.com')
        self.server.login(self.email_address, self.token)

    def get_unseen_emails(self, inbox_name: str) -> list[EmailMessage]:
        self.server.select(inbox_name, readonly=True)
        messages: list[EmailMessage] = []
        since = (datetime.now() - timedelta(weeks=4)).strftime("%d-%b-%Y")
        status, b_messages = self.server.search(
            None, f'(UNSEEN SINCE {since})'
        )
        if status != 'OK':
            raise UnableRetrieveEmailsException
        for message_id in b_messages[0].split():
            subject, message = self.get_decoded_message(message_id=message_id)
            messages.append(EmailMessage(
                id=message_id,
                message=message,
                subject=subject
            ))
        return messages

    def get_decoded_message(self, message_id) -> tuple:
        status, message = self.server.fetch(message_id, '(RFC822)')
        encoding = 'utf-8'
        message_content = ''
        if status != 'OK':
            raise UnableRetrieveSubjectException
        try:
            email_bytes = message[0][1]
            for parte in email.message_from_bytes(email_bytes).walk():
                if parte.get_content_type() == 'text/html':
                    message_content = parte.get_payload(decode=True)
            subject = email.message_from_bytes(email_bytes)['Subject']
            subject_to_decode, _ = decode_header(subject)[0]
            message_content = message_content.decode('utf-8')
        except Exception as ex:
            logging.error(ex)
            return (f'Unreadable subject message [{message_id}]', '')
        subject_decoded = (
            subject_to_decode
            if type(subject_to_decode) is str
            else subject_to_decode.decode(encoding)
        )
        return subject_decoded, message_content

    def get_message_content(self, message_id) -> str:
        ...

    def get_email_content(self, email_id: str) -> str:
        return ''
