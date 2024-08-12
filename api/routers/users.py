from fastapi import APIRouter, Depends, HTTPException
from api.dependencies import get_current_active_user, get_session
from sqlmodel import Session, select
from api.models import UserCreate, User, Cycle
from api.exceptions import IntegrityException
from api.tasks import create_cycles
from sqlalchemy.exc import IntegrityError
import logging


logger = logging.getLogger("expenses-tracker")


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/sign-up")
async def create_user(
    *, session: Session = Depends(get_session), user: UserCreate
):
    db_user = User.model_validate(user)
    existing_user = session.exec(
        select(User)
        .where(User.email == db_user.email)
        .where(User.auth0_id == db_user.auth0_id)
    ).first()
    if not existing_user:
        logger.info(f"Creating user: {user}")
        try:
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            new_user = db_user.model_copy()
            logger.info(f"User created: {new_user}. Creating cycles")
            # create_cycles(session, db_user.id)
            return new_user
        except IntegrityError as ex:
            raise IntegrityException(
                status_code=400, detail=ex.args, current_val=user
            )
        except Exception as ex:
            logger.error(f"Error creating user: {ex}")
            raise HTTPException(status_code=500, detail="Error creating user")
    else:
        logger.info(f"User already exists: {existing_user}")
        existing_cycle = session.exec(
            select(Cycle).where(Cycle.user_id == existing_user.id)
        ).all()
        if len(existing_cycle) == 0:
            logger.info(f"Creating cycles for existing user: {existing_user}")
            # Copy of user to avoid changing the original instance and allow
            # the user to be returned
            current_user = existing_user.model_copy()
            create_cycles(session, existing_user.id)
            return current_user
    return HTTPException(status_code=400, detail="User already exists")
