from abc import abstractmethod
from typing import Protocol

from src.models import EmailMessage, Expense


class EmailReceiver(Protocol):

    @abstractmethod
    def get_unseen_emails(self, inbox_name: str) -> list[EmailMessage]:
        ...

    @abstractmethod
    def get_decoded_message(self, email_id: str) -> str:
        ...

    @abstractmethod
    def get_clean_html_body(self, email_content: str) -> Expense:
        ...
