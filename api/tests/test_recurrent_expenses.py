from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import RecurrentExpense
import pytest


@pytest.fixture(name='recurrent_expenses')
def recurrent_expense_fixtures(session: Session):
    recurrent_expense_1 = RecurrentExpense(
        id=1,
        description='Desc 1',
        val_spent=100,
        user_id=1
    )
    recurrent_expense_2 = RecurrentExpense(
        id=2,
        description='Desc 2',
        val_spent=20000,
        user_id=1
    )
    recurrent_expense_3 = RecurrentExpense(
        id=3,
        description='Desc 3',
        val_spent=3994,
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
