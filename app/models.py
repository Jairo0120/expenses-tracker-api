from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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
    expense_value: float
    description: str
    date_expense: Optional[datetime] = None
