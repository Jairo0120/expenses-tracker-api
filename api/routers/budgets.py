from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import User, Budget, Cycle
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(prefix="/budgets", tags=["Budgets"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[Budget])
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
    stmt = (
        select(Budget)
        .join(Cycle, Budget.cycle_id == cycle_db.id)
        .where(Cycle.user_id == current_user.id)
        .where(Cycle.is_active == 1)
        .offset(commons["skip"])
        .limit(commons["limit"])
    )
    return session.exec(stmt).all()


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
    if cycle.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Budget not found")
    session.delete(budget)
    session.commit()
    return {"ok": True}
