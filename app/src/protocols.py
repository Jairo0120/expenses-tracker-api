from abc import abstractmethod
from typing import Protocol
from src.models import EmailMessage


class EmailReceiver(Protocol):

    @abstractmethod
    def login(self):
        ...

    @abstractmethod
    def get_unseen_emails(self) -> list[EmailMessage]:
        ...

    @abstractmethod
    def mark_as_read(self, message_id: str) -> str:
        ...
