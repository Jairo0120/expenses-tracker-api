from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import RecurrentSaving
import pytest


@pytest.fixture(name='recurrent_savings')
def recurrent_saving_fixtures(session: Session):
    recurrent_saving_1 = RecurrentSaving(
        id=1,
        description='Desc 1',
        val_saving=100,
        user_id=1
    )
    recurrent_saving_2 = RecurrentSaving(
        id=2,
        description='Desc 2',
        val_saving=20000,
        user_id=1
    )
    recurrent_saving_3 = RecurrentSaving(
        id=3,
        description='Desc 3',
        val_saving=3994,
        user_id=2
    )
    session.add(recurrent_saving_1)
    session.add(recurrent_saving_2)
    session.add(recurrent_saving_3)
    session.commit()


def test_read_recurrent_savings_ok(client: TestClient, recurrent_savings):
    response = client.get("/recurrent_savings/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_new_recurrent_saving_created(client: TestClient, recurrent_savings):
    req_data = {
        "description": "RE 1",
        "val_saving": 100,
    }
    response = client.post("/recurrent_savings/", json=req_data)
    resp_data = response.json()
    assert response.status_code == 200
    assert resp_data['description'] == "RE 1"
    assert resp_data['user_id'] == 1


def test_create_recurrent_saving_incomplete_data(
        client: TestClient,
        recurrent_savings
):
    req_data = {
        "description": "RE 1",
    }
    response = client.post("/recurrent_savings/", json=req_data)
    assert response.status_code == 422


def test_update_recurrent_saving_other_user(
        client: TestClient,
        recurrent_savings
):
    req_data = {
        "description": "RE 1",
    }
    response = client.patch("/recurrent_savings/3", json=req_data)
    assert response.status_code == 404


def test_update_recurrent_saving_other_empty_values(
        client: TestClient,
        recurrent_savings
):
    req_data = {
        "description": None,
        "val_saving": None
    }
    response = client.patch("/recurrent_savings/2", json=req_data)
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Desc 2"
    assert data['val_saving'] == 20000


def test_delete_recurrent_saving_other_user(
        client: TestClient,
        recurrent_savings
):
    response = client.delete("/recurrent_savings/3")
    assert response.status_code == 404


def test_delete_recurrent_saving_success(
        client: TestClient,
        recurrent_savings
):
    response = client.delete("/recurrent_savings/2")
    assert response.status_code == 200
    response_2 = client.delete("/recurrent_savings/2")
    assert response_2.status_code == 404


def test_get_single_recurrent_saving_not_found(
        client: TestClient,
        recurrent_savings
):
    response = client.get("/recurrent_savings/100")
    assert response.status_code == 404
    assert response.json() == {"detail": "Recurrent saving not found"}


def test_get_single_recurrent_saving_ok(
        client: TestClient,
        recurrent_savings
):
    response = client.get("/recurrent_savings/1")
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Desc 1"
    assert data['val_saving'] == 100
    assert data['user_id'] == 1
