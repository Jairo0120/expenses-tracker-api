from fastapi import APIRouter, Depends
from api.dependencies import get_current_active_user, get_session
from sqlmodel import Session
from api.models import UserCreate, User
from api.exceptions import IntegrityException
from sqlalchemy.exc import IntegrityError


router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/sign-up")
async def create_user(*, session: Session = Depends(get_session),
                      user: UserCreate):
    db_user = User.model_validate(user)
    session.add(db_user)
    try:
        session.commit()
    except IntegrityError as ex:
        raise IntegrityException(status_code=400, detail=ex.args,
                                 current_val=user)
    session.refresh(db_user)
    return db_user
