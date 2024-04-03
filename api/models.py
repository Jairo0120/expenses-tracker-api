from sqlmodel import Field, SQLModel, AutoString
from pydantic import EmailStr


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    name: str
    auth0_id: str = Field(unique=True, index=True)
    is_active: bool = True
    start_cycle_day: int = 1
    end_cycle_day: int = 31


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class UserCreate(UserBase):
    pass
