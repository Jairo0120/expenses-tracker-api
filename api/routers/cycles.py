from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import (
    User,
    Cycle,
    CycleExpensesStatus,
)
from sqlmodel import Session, select, text
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(prefix="/cycles", tags=["Cycles"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/cycle-status", response_model=CycleExpensesStatus)
async def get_cycle_expenses_status(
    cycle_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Reading cycle status for user {current_user.id}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()
    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    stmt = text(
        f"""
        SELECT 'total_recurrent_expenses' AS concept,
            sum(e.val_expense) AS total
        FROM expense e
        WHERE e.cycle_id = {cycle_db.id} AND
            e.is_recurrent_expense = 1
        UNION
        SELECT 'total_expenses',
            sum(e.val_expense) AS total
        FROM expense e
        WHERE e.cycle_id = {cycle_db.id} AND
            e.is_recurrent_expense = 0
        UNION
        SELECT 'total_incomes',
            sum(i.val_income) AS total
        FROM income i
        WHERE i.cycle_id = {cycle_db.id}
        UNION
        SELECT 'total_savings',
            sum(s.val_saving) AS total
        FROM saving s
        WHERE s.cycle_id = {cycle_db.id}
        """
    )

    totals = dict(session.exec(stmt).all())

    return CycleExpensesStatus(**totals)
