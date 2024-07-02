from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, Expense, Cycle, ExpenseCreate, Budget, ExpensePublic, ExpenseUpdate
)
from sqlmodel import Session, select
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(
    prefix='/expenses',
    tags=['Expenses']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/", response_model=list[ExpensePublic])
async def read_expenses(
    commons: CommonsDep,
    cycle_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    cycle_stmt = (
        select(Cycle)
        .where(Cycle.user_id == current_user.id)
    )
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()
    if not cycle_db:
        raise HTTPException(status_code=404, detail='Cycle not found')

    stmt = (
        select(Expense)
        .where(Expense.cycle_id == cycle_db.id)
        .order_by(Expense.date_expense.desc())
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("/", response_model=ExpensePublic)
async def create_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    expense: ExpenseCreate
):
    logger.info(f"Creating expense: {expense}")
    cycle_stmt = (
        select(Cycle)
        .where(Cycle.user_id == current_user.id)
    )
    if expense.cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == expense.cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()

    if not cycle_db:
        raise HTTPException(status_code=404, detail='Cycle not found')

    if expense.budget_id:
        budget_stmt = (
            select(Budget)
            .where(Budget.id == expense.budget_id)
            .where(Budget.cycle_id == cycle_db.id)
        )
        if not session.exec(budget_stmt).first():
            raise HTTPException(status_code=404, detail='Budget not found')

    try:
        db_expense = Expense.model_validate(
            expense,
            update={"user_id": current_user.id, "cycle_id": cycle_db.id}
        )
        session.add(db_expense)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        raise HTTPException(status_code=500, detail='Error creating expense')

    session.refresh(db_expense)
    return db_expense


@router.patch("/{expense_id}", response_model=ExpensePublic)
def update_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    expense_id: int,
    expense: ExpenseUpdate
):
    logger.info(f"Updating expense {expense_id}: {expense}")
    db_expense = session.exec(
        select(Expense)
        .where(Expense.id == expense_id)
    ).first()
    if not db_expense or db_expense.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail='Expense not found')

    if expense.cycle_id:
        db_cycle = session.exec(
            select(Cycle)
            .where(Cycle.user_id == current_user.id)
            .where(Cycle.id == expense.cycle_id)
        ).first()
        if not db_cycle:
            raise HTTPException(status_code=404, detail='Cycle not found')

    if (expense.budget_id
       and expense.cycle_id
       and expense.cycle_id == db_expense.cycle_id):
        budget_stmt = (
            select(Budget)
            .where(Budget.id == expense.budget_id)
            .where(Budget.cycle_id == db_expense.cycle_id)
        )
        if not session.exec(budget_stmt).first():
            raise HTTPException(status_code=404, detail='Budget not found')
    expense_data = expense.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    # If the cycle has been updated, we need to remove the budget as this
    # could lead to data inconsistency
    if expense.cycle_id and expense.cycle_id != db_expense.cycle_id:
        expense_data['budget_id'] = None
    db_expense.sqlmodel_update(expense_data)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense
