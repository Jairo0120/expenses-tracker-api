from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import Income, Cycle, RecurrentIncome
from sqlmodel import select
from datetime import datetime
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
    cycle_3 = Cycle(
        id=3,
        description="Cycle 3",
        start_date=datetime(2021, 3, 1),
        end_date=datetime(2021, 3, 31),
        is_active=True,
        user_id=2,
    )
    session.add(cycle_1)
    session.add(cycle_2)
    session.add(cycle_3)
    session.commit()


@pytest.fixture(name="incomes")
def incomes_fixture(session: Session, cycles):
    income_1 = Income(id=1, description="Income 1", val_income=100, cycle_id=1)
    income_2 = Income(id=2, description="Income 2", val_income=200, cycle_id=1)
    income_3 = Income(id=3, description="Income 3", val_income=300, cycle_id=2)
    income_4 = Income(id=4, description="Income 4", val_income=300, cycle_id=3)
    session.add(income_1)
    session.add(income_2)
    session.add(income_3)
    session.add(income_4)
    session.commit()


def test_list_incomes(client: TestClient, incomes):
    response = client.get("/incomes/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["description"] == "Income 2"
    assert response.json()[1]["val_income"] == 100


def test_list_incomes_different_cycle(client: TestClient, incomes):
    response = client.get("/incomes/?cycle_id=2")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["description"] == "Income 3"


def test_create_income_no_cycle(client: TestClient, cycles):
    response = client.post(
        "/incomes/", json={"description": "Income 4", "val_income": 400}
    )
    assert response.status_code == 201
    assert response.json()["description"] == "Income 4"


def test_create_income_with_cycle(client: TestClient, cycles):
    response = client.post(
        "/incomes/",
        json={"description": "Income 5", "val_income": 500, "cycle_id": 2},
    )
    assert response.status_code == 201
    assert response.json()["description"] == "Income 5"


def test_create_income_no_owned_cycle(client: TestClient, cycles):
    response = client.post(
        "/incomes/",
        json={"description": "Income 6", "val_income": 600, "cycle_id": 3},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cycle not found"


def test_create_income_with_recurrent_income(
    client: TestClient, cycles, session
):
    response = client.post(
        "/incomes/",
        json={
            "description": "Income 7",
            "val_income": 600,
            "create_recurrent_income": True,
        },
    )
    recurrent_income = session.exec(
        select(RecurrentIncome).where(RecurrentIncome.user_id == 1)
    ).all()
    assert response.status_code == 201
    assert response.json()["description"] == "Income 7"
    assert response.json()["is_recurrent_income"] is True
    assert len(recurrent_income) == 1
    assert recurrent_income[0].description == "Income 7"


def test_update_income(client: TestClient, incomes, cycles):
    response = client.patch(
        "/incomes/1",
        json={"description": "Income 1 updated", "val_income": 150},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Income 1 updated"
    assert response.json()["val_income"] == 150


def test_update_income_not_owned_cycle(client: TestClient, incomes, cycles):
    response = client.patch(
        "/incomes/3",
        json={
            "description": "Income 3 updated",
            "val_income": 350,
            "cycle_id": 3,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cycle not found"


def test_update_income_not_found(client: TestClient, incomes, cycles):
    response = client.patch(
        "/incomes/5",
        json={"description": "Income 5 updated", "val_income": 550},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Income not found"


def test_delete_income(client: TestClient, incomes):
    response = client.delete("/incomes/1")
    assert response.status_code == 200
    response = client.get("/incomes/")
    assert len(response.json()) == 1
    assert response.json()[0]["description"] == "Income 2"


def test_delete_income_other_user(client: TestClient, incomes):
    response = client.delete("/incomes/4")
    assert response.status_code == 404
    assert response.json()["detail"] == "Income not found"
    response = client.get("/incomes/")
    assert len(response.json()) == 2
