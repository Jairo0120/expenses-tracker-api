from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, RecurrentExpense, RecurrentExpenseCreate, RecurrentExpenseUpdate
)
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(
    prefix='/recurrent_expenses',
    tags=['Recurrent expenses']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/", response_model=list[RecurrentExpense])
async def read_recurrent_expenses(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select(RecurrentExpense)
        .where(RecurrentExpense.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("/", response_model=RecurrentExpense)
async def create_recurrent_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_expense: RecurrentExpenseCreate
):
    db_recurrent_expense = RecurrentExpense.model_validate(
        recurrent_expense,
        update={"user_id": current_user.id}
    )
    session.add(db_recurrent_expense)
    session.commit()
    session.refresh(db_recurrent_expense)
    return db_recurrent_expense


@router.patch("/{recurrent_expense_id}", response_model=RecurrentExpense)
async def update_recurrent_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_expense_id: int,
    recurrent_expense: RecurrentExpenseUpdate
):
    db_recurrent_expense = session.exec(
        select(RecurrentExpense)
        .where(RecurrentExpense.id == recurrent_expense_id)
        .where(RecurrentExpense.user_id == current_user.id)
    ).first()
    if not db_recurrent_expense:
        raise HTTPException(
            status_code=404,
            detail="Recurrent expense not found"
        )
    recurrent_expense_data = recurrent_expense.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    db_recurrent_expense.sqlmodel_update(recurrent_expense_data)
    session.add(db_recurrent_expense)
    session.commit()
    session.refresh(db_recurrent_expense)
    return db_recurrent_expense


@router.delete("/{recurrent_expense_id}", status_code=200)
async def delete_recurrent_expense(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_expense_id: int
):
    db_recurrent_expense = session.exec(
        select(RecurrentExpense)
        .where(RecurrentExpense.id == recurrent_expense_id)
        .where(RecurrentExpense.user_id == current_user.id)
    ).first()
    if not db_recurrent_expense:
        raise HTTPException(
            status_code=404,
            detail="Recurrent expense not found"
        )
    session.delete(db_recurrent_expense)
    session.commit()
    return {"ok": True}


@router.get("/{recurrent_expense_id}", response_model=RecurrentExpense)
async def read_recurrent_expense(
    recurrent_expense_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_recurrent_expense = session.exec(
        select(RecurrentExpense)
        .where(RecurrentExpense.id == recurrent_expense_id)
        .where(RecurrentExpense.user_id == current_user.id)
    ).first()
    if not db_recurrent_expense:
        raise HTTPException(
            status_code=404,
            detail="Recurrent expense not found"
        )
    return db_recurrent_expense
