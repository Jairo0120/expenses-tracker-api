from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, RecurrentBudget, RecurrentBudgetCreate, RecurrentBudgetUpdate
)
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(
    prefix='/recurrent_budgets',
    tags=['Recurrent budgets']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/", response_model=list[RecurrentBudget])
async def read_recurrent_budgets(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select(RecurrentBudget)
        .where(RecurrentBudget.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("/", response_model=RecurrentBudget)
async def create_recurrent_budget(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_budget: RecurrentBudgetCreate
):
    db_recurrent_budget = RecurrentBudget.model_validate(
        recurrent_budget,
        update={"user_id": current_user.id}
    )
    session.add(db_recurrent_budget)
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
        select(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    recurrent_budget_data = recurrent_budget.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    db_recurrent_budget.sqlmodel_update(recurrent_budget_data)
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
        select(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    session.delete(db_recurrent_budget)
    session.commit()
    return {"ok": True}


@router.get("/{recurrent_budget_id}", response_model=RecurrentBudget)
async def read_recurrent_budget(
    recurrent_budget_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_recurrent_budget = session.exec(
        select(RecurrentBudget)
        .where(RecurrentBudget.id == recurrent_budget_id)
        .where(RecurrentBudget.user_id == current_user.id)
    ).first()
    if not db_recurrent_budget:
        raise HTTPException(
            status_code=404,
            detail="Recurrent budget not found"
        )
    return db_recurrent_budget
