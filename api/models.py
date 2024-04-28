from sqlmodel import Field, SQLModel, AutoString, Relationship
from pydantic import EmailStr
from datetime import datetime
from enum import Enum


class SourceEnum(str, Enum):
    app = "App"
    email = "Email"
    bot = "Bot"


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    name: str
    auth0_id: str = Field(unique=True, index=True)
    is_active: bool = True
    start_cycle_day: int = 1
    end_cycle_day: int = 31


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    recurrent_savings: list["RecurrentSaving"] = Relationship(
        back_populates="user"
    )
    recurrent_expenses: list["RecurrentExpense"] = Relationship(
        back_populates="user"
    )
    recurrent_incomes: list["RecurrentIncome"] = Relationship(
        back_populates="user"
    )
    savings: list["Saving"] = Relationship(back_populates="user")
    cycles: list["Cycle"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    pass


class RecurrentSaving(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_saving: float
    enabled: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_savings")
    outcomes: list["SavingOutcome"] = Relationship(
        back_populates="recurrent_saving"
    )


class RecurrentExpense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_spent: float
    enabled: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_expenses")


class RecurrentIncome(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_income: float
    enabled: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_incomes")


class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str


class Cycle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="cycles")
    incomes: list["Income"] = Relationship(back_populates='cycle')
    expenses: list["Expense"] = Relationship(back_populates='cycle')
    savings: list["Saving"] = Relationship(back_populates='cycle')


class Income(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_income: float
    date_income: datetime
    is_recurrent_income: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="incomes")


class Expense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_spent: float
    date_spent: datetime
    source: SourceEnum
    categories: str
    is_recurrent_expense: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="expenses")


class Saving(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_saved: float
    date_saving: datetime
    is_recurrent_saving: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="savings")


class SavingOutcome(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    description: str
    val_outcome: float
    date_outcome: datetime
    source: SourceEnum
    recurrent_saving_id: int = Field(foreign_key='recurrentsaving.id')
    recurrent_saving: RecurrentSaving = Relationship(back_populates='outcomes')
