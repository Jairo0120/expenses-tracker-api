from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import RecurrentExpense
import pytest


@pytest.fixture(name='recurrent_expenses')
def recurrent_expense_fixtures(session: Session):
    recurrent_expense_1 = RecurrentExpense(
        id=1,
        description='Expense 1',
        val_expense=100,
        user_id=1
    )
    recurrent_expense_2 = RecurrentExpense(
        id=2,
        description='Expense 2',
        val_expense=20000,
        user_id=1
    )
    recurrent_expense_3 = RecurrentExpense(
        id=3,
        description='Expense 3',
        val_expense=3994,
        user_id=2
    )
    session.add(recurrent_expense_1)
    session.add(recurrent_expense_2)
    session.add(recurrent_expense_3)
    session.commit()


def test_read_recurrent_expenses_ok(client: TestClient, recurrent_expenses):
    response = client.get("/recurrent_expenses/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_new_recurrent_expense_created(client: TestClient, recurrent_expenses):
    req_data = {
        "description": "RE 1",
        "val_expense": 100,
        "categories": ""
    }
    response = client.post("/recurrent_expenses/", json=req_data)
    resp_data = response.json()
    assert response.status_code == 201
    assert resp_data['description'] == "RE 1"
    assert resp_data['user_id'] == 1


def test_create_recurrent_expense_incomplete_data(
        client: TestClient,
        recurrent_expenses
):
    req_data = {
        "description": "RE 1",
    }
    response = client.post("/recurrent_expenses/", json=req_data)
    assert response.status_code == 422


def test_update_recurrent_expense_other_user(
        client: TestClient,
        recurrent_expenses
):
    req_data = {
        "description": "RE 1",
    }
    response = client.patch("/recurrent_expenses/3", json=req_data)
    assert response.status_code == 404


def test_update_recurrent_expense_other_empty_values(
        client: TestClient,
        recurrent_expenses
):
    req_data = {
        "description": None,
        "val_expense": None
    }
    response = client.patch("/recurrent_expenses/2", json=req_data)
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Expense 2"
    assert data['val_expense'] == 20000


def test_delete_recurrent_expense_other_user(
        client: TestClient,
        recurrent_expenses
):
    response = client.delete("/recurrent_expenses/3")
    assert response.status_code == 404


def test_delete_recurrent_expense_success(
        client: TestClient,
        recurrent_expenses
):
    response = client.delete("/recurrent_expenses/2")
    assert response.status_code == 200
    response_2 = client.delete("/recurrent_expenses/2")
    assert response_2.status_code == 404
