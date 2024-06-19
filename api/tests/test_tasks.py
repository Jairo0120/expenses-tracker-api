from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from datetime import datetime
from freezegun import freeze_time
from .. import tasks
from ..models import User, Cycle, Income, RecurrentIncome
import pytest


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name='users')
def users_fixture(session: Session):
    active_user = User(
        id=1,
        email='test@test.com',
        name='Test',
        auth0_id='auth0|1',
        is_active=True,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    inactive_user = User(
        id=2,
        email='test2@test.com',
        name='Test',
        auth0_id='auth0|2',
        is_active=False,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(active_user)
    session.add(inactive_user)
    session.commit()


@pytest.fixture(name='active_cycle')
def active_cycle_fixture(session: Session, users):
    active_cycle = Cycle(
        description=datetime.now().strftime('%B, %Y'),
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        user_id=1
    )
    session.add(active_cycle)
    session.commit()


@pytest.fixture(name='inactive_cycle')
def inactive_cycle_fixture(session: Session, users):
    inactive_cycle = Cycle(
        description=datetime.now().strftime('%B, %Y'),
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        user_id=1,
        is_active=False
    )
    session.add(inactive_cycle)
    session.commit()


@pytest.fixture(name='recurrent_incomes')
def recurrent_incomes_fixture(session: Session, users):
    recurrent_income_1 = RecurrentIncome(
        description='Income 1',
        val_income=1000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    recurrent_income_2 = RecurrentIncome(
        description='Income 2',
        val_income=40000,
        user_id=1,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(recurrent_income_1)
    session.add(recurrent_income_2)
    session.commit()


def test_create_cycles_user_active(session: Session, users):
    tasks.create_cycles(session)
    cycles = session.exec(select(Cycle)).all()
    assert len(cycles) == 1
    assert cycles[0].user_id == 1


@freeze_time("2024-02-01")
def test_create_cycle_with_expired_cycle(session: Session, active_cycle):
    tasks.create_cycles(session)
    cycles = session.exec(select(Cycle).order_by(Cycle.id.asc())).all()
    assert len(cycles) == 2
    assert cycles[0].is_active is False


@freeze_time("2024-01-20")
def test_create_cycles_already_active_cycle(
    session: Session, users, active_cycle
):
    tasks.create_cycles(session)
    new_cycles = session.exec(select(Cycle)).all()
    assert len(new_cycles) == 1


def test_create_recurrent_incomes_active_cycle(
        session: Session, active_cycle, recurrent_incomes
):
    tasks.create_recurrent_incomes(session)
    incomes = session.exec(select(Income)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(incomes) == 2
    assert cycle.is_recurrent_incomes_created == 1


def test_create_recurrent_incomes_inactive_cycle(
        session: Session, inactive_cycle, recurrent_incomes
):
    tasks.create_recurrent_incomes(session)
    incomes = session.exec(select(Income)).all()
    cycle = session.exec(select(Cycle)).one()
    assert len(incomes) == 0
    assert cycle.is_recurrent_incomes_created == 0
