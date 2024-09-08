from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user,
    get_session,
    common_parameters,
)
from api.models import (
    User,
    RecurrentSaving,
    Saving,
    Cycle,
    SavingCreate,
    SavingUpdate,
    SavingPublic,
    SavingType,
    SavingOutcomeCreate,
    SavingMovementEnum,
)
from sqlmodel import Session, select
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(prefix="/savings", tags=["Savings"])
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[SavingPublic])
async def read_savings(
    commons: CommonsDep,
    cycle_id: int | None = None,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Reading savings for user {current_user.id}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)
    cycle_db = session.exec(cycle_stmt).first()
    stmt = (
        select(Saving)
        .where(Saving.cycle_id == cycle_db.id)
        .where(Saving.movement_type == SavingMovementEnum.income)
        .order_by(Saving.created_at.desc())
        .offset(commons["skip"])
        .limit(commons["limit"])
    )
    return session.exec(stmt).all()


@router.post("", response_model=SavingPublic, status_code=201)
async def create_saving(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    saving: SavingCreate,
):
    logger.info(f"Creating saving: {saving}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if saving.cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == saving.cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()

    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    try:
        saving_type = session.exec(
            select(SavingType).where(
                SavingType.description == saving.description.capitalize()
            )
        ).first()
        if not saving_type:
            saving_type = SavingType(
                description=saving.description.capitalize(),
                user_id=current_user.id or 0,
            )
        if saving.create_recurrent_saving:
            recurrent_saving = RecurrentSaving(
                val_saving=saving.val_saving,
                user_id=current_user.id or 0,
                saving_type=saving_type,
            )
            session.add(recurrent_saving)
        db_saving = Saving(
            val_saving=saving.val_saving,
            date_saving=saving.date_saving,
            cycle=cycle_db,
            is_recurrent_saving=saving.create_recurrent_saving,
            saving_type=saving_type,
        )
        session.add(db_saving)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating saving: {e}")
        raise HTTPException(status_code=500, detail="Error creating saving")
    session.refresh(db_saving)
    return db_saving


@router.post("/saving-outcome", response_model=SavingPublic, status_code=201)
async def create_saving_outcome(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    saving_outcome: SavingOutcomeCreate,
):
    logger.info(f"Creating saving outcome: {saving_outcome}")
    cycle_stmt = select(Cycle).where(Cycle.user_id == current_user.id)
    if saving_outcome.cycle_id:
        cycle_stmt = cycle_stmt.where(Cycle.id == saving_outcome.cycle_id)
    else:
        cycle_stmt = cycle_stmt.where(Cycle.is_active == 1)

    cycle_db = session.exec(cycle_stmt).first()

    if not cycle_db:
        raise HTTPException(status_code=404, detail="Cycle not found")

    saving_type = session.exec(
        select(SavingType).where(
            SavingType.description == saving_outcome.saving.capitalize()
        )
    ).first()
    if not saving_type:
        raise HTTPException(status_code=404, detail="Saving not found")

    try:
        db_saving = Saving(
            val_saving=saving_outcome.val_outcome,
            date_saving=saving_outcome.date_outcome,
            cycle=cycle_db,
            is_recurrent_saving=False,
            saving_type=saving_type,
            movement_type=SavingMovementEnum.outcome,
            movement_description=saving_outcome.description,
        )
        session.add(db_saving)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating saving outcome: {e}")
        raise HTTPException(
            status_code=500, detail="Error creating saving outcome"
        )
    session.refresh(db_saving)
    return db_saving


@router.patch("/{saving_id}", response_model=SavingPublic)
async def update_saving(
    saving_id: int,
    saving: SavingUpdate,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Updating saving: {saving}")
    db_saving = session.get(Saving, saving_id)
    if not db_saving or db_saving.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saving not found")
    if saving.cycle_id:
        db_cycle = session.exec(
            select(Cycle)
            .where(Cycle.user_id == current_user.id)
            .where(Cycle.id == saving.cycle_id)
        ).first()
        if not db_cycle:
            raise HTTPException(status_code=404, detail="Cycle not found")
    try:
        saving_data = saving.model_dump(exclude_unset=True, exclude_none=True)
        if new_description := saving_data.get("description"):
            saving_type = session.get(SavingType, db_saving.saving_type_id)
            saving_type.description = new_description
            session.add(saving_type)
        saving_data.pop("description", None)
        db_saving.sqlmodel_update(saving_data)
        session.add(db_saving)
        session.commit()
    except Exception as e:
        logger.error(f"Error updating saving: {e}")
        raise HTTPException(status_code=500, detail="Error updating saving")
    session.refresh(db_saving)
    return db_saving


@router.delete("/{saving_id}")
async def delete_saving(
    saving_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    logger.info(f"Deleting saving {saving_id}")
    db_saving = session.exec(
        select(Saving).where(Saving.id == saving_id)
    ).first()
    if not db_saving or db_saving.cycle.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Saving not found")

    session.delete(db_saving)
    session.commit()
    return {"detail": "Saving deleted"}
