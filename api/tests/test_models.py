from datetime import datetime
from ..models import (
    ExpenseCreate,
    IncomeCreate,
    SavingCreate,
    SavingOutcomeCreate,
)


def test_movement_dates_default_to_creation_time():
    # The defaults used to be evaluated once at import time, so every record
    # created without a date got the server start time.
    before = datetime.now()
    expense = ExpenseCreate(description="A", val_expense=1)
    income = IncomeCreate(description="B", val_income=1)
    saving = SavingCreate(description="C", val_saving=1)
    outcome = SavingOutcomeCreate(saving="C", val_outcome=1, description="D")

    assert expense.date_expense >= before
    assert income.date_income >= before
    assert saving.date_saving >= before
    assert outcome.date_outcome >= before
