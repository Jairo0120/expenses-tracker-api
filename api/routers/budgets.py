from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import User, Budget, Cycle, Expense, BudgetWithTotal
from sqlmodel import Session, select, col
from sqlalchemy import func, and_
from typing import Annotated


router = APIRouter(prefix="/budgets", tags=["Budgets"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[BudgetWithTotal])
async def read_budgets(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    cycle_id: int | None = None,
    session: Session = Depends(get_session),
):
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)
    cycle_db = session.exec(cycle_stmt).first()
    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    total_spent = func.coalesce(func.sum(Expense.val_expense), 0).label(
        "total_spent"
    )
    stmt = (
        select(Budget, total_spent)
        .where(Budget.cycle_id == cycle_db.id)
        .outerjoin(
            Expense,
            and_(
                col(Expense.budget_id) == col(Budget.id),
                col(Expense.cycle_id) == cycle_db.id,
            ),
        )
        .group_by(col(Budget.id))
        .offset(commons["skip"])
        .limit(commons["limit"])
    )
    rows = session.exec(stmt).all()
    return [
        BudgetWithTotal(
            id=budget.id or 0,
            description=budget.description,
            val_budget=budget.val_budget,
            cycle_id=budget.cycle_id,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
            total_spent=float(spent or 0),
        )
        for budget, spent in rows
    ]


@router.delete("/{budget_id}", status_code=200)
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    budget = session.get(Budget, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    cycle = session.get(Cycle, budget.cycle_id)
    if not cycle or cycle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Budget not found")
    session.delete(budget)
    session.commit()
    return {"ok": True}
