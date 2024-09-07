from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, RecurrentSaving, RecurrentSavingCreate, RecurrentSavingUpdate,
    SavingType, RecurrentSavingPublic
)
from sqlmodel import Session, select
from typing import Annotated
import logging


logger = logging.getLogger("expenses-tracker")
router = APIRouter(
    prefix='/recurrent_savings',
    tags=['Recurrent savings']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[RecurrentSavingPublic])
async def read_recurrent_savings(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select(RecurrentSaving)
        .where(RecurrentSaving.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("", response_model=RecurrentSavingPublic)
async def create_recurrent_saving(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_saving: RecurrentSavingCreate
):
    saving_type = session.exec(
        select(SavingType).where(
            SavingType.description == recurrent_saving.description.capitalize()
        )
    ).first()
    if not saving_type:
        saving_type = SavingType(
            description=recurrent_saving.description.capitalize(),
            user_id=current_user.id or 0
        )
    db_recurrent_saving = RecurrentSaving(
        val_saving=recurrent_saving.val_saving,
        user_id=current_user.id,
        saving_type=saving_type
    )
    session.add(db_recurrent_saving)
    session.commit()
    session.refresh(db_recurrent_saving)
    return db_recurrent_saving


@router.patch("/{recurrent_saving_id}", response_model=RecurrentSavingPublic)
async def update_recurrent_saving(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_saving_id: int,
    recurrent_saving: RecurrentSavingUpdate
):
    db_recurrent_saving = session.exec(
        select(RecurrentSaving)
        .where(RecurrentSaving.id == recurrent_saving_id)
        .where(RecurrentSaving.user_id == current_user.id)
    ).first()
    if not db_recurrent_saving:
        raise HTTPException(
            status_code=404,
            detail="Recurrent saving not found"
        )
    recurrent_saving_data = recurrent_saving.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    if new_description := recurrent_saving_data.get('description'):
        saving_type = session.get(
            SavingType, db_recurrent_saving.saving_type_id
        )
        saving_type.description = new_description
        session.add(saving_type)
    db_recurrent_saving.sqlmodel_update(recurrent_saving_data)
    session.add(db_recurrent_saving)
    session.commit()
    session.refresh(db_recurrent_saving)
    return db_recurrent_saving


@router.delete("/{recurrent_saving_id}", status_code=200)
async def delete_recurrent_saving(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_saving_id: int
):
    db_recurrent_saving = session.exec(
        select(RecurrentSaving)
        .where(RecurrentSaving.id == recurrent_saving_id)
        .where(RecurrentSaving.user_id == current_user.id)
    ).first()
    if not db_recurrent_saving:
        raise HTTPException(
            status_code=404,
            detail="Recurrent saving not found"
        )
    session.delete(db_recurrent_saving)
    session.commit()
    return {"ok": True}


@router.get("/{recurrent_saving_id}", response_model=RecurrentSavingPublic)
async def read_recurrent_saving(
    recurrent_saving_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_recurrent_saving = session.exec(
        select(RecurrentSaving)
        .where(RecurrentSaving.id == recurrent_saving_id)
        .where(RecurrentSaving.user_id == current_user.id)
    ).first()
    if not db_recurrent_saving:
        raise HTTPException(
            status_code=404,
            detail="Recurrent saving not found"
        )
    return db_recurrent_saving
