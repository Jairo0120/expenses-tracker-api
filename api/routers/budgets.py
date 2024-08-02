from fastapi import APIRouter, Depends
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


@router.get("/", response_model=list[Budget])
async def read_budgets(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    stmt = (
        select(Budget)
        .join(Cycle, Budget.cycle_id == Cycle.id)
        .where(Cycle.user_id == current_user.id)
        .where(Cycle.is_active == 1)
        .offset(commons["skip"])
        .limit(commons["limit"])
    )
    return session.exec(stmt).all()
