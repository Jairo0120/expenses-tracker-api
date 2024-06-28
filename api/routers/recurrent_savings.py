from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (
    User, RecurrentSaving, RecurrentSavingCreate, RecurrentSavingUpdate
)
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(
    prefix='/recurrent_savings',
    tags=['Recurrent savings']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("/", response_model=list[RecurrentSaving])
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


@router.post("/", response_model=RecurrentSaving)
async def create_recurrent_saving(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    recurrent_saving: RecurrentSavingCreate
):
    db_recurrent_saving = RecurrentSaving.model_validate(
        recurrent_saving,
        update={"user_id": current_user.id}
    )
    session.add(db_recurrent_saving)
    session.commit()
    session.refresh(db_recurrent_saving)
    return db_recurrent_saving


@router.patch("/{recurrent_saving_id}", response_model=RecurrentSaving)
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


@router.get("/{recurrent_saving_id}", response_model=RecurrentSaving)
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
