from sqlmodel import Session
from fastapi.testclient import TestClient
from datetime import datetime
from ..models import Budget, Cycle
import pytest


@pytest.fixture(name="cycles")
def cycle_fixture(session: Session):
    cycle_1 = Cycle(
        id=1,
        description="Cycle 1",
        start_date=datetime(2021, 1, 1),
        end_date=datetime(2021, 1, 31),
        is_active=True,
        user_id=1,
    )
    cycle_2 = Cycle(
        id=2,
        description="Cycle 2",
        start_date=datetime(2021, 2, 1),
        end_date=datetime(2021, 2, 28),
        is_active=False,
        user_id=1,
    )
    session.add(cycle_1)
    session.add(cycle_2)
    session.commit()


@pytest.fixture(name="budgets")
def budget_fixtures(session: Session, cycles):
    budget_1 = Budget(id=1, description="Budget 1", val_budget=100, cycle_id=1)
    budget_2 = Budget(
        id=2, description="Budget 2", val_budget=20000, cycle_id=1
    )
    budget_3 = Budget(
        id=3, description="Budget 3", val_budget=3994, cycle_id=2
    )
    session.add(budget_1)
    session.add(budget_2)
    session.add(budget_3)
    session.commit()


def test_read_budgets_ok(client: TestClient, budgets):
    response = client.get("/budgets/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_read_budgets_limit(client: TestClient, budgets):
    response = client.get("/budgets/?limit=1")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
