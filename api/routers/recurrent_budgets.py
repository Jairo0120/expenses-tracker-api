from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    select_live, soft_delete,
    User, RecurrentBudget, RecurrentBudgetCreate, RecurrentBudgetUpdate,
    Budget, Cycle
)
from sqlmodel import Session
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")


router = APIRouter(
    prefix='/recurrent_budgets',
    tags=['Recurrent budgets']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[RecurrentBudget])
async def read_recurrent_budgets(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select_live(RecurrentBudget)
        .where(RecurrentBudget.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
        .order_by(RecurrentBudget.created_at.desc())
    )
    return session.exec(stmt).all()


def find_current_budget(
    session: Session,
    recurrent_budget: RecurrentBudget,
    current_cycle: Cycle | None,
) -> Budget | None:
    """
    The active cycle's copy of a recurrent budget: by its link, or by
    description for copies made before links existed.
    """
    if not current_cycle:
        return None
    return session.exec(
        select_live(Budget)
        .where(Budget.cycle_id == current_cycle.id)
        .where(
            (Budget.recurrent_budget_id == recurrent_budget.id)
            | (
                Budget.recurrent_budget_id.is_(None)
                & (Budget.description == recurrent_budget.description)
            )
        )
    ).first()


@router.post("", response_model=RecurrentBudget, status_code=201)
async def create_recurrent_budget(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_budget: RecurrentBudgetCreate
):
    logger.info(f"Creating recurrent budget for user {current_user.id}")
    db_recurrent_budget = RecurrentBudget.model_validate(
        recurrent_budget,
        update={"user_id": current_user.id}
    )
    session.add(db_recurrent_budget)
    current_cycle = session.exec(
        select_live(Cycle)
        .where(Cycle.is_active)
        .where(Cycle.user_id == current_user.id)
    ).first()
    if current_cycle:
        session.flush()
        budget = Budget(
            description=db_recurrent_budget.description,
            val_budget=db_recurrent_budget.val_budget,
            cycle=current_cycle,
            recurrent_budget_id=db_recurrent_budget.id,
        )
        session.add(budget)
    session.commit()
    session.refresh(db_recurrent_budget)
    return db_recurrent_budget


@router.patch("/{recurrent_budget_id}", response_model=RecurrentBudget)
async def update_recurrent_budget(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_budget_id: int,
    recurrent_budget: RecurrentBudgetUpdate
):
    db_recurrent_budget = session.exec(
        select_live(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    current_cycle = session.exec(
        select_live(Cycle)
        .where(Cycle.is_active)
        .where(Cycle.user_id == current_user.id)
    ).first()
    current_budget = find_current_budget(
        session, db_recurrent_budget, current_cycle
    )
    recurrent_budget_data = recurrent_budget.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    db_recurrent_budget.sqlmodel_update(recurrent_budget_data)
    if current_budget:
        current_budget.sqlmodel_update(recurrent_budget_data)
        session.add(current_budget)
    session.add(db_recurrent_budget)
    session.commit()
    session.refresh(db_recurrent_budget)
    return db_recurrent_budget


@router.delete("/{recurrent_budget_id}", status_code=200)
async def delete_recurrent_budget(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_budget_id: int
):
    db_recurrent_budget = session.exec(
        select_live(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    current_cycle = session.exec(
        select_live(Cycle)
        .where(Cycle.is_active)
        .where(Cycle.user_id == current_user.id)
    ).first()
    current_budget = find_current_budget(
        session, db_recurrent_budget, current_cycle
    )
    soft_delete(session, db_recurrent_budget)
    if current_budget:
        soft_delete(session, current_budget)
    session.commit()
    return {"ok": True}


@router.get("/{recurrent_budget_id}", response_model=RecurrentBudget)
async def read_recurrent_budget(
    recurrent_budget_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_recurrent_budget = session.exec(
        select_live(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    return db_recurrent_budget
