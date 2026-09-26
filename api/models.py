from sqlmodel import Field, SQLModel, AutoString, Relationship, Session, select
from sqlalchemy import UniqueConstraint, event, text
from pydantic import EmailStr
from datetime import datetime, date, timezone
from enum import Enum
from uuid import uuid4


def utcnow() -> datetime:
    """
    The current time as naive UTC, the way every datetime is stored. Lambda
    runs in UTC, but the dev server doesn't, and syncing compares server and
    client timestamps.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    # Stable id shared with the apps, which generate it for records created
    # offline. The integer id stays the internal key.
    uuid: str = Field(
        default_factory=lambda: str(uuid4()),
        unique=True,
        index=True,
        max_length=36,
    )
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": utcnow},
    )
    # Soft-delete marker, so syncing clients learn about deletions.
    deleted_at: datetime | None = Field(default=None)
    # Position in the global change sequence (see assign_sync_versions);
    # clients pull whatever changed after the last version they saw.
    sync_version: int = Field(default=0, index=True)


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
    # One cycle per user and month, whoever creates it (server task or app).
    __table_args__ = (
        UniqueConstraint("user_id", "start_date", name="uq_cycle_user_month"),
    )

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
    # A recurrent budget is copied into a cycle at most once.
    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "recurrent_budget_id", name="uq_budget_cycle_recurrent"
        ),
    )

    description: str
    val_budget: float
    cycle_id: int = Field(foreign_key='cycle.id')
    recurrent_budget_id: int | None = Field(
        default=None, foreign_key='recurrentbudget.id'
    )
    cycle: Cycle = Relationship(back_populates="budgets")
    expenses: list["Expense"] = Relationship(back_populates="budget")


class BudgetPublic(SQLModel):
    id: int
    description: str
    val_budget: float


class BudgetWithTotal(SQLModel):
    id: int
    description: str
    val_budget: float
    cycle_id: int
    created_at: datetime
    updated_at: datetime
    total_spent: float


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
    date_income: datetime = Field(default_factory=utcnow, nullable=False)


class Income(IncomeBase, BaseModel, table=True):
    # A recurrent income is copied into a cycle at most once.
    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "recurrent_income_id", name="uq_income_cycle_recurrent"
        ),
    )

    is_recurrent_income: bool = False
    recurrent_income_id: int | None = Field(
        default=None, foreign_key='recurrentincome.id'
    )
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
    date_expense: datetime = Field(
        default_factory=utcnow, nullable=False
    )
    source: SourceEnum = SourceEnum.app
    categories: str = ""


class Expense(ExpenseBase, BaseModel, table=True):
    # A recurrent expense is copied into a cycle at most once.
    __table_args__ = (
        UniqueConstraint(
            "cycle_id",
            "recurrent_expense_id",
            name="uq_expense_cycle_recurrent",
        ),
    )

    is_recurrent_expense: bool = False
    recurrent_expense_id: int | None = Field(
        default=None, foreign_key='recurrentexpense.id'
    )
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
    date_saving: datetime = Field(default_factory=utcnow, nullable=False)
    movement_type: SavingMovementEnum = SavingMovementEnum.income
    movement_description: str = ''


class Saving(SavingBase, BaseModel, table=True):
    # A recurrent saving is copied into a cycle at most once.
    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "recurrent_saving_id", name="uq_saving_cycle_recurrent"
        ),
    )

    is_recurrent_saving: bool = False
    recurrent_saving_id: int | None = Field(
        default=None, foreign_key='recurrentsaving.id'
    )
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
    date_outcome: datetime = Field(
        default_factory=utcnow, nullable=False
    )
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
    last_saving: datetime | None = None


class CycleExpensesStatus(SQLModel):
    total_recurrent_expenses: float
    total_expenses: float
    total_incomes: float
    total_savings: float


class CycleSimpleList(SQLModel):
    id: int
    start_date: date
    end_date: date
    description: str


class SyncState(SQLModel, table=True):
    """Single row holding the last sync_version handed out."""

    id: int = Field(default=1, primary_key=True)
    last_version: int = 0


@event.listens_for(Session, "before_flush")
def assign_sync_versions(session, flush_context, instances):
    """
    Give every inserted or modified record the next versions of a global
    counter. The counter is bumped inside the flush's transaction, and SQLite
    serializes writers, so versions are committed in increasing order and a
    client pulling "after version N" never misses a change.
    """
    changed = [obj for obj in session.new if isinstance(obj, BaseModel)]
    changed += [
        obj
        for obj in session.dirty
        if isinstance(obj, BaseModel) and session.is_modified(obj)
    ]
    if not changed:
        return
    connection = session.connection()
    connection.execute(
        text(
            "INSERT INTO syncstate (id, last_version) VALUES (1, 0) "
            "ON CONFLICT (id) DO NOTHING"
        )
    )
    connection.execute(
        text(
            "UPDATE syncstate SET last_version = last_version + :count "
            "WHERE id = 1"
        ),
        {"count": len(changed)},
    )
    last = connection.execute(
        text("SELECT last_version FROM syncstate WHERE id = 1")
    ).scalar_one()
    for offset, obj in enumerate(changed):
        obj.sync_version = last - len(changed) + 1 + offset


def select_live(model):
    """`select(model)` without soft-deleted records."""
    return select(model).where(model.deleted_at.is_(None))


def soft_delete(session: Session, record: BaseModel):
    """
    Mark a record deleted instead of removing it, so syncing clients learn
    about the deletion. Expenses stop pointing at a deleted budget.
    """
    record.deleted_at = utcnow()
    session.add(record)
    if isinstance(record, Budget):
        for expense in session.exec(
            select(Expense).where(Expense.budget_id == record.id)
        ).all():
            expense.budget_id = None
            session.add(expense)


def refresh_active_cycle(session: Session, user_id: int, today: date):
    """
    Make the cycle containing `today` the user's only active one, if it
    exists. Cycles can now also arrive from the apps (created offline).
    """
    current = session.exec(
        select(Cycle)
        .where(Cycle.user_id == user_id)
        .where(Cycle.deleted_at.is_(None))
        .where(Cycle.start_date <= today)
        .where(Cycle.end_date >= today)
    ).first()
    if not current:
        return
    for cycle in session.exec(
        select(Cycle)
        .where(Cycle.user_id == user_id)
        .where(Cycle.is_active == 1)
        .where(Cycle.id != current.id)
    ).all():
        cycle.is_active = False
        session.add(cycle)
    if not current.is_active:
        current.is_active = True
        session.add(current)
