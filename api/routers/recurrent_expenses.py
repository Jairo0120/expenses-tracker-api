from fastapi import APIRouter, Depends
from api.dependencies import (get_current_active_user, get_session,
                              common_parameters)
from api.models import User, RecurrentExpense, RecurrentExpenseCreate
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
