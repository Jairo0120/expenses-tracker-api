from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import Expense, Cycle, Budget
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
        user_id=1
    )
    cycle_2 = Cycle(
        id=2,
        description="Cycle 2",
        start_date=datetime(2021, 2, 1),
        end_date=datetime(2021, 2, 28),
        is_active=False,
        user_id=1
    )
    session.add(cycle_1)
    session.add(cycle_2)
    session.commit()


@pytest.fixture(name="budgets")
def budget_fixtures(session: Session, cycles):
    budget_1 = Budget(
        id=1,
        description="Budget 1",
        val_budget=100,
        cycle_id=1
    )
    budget_2 = Budget(
        id=2,
        description="Budget 2",
        val_budget=200,
        cycle_id=1
    )
    budget_3 = Budget(
        id=3,
        description="Budget 3",
        val_budget=300,
        cycle_id=2
    )
    session.add(budget_1)
    session.add(budget_2)
    session.add(budget_3)
    session.commit()


@pytest.fixture(name='expenses')
def expense_fixtures(session: Session, cycles):
    expense_1 = Expense(
        id=1,
        description='Expense 1',
        val_expense=100,
        date_expense=datetime(2021, 1, 1),
        cycle_id=1,
        budget_id=None
    )
    expense_2 = Expense(
        id=2,
        description='Expense 2',
        val_expense=200,
        date_expense=datetime(2021, 1, 3),
        cycle_id=1,
        budget_id=1
    )
    expense_3 = Expense(
        id=3,
        description='Expense 3',
        val_expense=300,
        date_expense=datetime(2021, 1, 3),
        cycle_id=2,
        budget_id=1
    )
    session.add(expense_1)
    session.add(expense_2)
    session.add(expense_3)
    session.commit()


def test_read_expenses(client: TestClient, expenses):
    response = client.get('/expenses/')
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_create_expense(client: TestClient, expenses, cycles, budgets):
    req_data = {
        "description": "Expense 4",
        "val_expense": 400,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 1
    }
    response = client.post('/expenses/', json=req_data)
    assert response.status_code == 201
    data = response.json()
    assert data['description'] == "Expense 4"
    assert data['val_expense'] == 400
    assert data['cycle']['id'] == 1
    assert data['budget']['id'] == 1
    assert data['date_expense'] == "2021-01-10T00:00:00"


def test_create_expense_cycle_not_found(client: TestClient, expenses, budgets):
    req_data = {
        "description": "Expense 4",
        "val_expense": 400,
        "date_expense": "2021-01-10",
        "cycle_id": 3,
        "budget_id": 1
    }
    response = client.post('/expenses/', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Cycle not found"


def test_create_expense_budget_not_found(client: TestClient, expenses, cycles):
    req_data = {
        "description": "Expense 4",
        "val_expense": 400,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 3
    }
    response = client.post('/expenses/', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Budget not found"


def test_create_expense_incomplete_data(client: TestClient, expenses):
    response = client.post('/expenses/')
    assert response.status_code == 422


def test_update_expense(client: TestClient, expenses, cycles, budgets):
    req_data = {
        "description": "Expense 1 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 1
    }
    response = client.patch('/expenses/1', json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert data['description'] == "Expense 1 Updated"
    assert data['val_expense'] == 200
    assert data['cycle']['id'] == 1
    assert data['budget']['id'] == 1
    assert data['date_expense'] == "2021-01-10T00:00:00"


def test_update_expense_cycle_not_found(client: TestClient, expenses, budgets):
    req_data = {
        "description": "Expense 1 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 3,
        "budget_id": 1
    }
    response = client.patch('/expenses/1', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Cycle not found"


def test_update_expense_budget_not_found(client: TestClient, expenses, cycles):
    req_data = {
        "description": "Expense 1 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 3
    }
    response = client.patch('/expenses/1', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Budget not found"


def test_update_expense_not_found(client: TestClient, expenses):
    req_data = {
        "description": "Expense 1 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 1
    }
    response = client.patch('/expenses/4', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Expense not found"


def test_update_cycle_budget_should_empty(client: TestClient, expenses, cycles,
                                          budgets):
    req_data = {
        "description": "Expense 2 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 2
    }
    response = client.patch('/expenses/2', json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert data['cycle']['id'] == 2
    assert data['budget'] is None


def test_update_budget_should_be_in_cycle(client: TestClient, expenses, cycles,
                                          budgets):
    req_data = {
        "description": "Expense 2 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 3
    }
    response = client.patch('/expenses/1', json=req_data)
    assert response.status_code == 404
    assert response.json()['detail'] == "Budget not found"


def test_update_budget_ok(client: TestClient, expenses, cycles, budgets):
    req_data = {
        "description": "Expense 2 Updated",
        "val_expense": 200,
        "date_expense": "2021-01-10",
        "cycle_id": 1,
        "budget_id": 2
    }
    response = client.patch('/expenses/1', json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert data['description'] == "Expense 2 Updated"
    assert data['val_expense'] == 200
    assert data['cycle']['id'] == 1
    assert data['budget']['id'] == 2
    assert data['date_expense'] == "2021-01-10T00:00:00"


def test_delete_expense(client: TestClient, expenses):
    response = client.delete('/expenses/1')
    assert response.status_code == 200
    response_2 = client.delete('/expenses/1')
    assert response_2.status_code == 404
