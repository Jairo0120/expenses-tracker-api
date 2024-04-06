from functools import lru_cache
from pathlib import Path
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from api.models import User
from sqlmodel import Session, create_engine, select
from . import config


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='token',
)


@lru_cache
def get_settings():
    return config.Settings()


def get_session():
    sqlite_url = f"sqlite:///{get_settings().sqlite_database_url}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
    with Session(engine) as session:
        yield session


async def get_current_user(token: str = Depends(oauth2_scheme),
                           session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    settings = get_settings()
    try:
        # python-jose takes care of the validation of the exp date of the token
        payload = jwt.decode(
            token,
            Path(settings.auth0_file_url).read_text(),
            algorithms="RS256",
            audience=settings.auth0_audience
        )
        auth0_id = payload.get('sub')
        if auth0_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # Check if the user exists
    statement = select(User).where(User.auth0_id == auth0_id)
    results = session.exec(statement)
    user = results.first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return current_user
