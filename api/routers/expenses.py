from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import (
    select_live, soft_delete,
    User,
    Expense,
    Cycle,
    ExpenseCreate,
    Budget,
    ExpensePublic,
    ExpenseUpdate,
    RecurrentExpense,
)
from sqlmodel import Session
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(prefix="/expenses", tags=["Expenses"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[ExpensePublic])
async def read_expenses(
    commons: CommonsDep,
    cycle_id: int | None = None,
    budget_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Reading expenses for user {current_user.id}")
    cycle_stmt = select_live(Cycle).where(Cycle.user_id == current_user.id)
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()
    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    if budget_id == 0:
        stmt = (
            select_live(Expense)
            .where(Expense.cycle_id == cycle_db.id)
            .where(Expense.budget_id.is_(None))
            .order_by(Expense.date_expense.desc())
            .offset(commons["skip"])
            .limit(commons["limit"])
        )
    elif budget_id:
        budget_stmt = (
            select_live(Budget)
            .where(Budget.cycle_id == cycle_db.id)
            .where(Budget.id == budget_id)
        )
        budget_db = session.exec(budget_stmt).first()
        if not budget_db:
            raise HTTPException(status_code=404, detail="Budget not found")
        stmt = (
            select_live(Expense)
            .where(Expense.cycle_id == cycle_db.id)
            .where(Expense.budget_id == budget_db.id)
            .order_by(Expense.date_expense.desc())
            .offset(commons["skip"])
            .limit(commons["limit"])
        )
    else:
        stmt = (
            select_live(Expense)
            .where(Expense.cycle_id == cycle_db.id)
            .order_by(Expense.date_expense.desc())
            .offset(commons["skip"])
            .limit(commons["limit"])
        )
    return session.exec(stmt).all()


@router.post("", response_model=ExpensePublic, status_code=201)
async def create_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    expense: ExpenseCreate,
):
    logger.info(f"Creating expense: {expense}")
    # 0 is how the list filter names "no budget"; never store it as an id.
    if expense.budget_id == 0:
        expense.budget_id = None
    cycle_stmt = select_live(Cycle).where(Cycle.user_id == current_user.id)
    if expense.cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == expense.cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()

    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    if expense.budget_id:
        budget_stmt = (
            select_live(Budget)
            .where(Budget.id == expense.budget_id)
            .where(Budget.cycle_id == cycle_db.id)
        )
        if not session.exec(budget_stmt).first():
            raise HTTPException(status_code=404, detail="Budget not found")

    try:
        recurrent_expense_id = None
        if expense.create_recurrent_expense:
            recurrent_expense = RecurrentExpense(
                description=expense.description,
                val_expense=expense.val_expense,
                user_id=current_user.id or 0,
            )
            session.add(recurrent_expense)
            # This expense is the recurrent one's copy for this cycle.
            session.flush()
            recurrent_expense_id = recurrent_expense.id
        db_expense = Expense.model_validate(
            expense,
            update={
                "user_id": current_user.id,
                "cycle_id": cycle_db.id,
                "is_recurrent_expense": expense.create_recurrent_expense,
                "recurrent_expense_id": recurrent_expense_id,
            },
        )
        session.add(db_expense)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        raise HTTPException(status_code=500, detail="Error creating expense")

    session.refresh(db_expense)
    return db_expense


@router.patch("/{expense_id}", response_model=ExpensePublic)
def update_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    expense_id: int,
    expense: ExpenseUpdate,
):
    logger.info(f"Updating expense {expense_id}: {expense}")
    db_expense = session.exec(
        select_live(Expense).where(Expense.id == expense_id)
    ).first()
    if not db_expense or db_expense.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense.cycle_id:
        db_cycle = session.exec(
            select_live(Cycle)
            .where(Cycle.user_id == current_user.id)
            .where(Cycle.id == expense.cycle_id)
        ).first()
        if not db_cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")

    cycle_changes = bool(
        expense.cycle_id and expense.cycle_id != db_expense.cycle_id
    )
    if expense.budget_id and not cycle_changes:
        budget_stmt = (
            select_live(Budget)
            .where(Budget.id == expense.budget_id)
            .where(Budget.cycle_id == db_expense.cycle_id)
        )
        if not session.exec(budget_stmt).first():
            raise HTTPException(status_code=404, detail="Budget not found")
    expense_data = expense.model_dump(exclude_unset=True, exclude_none=True)
    # An explicit null (or 0, the "no budget" filter value) clears the budget.
    if "budget_id" in expense.model_fields_set and not expense.budget_id:
        expense_data["budget_id"] = None
    # If the cycle has been updated, we need to remove the budget as this
    # could lead to data inconsistency
    if cycle_changes:
        expense_data["budget_id"] = None
    db_expense.sqlmodel_update(expense_data)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense


@router.delete("/{expense_id}")
def delete_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    expense_id: int,
):
    logger.info(f"Deleting expense {expense_id}")
    db_expense = session.exec(
        select_live(Expense).where(Expense.id == expense_id)
    ).first()
    if not db_expense or db_expense.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Expense not found")

    soft_delete(session, db_expense)
    session.commit()
    return {"detail": "Expense deleted"}
