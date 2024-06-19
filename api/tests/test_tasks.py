from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from datetime import datetime
from freezegun import freeze_time
from .. import tasks
from ..models import User, Cycle
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
def cycles_fixture(session: Session, users):
    active_cycle = Cycle(
        description=datetime.now().strftime('%B, %Y'),
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        user_id=1
    )
    session.add(active_cycle)
    session.commit()


def test_create_cycles_user_active(session: Session, users):
    tasks.create_cycles(session)
    cycles = session.exec(select(Cycle)).all()
    assert len(cycles) == 1
    assert cycles[0].user_id == 1


@freeze_time("2024-01-20")
def test_create_cycles_already_active_cycle(
    session: Session, users, active_cycle
):
    tasks.create_cycles(session)
    new_cycles = session.exec(select(Cycle)).all()
    assert len(new_cycles) == 1
