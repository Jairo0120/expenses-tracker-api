from dataclasses import dataclass
from datetime import datetime


@dataclass
class EmailSubject:
    id: str
    subject: str


@dataclass
class EmailMessage:
    id: str
    subject: str
    message: str


@dataclass
class Expense:
    date_expense: datetime
    expense_value: float
    description: str
