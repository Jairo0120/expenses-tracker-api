from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ExpenseSource(Enum):
    BANCOLOMBIA_PSE = "Bancolombia PSE"
    ITAU_CR = "Itaú Tarjeta de Crédito"


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
    expense_source: ExpenseSource
    date_expense: Optional[datetime] = None
