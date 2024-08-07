from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import (
    get_current_active_user, get_session, common_parameters
)
from api.models import (User, Category, CategoryBase)
from sqlmodel import Session, select
from typing import Annotated


router = APIRouter(
    prefix='/categories',
    tags=['Categories']
)
CommonsDep = Annotated[dict, Depends(common_parameters)]


@router.get("", response_model=list[Category])
async def read_categories(
    commons: CommonsDep,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    stmt = (
        select(Category)
        .where(Category.user_id == current_user.id)
        .offset(commons['skip'])
        .limit(commons['limit'])
    )
    return session.exec(stmt).all()


@router.post("", response_model=Category)
async def create_category(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    category: CategoryBase
):
    db_category = Category.model_validate(
        category,
        update={"user_id": current_user.id}
    )
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@router.patch("/{category_id}", response_model=Category)
async def update_category(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    category_id: int,
    category: CategoryBase
):
    db_category = session.exec(
        select(Category)
        .where(Category.id == category_id)
        .where(Category.user_id == current_user.id)
    ).first()
    if not db_category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    category_data = category.model_dump(
        exclude_unset=True,
        exclude_none=True
    )
    db_category.sqlmodel_update(category_data)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=200)
async def delete_category(
    *,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
    category_id: int
):
    db_category = session.exec(
        select(Category)
        .where(Category.id == category_id)
        .where(Category.user_id == current_user.id)
    ).first()
    if not db_category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    session.delete(db_category)
    session.commit()
    return {"ok": True}


@router.get("/{category_id}", response_model=Category)
async def read_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    db_category = session.exec(
        select(Category)
        .where(Category.id == category_id)
        .where(Category.user_id == current_user.id)
    ).first()
    if not db_category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )
    return db_category
