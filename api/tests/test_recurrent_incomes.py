from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import RecurrentIncome
import pytest


@pytest.fixture(name='recurrent_incomes')
def recurrent_income_fixtures(session: Session):
    recurrent_income_1 = RecurrentIncome(
        id=1,
        description='Income 1',
        val_income=100,
        user_id=1
    )
    recurrent_income_2 = RecurrentIncome(
        id=2,
        description='Income 2',
        val_income=20000,
        user_id=1
    )
    recurrent_income_3 = RecurrentIncome(
        id=3,
        description='Income 3',
        val_income=3994,
        user_id=2
    )
    session.add(recurrent_income_1)
    session.add(recurrent_income_2)
    session.add(recurrent_income_3)
    session.commit()


def test_read_recurrent_incomes_ok(client: TestClient, recurrent_incomes):
    response = client.get("/recurrent_incomes/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_new_recurrent_income_created(client: TestClient, recurrent_incomes):
    req_data = {
        "description": "RE 1",
        "val_income": 100,
    }
    response = client.post("/recurrent_incomes/", json=req_data)
    resp_data = response.json()
    assert response.status_code == 201
    assert resp_data['description'] == "RE 1"
    assert resp_data['user_id'] == 1


def test_create_recurrent_income_incomplete_data(
        client: TestClient,
        recurrent_incomes
):
    req_data = {
        "description": "RE 1",
    }
    response = client.post("/recurrent_incomes/", json=req_data)
    assert response.status_code == 422


def test_update_recurrent_income_other_user(
        client: TestClient,
        recurrent_incomes
):
    req_data = {
        "description": "RE 1",
    }
    response = client.patch("/recurrent_incomes/3", json=req_data)
    assert response.status_code == 404


def test_update_recurrent_income_other_empty_values(
        client: TestClient,
        recurrent_incomes
):
    req_data = {
        "description": None,
        "val_income": None
    }
    response = client.patch("/recurrent_incomes/2", json=req_data)
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Income 2"
    assert data['val_income'] == 20000


def test_delete_recurrent_income_other_user(
        client: TestClient,
        recurrent_incomes
):
    response = client.delete("/recurrent_incomes/3")
    assert response.status_code == 404


def test_delete_recurrent_income_success(
        client: TestClient,
        recurrent_incomes
):
    response = client.delete("/recurrent_incomes/2")
    assert response.status_code == 200
    response_2 = client.delete("/recurrent_incomes/2")
    assert response_2.status_code == 404


def test_get_single_recurrent_income_not_found(
        client: TestClient,
        recurrent_incomes
):
    response = client.get("/recurrent_incomes/100")
    assert response.status_code == 404
    assert response.json() == {"detail": "Recurrent income not found"}


def test_get_single_recurrent_income_ok(
        client: TestClient,
        recurrent_incomes
):
    response = client.get("/recurrent_incomes/1")
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Income 1"
    assert data['val_income'] == 100
    assert data['user_id'] == 1
