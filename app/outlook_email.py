from dataclasses import dataclass
from models import EmailSubject, Expense
from datetime import datetime
from email.header import decode_header
import email
import imaplib


@dataclass
class OutlookEmail:
    email_address: str
    token: str

    def login(self):
        self.server = imaplib.IMAP4_SSL('imap-mail.outlook.com')
        self.server.login(self.email_address, self.token)

    def get_unseen_emails(self) -> list[EmailSubject]:
        self.server.select('inbox')
        messages: list[EmailSubject] = []
        status, b_messages = self.server.search(None, 'UnSeen')
        print(status)
        for message_id in b_messages[0].split():
            status, message = self.server.fetch(message_id, '(RFC822)')
            subject = email.message_from_bytes(message[0][1])['Subject']
            subject_to_decode, encoding = decode_header(subject)[0]
            subject_decoded = (
                subject_to_decode
                if type(subject_to_decode) is str
                else subject_to_decode.decode(encoding)
            )
            print(subject_decoded)
            # print(status, subject_decoded)
            # messages.append(EmailSubject(
            #     id=message_id,
            #     subject=subject
            # ))
        return messages

    def get_email_content(self, email_id: str) -> str:
        return ''

    def get_clean_expense(self, email_content: str) -> Expense:
        return Expense(datetime.now(), 2, '')
