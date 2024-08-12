from sqlmodel import Session, select
from datetime import datetime
from freezegun import freeze_time
from .. import tasks
from ..models import (
    Cycle, Income, RecurrentIncome, RecurrentExpense, RecurrentSaving,
    Expense, Saving, RecurrentBudget, Budget
)
import pytest


@pytest.fixture(name='active_cycle')
def active_cycle_fixture(session: Session, users):
    active_cycle = Cycle(
        description=datetime.now().strftime('%B, %Y'),
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        user_id=1
    )
    session.add(active_cycle)
    session.commit()


@pytest.fixture(name='inactive_cycle')
def inactive_cycle_fixture(session: Session, users):
    inactive_cycle = Cycle(
        description=datetime.now().strftime('%B, %Y'),
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        user_id=1,
        is_active=False
    )
    session.add(inactive_cycle)
    session.commit()


@pytest.fixture(name='recurrent_incomes')
def recurrent_incomes_fixture(session: Session, users):
    recurrent_income_1 = RecurrentIncome(
        description='Income 1',
        val_income=1000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    recurrent_income_2 = RecurrentIncome(
        description='Income 2',
        val_income=40000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(recurrent_income_1)
    session.add(recurrent_income_2)
    session.commit()


@pytest.fixture(name='recurrent_expenses')
def recurrent_expenses_fixture(session: Session, users):
    recurrent_expense_1 = RecurrentExpense(
        description='expense 1',
        val_expense=1000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    recurrent_expense_2 = RecurrentExpense(
        description='expense 2',
        val_expense=40000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(recurrent_expense_1)
    session.add(recurrent_expense_2)
    session.commit()


@pytest.fixture(name='recurrent_savings')
def recurrent_savings_fixture(session: Session, users):
    recurrent_saving_1 = RecurrentSaving(
        description='saving 1',
        val_saving=1000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    recurrent_saving_2 = RecurrentSaving(
        description='saving 2',
        val_saving=40000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(recurrent_saving_1)
    session.add(recurrent_saving_2)
    session.commit()


@pytest.fixture(name="recurrent_budgets")
def recurrent_budgets_fixture(session: Session, users):
    recurrent_budget_1 = RecurrentBudget(
        description='budget 1',
        val_budget=600000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    recurrent_budget_2 = RecurrentBudget(
        description='budget 2',
        val_budget=1000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(recurrent_budget_1)
    session.add(recurrent_budget_2)
    session.commit()


def test_create_cycles_user_active(session: Session, users):
    tasks.create_cycles(session)
    cycles = session.exec(select(Cycle)).all()
    assert len(cycles) == 1
    assert cycles[0].user_id == 1


def test_create_cycle_given_active_user(session: Session, users):
    tasks.create_cycles(session, 3)
    cycles = session.exec(select(Cycle)).all()
    assert len(cycles) == 1


@freeze_time("2024-02-01")
def test_create_cycle_with_expired_cycle(session: Session, active_cycle):
    tasks.create_cycles(session)
    cycles = session.exec(select(Cycle).order_by(Cycle.id.asc())).all()
    assert len(cycles) == 2
    assert cycles[0].is_active is False


@freeze_time("2024-01-20")
def test_create_cycles_already_active_cycle(
    session: Session, users, active_cycle
):
    tasks.create_cycles(session)
    new_cycles = session.exec(select(Cycle)).all()
    assert len(new_cycles) == 1


def test_create_recurrent_incomes_active_cycle(
        session: Session, active_cycle, recurrent_incomes
):
    tasks.create_recurrent_incomes(session)
    incomes = session.exec(select(Income)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(incomes) == 2
    assert cycle.is_recurrent_incomes_created == 1


def test_create_recurrent_incomes_inactive_cycle(
        session: Session, inactive_cycle, recurrent_incomes
):
    tasks.create_recurrent_incomes(session)
    incomes = session.exec(select(Income)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(incomes) == 0
    assert cycle.is_recurrent_incomes_created == 0


def test_create_recurrent_expenses_active_cycle(
        session: Session, active_cycle, recurrent_expenses
):
    tasks.create_recurrent_expenses(session)
    expenses = session.exec(select(Expense)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(expenses) == 2
    assert cycle.is_recurrent_expenses_created == 1


def test_create_recurrent_expenses_inactive_cycle(
        session: Session, inactive_cycle, recurrent_expenses
):
    tasks.create_recurrent_expenses(session)
    expenses = session.exec(select(Expense)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(expenses) == 0
    assert cycle.is_recurrent_expenses_created == 0


def test_create_recurrent_savings_active_cycle(
        session: Session, active_cycle, recurrent_savings
):
    tasks.create_recurrent_savings(session)
    savings = session.exec(select(Saving)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(savings) == 2
    assert cycle.is_recurrent_savings_created == 1


def test_create_recurrent_savings_inactive_cycle(
        session: Session, inactive_cycle, recurrent_savings
):
    tasks.create_recurrent_savings(session)
    savings = session.exec(select(Saving)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(savings) == 0
    assert cycle.is_recurrent_savings_created == 0


def test_create_recurrent_budgets_active_cycle(
        session: Session, active_cycle, recurrent_budgets
):
    tasks.create_recurrent_budgets(session)
    budgets = session.exec(select(Budget)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(budgets) == 2
    assert cycle.is_recurrent_budgets_created == 1


def test_create_recurrent_budgets_inactive_cycle(
        session: Session, inactive_cycle, recurrent_budgets
):
    tasks.create_recurrent_budgets(session)
    budgets = session.exec(select(Budget)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(budgets) == 0
    assert cycle.is_recurrent_budgets_created == 0
