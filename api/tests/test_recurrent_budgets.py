from sqlmodel import Session, select
from fastapi.testclient import TestClient
from datetime import datetime
from ..models import RecurrentBudget, Budget, Cycle
import pytest


@pytest.fixture(name='recurrent_budgets')
def recurrent_budget_fixtures(session: Session):
    recurrent_budget_1 = RecurrentBudget(
        id=1,
        description='Budget 1',
        val_budget=100,
        user_id=1
    )
    recurrent_budget_2 = RecurrentBudget(
        id=2,
        description='Budget 2',
        val_budget=20000,
        user_id=1
    )
    recurrent_budget_3 = RecurrentBudget(
        id=3,
        description='Budget 3',
        val_budget=3994,
        user_id=2
    )
    session.add(recurrent_budget_1)
    session.add(recurrent_budget_2)
    session.add(recurrent_budget_3)
    session.commit()


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


def test_read_recurrent_budgets_ok(client: TestClient, recurrent_budgets):
    response = client.get("/recurrent_budgets/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_new_recurrent_budget_created(client: TestClient, recurrent_budgets,
                                      cycles, session):
    req_data = {
        "description": "RE 1",
        "val_budget": 100,
    }
    response = client.post("/recurrent_budgets/", json=req_data)
    resp_data = response.json()
    budget = session.exec(
        select(Budget).where(Budget.description == "RE 1")
    ).first()
    assert response.status_code == 201
    assert resp_data['description'] == "RE 1"
    assert resp_data['user_id'] == 1
    assert budget.description == "RE 1"


def test_create_recurrent_budget_incomplete_data(
        client: TestClient,
        recurrent_budgets
):
    req_data = {
        "description": "RE 1",
    }
    response = client.post("/recurrent_budgets/", json=req_data)
    assert response.status_code == 422


def test_update_recurrent_budget_other_user(
        client: TestClient,
        recurrent_budgets
):
    req_data = {
        "description": "RE 1",
    }
    response = client.patch("/recurrent_budgets/3", json=req_data)
    assert response.status_code == 404


def test_update_recurrent_budget_other_empty_values(
        client: TestClient,
        recurrent_budgets
):
    req_data = {
        "description": None,
        "val_budget": None
    }
    response = client.patch("/recurrent_budgets/2", json=req_data)
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Budget 2"
    assert data['val_budget'] == 20000


def test_delete_recurrent_budget_other_user(
        client: TestClient,
        recurrent_budgets
):
    response = client.delete("/recurrent_budgets/3")
    assert response.status_code == 404


def test_delete_recurrent_budget_success(
        client: TestClient,
        recurrent_budgets
):
    response = client.delete("/recurrent_budgets/2")
    assert response.status_code == 200
    response_2 = client.delete("/recurrent_budgets/2")
    assert response_2.status_code == 404


def test_get_single_recurrent_budget_not_found(
        client: TestClient,
        recurrent_budgets
):
    response = client.get("/recurrent_budgets/100")
    assert response.status_code == 404
    assert response.json() == {"detail": "Recurrent budget not found"}


def test_get_single_recurrent_budget_ok(
        client: TestClient,
        recurrent_budgets
):
    response = client.get("/recurrent_budgets/1")
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Budget 1"
    assert data['val_budget'] == 100
    assert data['user_id'] == 1
