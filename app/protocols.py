from abc import abstractmethod
from typing import Protocol

from models import EmailMessage, Expense


class EmailReceiver(Protocol):

    @abstractmethod
    def get_unseen_emails(self, inbox_name: str) -> list[EmailMessage]:
        ...

    @abstractmethod
    def get_email_content(self, email_id: str) -> str:
        ...

    @abstractmethod
    def get_clean_expense(self, email_content: str) -> Expense:
        ...
