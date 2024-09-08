from api import config
from api.models import (
    Cycle, User, RecurrentIncome, Income, RecurrentExpense, Expense,
    SourceEnum, RecurrentSaving, Saving, Budget, RecurrentBudget
)
from sqlmodel import Session, create_engine, select, update
from datetime import date, datetime
from logging.config import dictConfig
from api.log_config import LogConfig
from api import utils
import logging


dictConfig(LogConfig().model_dump())
logger = logging.getLogger("expenses-tracker")
db_session = None


def get_session() -> Session:
    global db_session
    if db_session:
        return db_session
    sqlite_url = f"sqlite:///{config.Settings().sqlite_database_url}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
    with Session(engine) as session:
        db_session = session
        return db_session


def create_cycles(session: Session, user_id: int = 0):
    """
    Function that iterates over all (or one) active users and start creating
    new cycles (if necessary) and disable old cycles
    """
    statement = select(User).where(User.is_active == 1)
    if user_id:
        statement = statement.where(User.id == user_id)
    for user in session.exec(statement).all():
        current_cycle = session.exec(
            select(Cycle)
            .where(Cycle.user_id == user.id)
            .where(Cycle.end_date >= datetime.now())
        ).first()
        if current_cycle:
            continue
        cycle = Cycle(
            description=datetime.now().strftime('%B, %Y'),
            start_date=utils.get_first_day_month(date.today()),
            end_date=utils.get_last_day_month(date.today()),
            user_id=user.id or 0
        )
        session.exec(
            update(Cycle)
            .where(Cycle.user_id == user.id)
            .where(Cycle.is_active == 1)
            .values(is_active=0)
        )
        session.add(cycle)
        session.commit()


def create_recurrent_incomes(session: Session):
    """
    Function intended to create all of the recurrent incomes configured
    in the recurrentIncome table
    """
    statement = (
        select(Cycle)
        .where(Cycle.is_active == 1)
        .where(Cycle.is_recurrent_incomes_created == 0)
    )
    for cycle in session.exec(statement).all():
        recurrent_incomes_stmt = (
            select(RecurrentIncome)
            .where(RecurrentIncome.enabled == 1)
            .where(RecurrentIncome.user_id == cycle.user_id)
        )
        for re_income in session.exec(recurrent_incomes_stmt):
            income = Income(
                description=re_income.description,
                val_income=re_income.val_income,
                date_income=datetime.now(),
                is_recurrent_income=True,
                cycle_id=cycle.id or 0
            )
            session.add(income)
        cycle.is_recurrent_incomes_created = True
        session.add(cycle)
        session.commit()


def create_recurrent_expenses(session: Session):
    """
    Function intended to create all of the recurrent expenses configured
    in the recurrentExpense table
    """
    statement = (
        select(Cycle)
        .where(Cycle.is_active == 1)
        .where(Cycle.is_recurrent_expenses_created == 0)
    )
    for cycle in session.exec(statement).all():
        recurrent_expenses_stmt = (
            select(RecurrentExpense)
            .where(RecurrentExpense.enabled == 1)
            .where(RecurrentExpense.user_id == cycle.user_id)
        )
        for re_expense in session.exec(recurrent_expenses_stmt):
            expense = Expense(
                description=re_expense.description,
                val_expense=re_expense.val_expense,
                date_expense=datetime.now(),
                is_recurrent_expense=True,
                source=SourceEnum.recurrent,
                categories=re_expense.categories,
                cycle_id=cycle.id or 0
            )
            session.add(expense)
        cycle.is_recurrent_expenses_created = True
        session.add(cycle)
        session.commit()


def create_recurrent_savings(session: Session):
    """
    Function intended to create all of the recurrent savings configured
    in the recurrentSaving table
    """
    statement = (
        select(Cycle)
        .where(Cycle.is_active == 1)
        .where(Cycle.is_recurrent_savings_created == 0)
    )
    for cycle in session.exec(statement).all():
        recurrent_savings_stmt = (
            select(RecurrentSaving)
            .where(RecurrentSaving.enabled == 1)
            .where(RecurrentSaving.user_id == cycle.user_id)
        )
        for re_saving in session.exec(recurrent_savings_stmt):
            saving = Saving(
                val_saving=re_saving.val_saving,
                date_saving=datetime.now(),
                is_recurrent_saving=True,
                cycle_id=cycle.id or 0,
                saving_type_id=re_saving.saving_type_id
            )
            session.add(saving)
        cycle.is_recurrent_savings_created = True
        session.add(cycle)
        session.commit()


def create_recurrent_budgets(session: Session):
    """
    Function intended to create all of the recurrent budgets configured
    in the recurrentBudget table
    """
    statement = (
        select(Cycle)
        .where(Cycle.is_active == 1)
        .where(Cycle.is_recurrent_budgets_created == 0)
    )
    for cycle in session.exec(statement).all():
        recurrent_budgets_stmt = (
            select(RecurrentBudget)
            .where(RecurrentBudget.is_enabled == 1)
            .where(RecurrentBudget.user_id == cycle.user_id)
        )
        for re_budget in session.exec(recurrent_budgets_stmt):
            budget = Budget(
                description=re_budget.description,
                val_budget=re_budget.val_budget,
                cycle_id=cycle.id or 0
            )
            session.add(budget)
        cycle.is_recurrent_budgets_created = True
        session.add(cycle)
        session.commit()


def lambda_handler(event, context):
    logger.info("Creating recurrent objects...")
    session = get_session()
    create_cycles(session)
    create_recurrent_incomes(session)
    create_recurrent_expenses(session)
    create_recurrent_savings(session)
    create_recurrent_budgets(session)


if __name__ == '__main__':
    session = get_session()
    create_cycles(session)
    create_recurrent_incomes(session)
    create_recurrent_expenses(session)
    create_recurrent_savings(session)
    create_recurrent_budgets(session)
