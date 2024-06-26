from sqlmodel import Field, SQLModel, AutoString, Relationship
from pydantic import EmailStr
from datetime import datetime, date
from enum import Enum


class SourceEnum(str, Enum):
    app = "App"
    email = "Email"
    bot = "Bot"
    recurrent = "Recurrent"


class BaseModel(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default=datetime.now(), nullable=False)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class UserBase(BaseModel):
    email: EmailStr = Field(unique=True, index=True, sa_type=AutoString)
    name: str
    auth0_id: str = Field(unique=True, index=True)
    is_active: bool = True
    start_cycle_day: int = 1
    end_cycle_day: int = 31


class User(UserBase, table=True):
    recurrent_savings: list["RecurrentSaving"] = Relationship(
        back_populates="user"
    )
    recurrent_expenses: list["RecurrentExpense"] = Relationship(
        back_populates="user"
    )
    recurrent_incomes: list["RecurrentIncome"] = Relationship(
        back_populates="user"
    )
    categories: list["Category"] = Relationship(back_populates="user")
    cycles: list["Cycle"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    pass


class RecurrentSaving(BaseModel, table=True):
    description: str
    val_saving: float
    enabled: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_savings")
    outcomes: list["SavingOutcome"] = Relationship(
        back_populates="recurrent_saving"
    )


class RecurrentExpenseBase(SQLModel):
    description: str
    val_spent: float
    enabled: bool = True
    categories: str = ''


class RecurrentExpense(BaseModel, RecurrentExpenseBase, table=True):
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_expenses")


class RecurrentExpenseCreate(RecurrentExpenseBase):
    pass


class RecurrentIncome(BaseModel, table=True):
    description: str
    val_income: float
    enabled: bool = True
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_incomes")


class Category(BaseModel, table=True):
    description: str
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="categories")


class Cycle(BaseModel, table=True):
    description: str
    start_date: date
    end_date: date
    is_active: bool = True
    is_recurrent_incomes_created: bool = False
    is_recurrent_expenses_created: bool = False
    is_recurrent_savings_created: bool = False
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="cycles")
    incomes: list["Income"] = Relationship(back_populates='cycle')
    expenses: list["Expense"] = Relationship(back_populates='cycle')
    savings: list["Saving"] = Relationship(back_populates='cycle')


class Income(BaseModel, table=True):
    description: str
    val_income: float
    date_income: datetime
    is_recurrent_income: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="incomes")


class Expense(BaseModel, table=True):
    description: str
    val_spent: float
    date_spent: datetime
    source: SourceEnum
    categories: str
    is_recurrent_expense: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="expenses")


class Saving(BaseModel, table=True):
    description: str
    val_saved: float
    date_saving: datetime
    is_recurrent_saving: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="savings")


class SavingOutcome(BaseModel, table=True):
    description: str
    val_outcome: float
    date_outcome: datetime
    source: SourceEnum
    recurrent_saving_id: int = Field(foreign_key='recurrentsaving.id')
    recurrent_saving: RecurrentSaving = Relationship(back_populates='outcomes')
