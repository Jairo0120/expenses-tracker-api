from sqlmodel import Field, SQLModel, AutoString, Relationship
from pydantic import EmailStr
from datetime import datetime, date
from enum import Enum


class SourceEnum(str, Enum):
    app = "App"
    email = "Email"
    bot = "Bot"
    recurrent = "Recurrent"


class SavingMovementEnum(str, Enum):
    income = "Income"
    outcome = "Outcome"


class BaseModel(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
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
    recurrent_budgets: list["RecurrentBudget"] = Relationship(
        back_populates="user"
    )
    cycles: list["Cycle"] = Relationship(back_populates="user")
    saving_types: list["SavingType"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    pass


class SavingType(BaseModel, table=True):
    description: str
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="saving_types")
    savings: list["Saving"] = Relationship(back_populates="saving_type")
    recurrent_savings: list["RecurrentSaving"] = \
        Relationship(back_populates="saving_type")


class SavingTypePublic(SQLModel):
    id: int
    description: str


class RecurrentSavingBase(SQLModel):
    val_saving: float
    enabled: bool = True


class RecurrentSaving(BaseModel, RecurrentSavingBase, table=True):
    saving_type_id: int = Field(foreign_key='savingtype.id')
    saving_type: SavingType = Relationship(back_populates="recurrent_savings")
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_savings")


class RecurrentSavingUpdate(SQLModel):
    description: str | None = None
    val_saving: float | None = None
    enabled: bool | None = None


class RecurrentSavingCreate(RecurrentSavingBase):
    description: str


class RecurrentSavingPublic(SQLModel):
    id: int
    saving_type: SavingTypePublic
    val_saving: float
    enabled: bool
    user_id: int
    created_at: datetime


class RecurrentExpenseBase(SQLModel):
    description: str
    val_expense: float
    enabled: bool = True
    categories: str = ''


class RecurrentExpense(BaseModel, RecurrentExpenseBase, table=True):
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_expenses")


class RecurrentExpenseCreate(RecurrentExpenseBase):
    pass


class RecurrentExpenseUpdate(SQLModel):
    description: str | None = None
    val_expense: float | None = None
    enabled: bool | None = None
    categories: str | None = None


class RecurrentIncomeBase(SQLModel):
    description: str
    val_income: float
    enabled: bool = True


class RecurrentIncomeCreate(RecurrentIncomeBase):
    pass


class RecurrentIncomeUpdate(SQLModel):
    description: str | None = None
    val_income: float | None = None
    enabled: bool | None = None


class RecurrentIncome(BaseModel, RecurrentIncomeBase, table=True):
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_incomes")


class CategoryBase(SQLModel):
    description: str


class Category(BaseModel, CategoryBase, table=True):
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
    is_recurrent_budgets_created: bool = False
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="cycles")
    incomes: list["Income"] = Relationship(back_populates='cycle')
    expenses: list["Expense"] = Relationship(back_populates='cycle')
    savings: list["Saving"] = Relationship(back_populates='cycle')
    budgets: list["Budget"] = Relationship(back_populates='cycle')


class CyclePublic(SQLModel):
    id: int
    description: str
    start_date: date
    end_date: date
    is_active: bool = True


class Budget(BaseModel, table=True):
    description: str
    val_budget: float
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="budgets")
    expenses: list["Expense"] = Relationship(back_populates="budget")


class BudgetPublic(SQLModel):
    id: int
    description: str
    val_budget: float


class RecurrentBudgetBase(SQLModel):
    description: str
    val_budget: float
    is_enabled: bool = True


class RecurrentBudget(BaseModel, RecurrentBudgetBase, table=True):
    user_id: int = Field(foreign_key='user.id')
    user: User = Relationship(back_populates="recurrent_budgets")


class RecurrentBudgetCreate(RecurrentBudgetBase):
    pass


class RecurrentBudgetUpdate(SQLModel):
    description: str | None = None
    val_budget: float | None = None
    is_enabled: bool | None = None


class IncomeBase(SQLModel):
    description: str
    val_income: float
    date_income: datetime = Field(default=datetime.now(), nullable=False)


class Income(IncomeBase, BaseModel, table=True):
    is_recurrent_income: bool = False
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="incomes")


class IncomeCreate(IncomeBase):
    cycle_id: int | None = None
    create_recurrent_income: bool = False


class IncomeUpdate(SQLModel):
    description: str | None = None
    val_income: float | None = None
    date_income: datetime | None = None
    cycle_id: int | None = None


class ExpenseBase(SQLModel):
    description: str
    val_expense: float
    date_expense: datetime = Field(default=datetime.now(), nullable=False)
    source: SourceEnum = SourceEnum.app
    categories: str = ""


class Expense(ExpenseBase, BaseModel, table=True):
    is_recurrent_expense: bool = False
    budget_id: int | None = Field(foreign_key='budget.id', nullable=True)
    budget: Budget | None = Relationship(back_populates="expenses")
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="expenses")


class ExpenseCreate(ExpenseBase):
    cycle_id: int | None = None
    budget_id: int | None = None
    create_recurrent_expense: bool = False


class ExpensePublic(ExpenseBase):
    id: int
    budget: BudgetPublic | None = None
    cycle: CyclePublic
    is_recurrent_expense: bool


class ExpenseUpdate(SQLModel):
    description: str | None = None
    val_expense: float | None = None
    date_expense: datetime | None = None
    source: SourceEnum | None = None
    categories: str | None = None
    cycle_id: int | None = None
    budget_id: int | None = None


class SavingBase(SQLModel):
    val_saving: float
    date_saving: datetime = Field(default=datetime.now(), nullable=False)
    movement_type: SavingMovementEnum = SavingMovementEnum.income
    movement_description: str = ''


class Saving(SavingBase, BaseModel, table=True):
    is_recurrent_saving: bool = False
    saving_type_id: int = Field(foreign_key='savingtype.id')
    saving_type: SavingType = Relationship(back_populates="savings")
    cycle_id: int = Field(foreign_key='cycle.id')
    cycle: Cycle = Relationship(back_populates="savings")


class SavingCreate(SavingBase):
    description: str
    cycle_id: int | None = None
    create_recurrent_saving: bool = False


class SavingOutcomeCreate(SQLModel):
    saving: str
    val_outcome: float
    date_outcome: datetime = Field(default=datetime.now(), nullable=False)
    description: str
    cycle_id: int | None = None


class SavingUpdate(SQLModel):
    description: str | None = None
    val_saving: float | None = None
    date_saving: datetime | None = None
    cycle_id: int | None = None


class SavingPublic(SQLModel):
    id: int
    val_saving: float
    date_saving: datetime
    is_recurrent_saving: bool
    movement_type: SavingMovementEnum
    movement_description: str
    saving_type: SavingTypePublic
    cycle: CyclePublic


class GroupedSavings(SQLModel):
    id: int
    description: str
    is_recurrent_saving: bool
    total_global: float
    total_last_month: float
    last_saving: datetime


class CycleExpensesStatus(SQLModel):
    total_recurrent_expenses: float
    total_expenses: float
    total_incomes: float
    total_savings: float
