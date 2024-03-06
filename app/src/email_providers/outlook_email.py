import email
import imaplib
import logging
from dataclasses import dataclass
from src.exceptions import (
    UnableRetrieveEmailsException, UnableRetrieveSubjectException,
)
from email.header import decode_header
from datetime import datetime, timedelta
from src.models import EmailMessage


logger = logging.getLogger(__name__)


@dataclass
class OutlookEmail:
    email_address: str
    token: str
    inbox_name: str

    def login(self):
        logger.info('Starting connection to Outlook imap')
        self._server = imaplib.IMAP4_SSL('outlook.office365.com', timeout=3)
        logger.info('Stablishing connection to Outlook Server: %s',
                    self._server)
        self._server.login(self.email_address, self.token)

    def get_unseen_emails(self) -> list[EmailMessage]:
        self._server.select(self.inbox_name, readonly=True)
        messages: list[EmailMessage] = []
        since = (datetime.now() - timedelta(weeks=3)).strftime("%d-%b-%Y")
        status, b_messages = self._server.search(
            None, f'(UNSEEN SINCE {since})'
        )
        if status != 'OK':
            raise UnableRetrieveEmailsException
        for message_id in b_messages[0].split():
            subject, message = self.get_decoded_message(message_id=message_id)
            messages.append(EmailMessage(
                id=message_id.decode('utf-8'),
                message=message,
                subject=subject
            ))
        return messages

    def get_decoded_message(self, message_id) -> tuple:
        status, message = self._server.fetch(message_id, '(RFC822)')
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
            logger.error(ex)
            return (f'Unreadable subject message [{message_id}]', '')
        subject_decoded = (
            subject_to_decode
            if type(subject_to_decode) is str
            else subject_to_decode.decode(encoding)
        )
        return subject_decoded, message_content

    def mark_as_read(self, message_id: str):
        # Set up readonly flag to False to mark as read the emails that are
        # fetched
        self._server.select(self.inbox_name, readonly=False)
        self._server.fetch(message_id, '(RFC822)')
