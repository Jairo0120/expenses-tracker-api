from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, RecurrentIncome, RecurrentIncomeCreate, RecurrentIncomeUpdate
)
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(
    prefix='/recurrent_incomes',
    tags=['Recurrent incomes']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/", response_model=list[RecurrentIncome])
async def read_recurrent_incomes(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select(RecurrentIncome)
        .where(RecurrentIncome.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("/", response_model=RecurrentIncome)
async def create_recurrent_income(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_income: RecurrentIncomeCreate
):
    db_recurrent_income = RecurrentIncome.model_validate(
        recurrent_income,
        update={"user_id": current_user.id}
    )
    session.add(db_recurrent_income)
    session.commit()
    session.refresh(db_recurrent_income)
    return db_recurrent_income


@router.patch("/{recurrent_income_id}", response_model=RecurrentIncome)
async def update_recurrent_income(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_income_id: int,
    recurrent_income: RecurrentIncomeUpdate
):
    db_recurrent_income = session.exec(
        select(RecurrentIncome)
        .where(RecurrentIncome.id == recurrent_income_id)
        .where(RecurrentIncome.user_id == current_user.id)
    ).first()
    if not db_recurrent_income:
        raise HTTPException(
            status_code=404,
            detail="Recurrent income not found"
        )
    recurrent_income_data = recurrent_income.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    db_recurrent_income.sqlmodel_update(recurrent_income_data)
    session.add(db_recurrent_income)
    session.commit()
    session.refresh(db_recurrent_income)
    return db_recurrent_income


@router.delete("/{recurrent_income_id}", status_code=200)
async def delete_recurrent_income(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_income_id: int
):
    db_recurrent_income = session.exec(
        select(RecurrentIncome)
        .where(RecurrentIncome.id == recurrent_income_id)
        .where(RecurrentIncome.user_id == current_user.id)
    ).first()
    if not db_recurrent_income:
        raise HTTPException(
            status_code=404,
            detail="Recurrent income not found"
        )
    session.delete(db_recurrent_income)
    session.commit()
    return {"ok": True}


@router.get("/{recurrent_income_id}", response_model=RecurrentIncome)
async def read_recurrent_income(
    recurrent_income_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_recurrent_income = session.exec(
        select(RecurrentIncome)
        .where(RecurrentIncome.id == recurrent_income_id)
        .where(RecurrentIncome.user_id == current_user.id)
    ).first()
    if not db_recurrent_income:
        raise HTTPException(
            status_code=404,
            detail="Recurrent income not found"
        )
    return db_recurrent_income
