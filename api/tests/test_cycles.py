from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import Cycle, Expense, Income, Saving, SavingType
from datetime import datetime
import pytest


@pytest.fixture(name="cycle_movements")
def cycle_movements_fixture(session: Session):
    session.add(
        Cycle(
            id=1,
            description="Cycle 1",
            start_date=datetime(2021, 1, 1),
            end_date=datetime(2021, 1, 31),
            is_active=True,
            user_id=1,
        )
    )
    session.add(
        Cycle(
            id=2,
            description="Cycle 2",
            start_date=datetime(2021, 2, 1),
            end_date=datetime(2021, 2, 28),
            is_active=False,
            user_id=1,
        )
    )
    session.add(SavingType(id=1, description="Saving 1", user_id=1))
    session.add(Expense(description="E1", val_expense=100, cycle_id=1))
    session.add(Expense(description="E2", val_expense=40, cycle_id=1))
    session.add(
        Expense(
            description="Rent",
            val_expense=500,
            cycle_id=1,
            is_recurrent_expense=True,
        )
    )
    session.add(Expense(description="E3", val_expense=999, cycle_id=2))
    session.add(Income(description="Salary", val_income=2000, cycle_id=1))
    session.add(Saving(val_saving=300, cycle_id=1, saving_type_id=1))
    session.commit()


def test_cycle_status_active_cycle(client: TestClient, cycle_movements):
    response = client.get("/cycles/cycle-status")
    assert response.status_code == 200
    assert response.json() == {
        "total_recurrent_expenses": 500,
        "total_expenses": 140,
        "total_incomes": 2000,
        "total_savings": 300,
    }


def test_cycle_status_other_cycle(client: TestClient, cycle_movements):
    response = client.get("/cycles/cycle-status?cycle_id=2")
    assert response.status_code == 200
    assert response.json()["total_expenses"] == 999
    assert response.json()["total_incomes"] == 0


def test_cycle_status_cycle_not_found(client: TestClient, cycle_movements):
    response = client.get("/cycles/cycle-status?cycle_id=999")
    assert response.status_code == 404
