import logging
from ..models import Expense


logger = logging.getLogger(__name__)


class ExpensesTrackerAPI:

    def login(self):
        ...

    def add_expense(self, expenses: list[Expense]) -> bool:
        logger.info("Expenses to send %s", expenses)
        return True
