from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import (
    User,
    RecurrentIncome,
    Income,
    Cycle,
    IncomeCreate,
    IncomeUpdate,
)
from sqlmodel import Session, select
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(prefix="/incomes", tags=["Incomes"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[Income])
async def read_incomes(
    commons: CommonsDep,
    cycle_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Reading incomes for user {current_user.id}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)
    cycle_db = session.exec(cycle_stmt).first()
    stmt = (
        select(Income)
        .where(Income.cycle_id == cycle_db.id)
        .order_by(Income.created_at.desc())
        .offset(commons["skip"])
        .limit(commons["limit"])
    )
    return session.exec(stmt).all()


@router.post("", response_model=Income, status_code=201)
async def create_income(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    income: IncomeCreate,
):
    logger.info(f"Creating income: {income}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if income.cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == income.cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()

    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    try:
        if income.create_recurrent_income:
            recurrent_income = RecurrentIncome(
                description=income.description,
                val_income=income.val_income,
                user_id=current_user.id or 0,
            )
            session.add(recurrent_income)
        db_income = Income.model_validate(
            income,
            update={
                "cycle_id": cycle_db.id,
                "is_recurrent_income": income.create_recurrent_income,
            },
        )
        session.add(db_income)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating income: {e}")
        raise HTTPException(status_code=500, detail="Error creating income")
    session.refresh(db_income)
    return db_income


@router.patch("/{income_id}", response_model=Income)
async def update_income(
    income_id: int,
    income: IncomeUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Updating income: {income}")
    stmt = select(Income).where(Income.id == income_id)
    db_income = session.exec(stmt).first()
    if not db_income or db_income.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Income not found")
    if income.cycle_id:
        db_cycle = session.exec(
            select(Cycle)
            .where(Cycle.user_id == current_user.id)
            .where(Cycle.id == income.cycle_id)
        ).first()
        if not db_cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
    try:
        income_data = income.model_dump(exclude_unset=True, exclude_none=True)
        db_income.sqlmodel_update(income_data)
        session.add(db_income)
        session.commit()
    except Exception as e:
        logger.error(f"Error updating income: {e}")
        raise HTTPException(status_code=500, detail="Error updating income")
    session.refresh(db_income)
    return db_income


@router.delete("/{income_id}")
async def delete_income(
    income_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Deleting income {income_id}")
    db_income = session.exec(
        select(Income).where(Income.id == income_id)
    ).first()
    if not db_income or db_income.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Income not found")

    session.delete(db_income)
    session.commit()
    return {"detail": "Income deleted"}
