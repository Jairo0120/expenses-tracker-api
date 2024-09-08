from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import Saving, Cycle, RecurrentSaving, SavingType
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


@pytest.fixture(name="saving_types")
def saving_types_fixture(session: Session):
    saving_type_1 = SavingType(
        id=1,
        description="Saving 1",
        user_id=1
    )
    saving_type_2 = SavingType(
        id=2,
        description="Saving 2",
        user_id=1
    )
    saving_type_3 = SavingType(
        id=3,
        description="Saving 3",
        user_id=2
    )
    session.add(saving_type_1)
    session.add(saving_type_2)
    session.add(saving_type_3)
    session.commit()


@pytest.fixture(name="savings")
def savings_fixture(session: Session, cycles, saving_types):
    saving_1 = Saving(id=1, val_saving=100, cycle_id=1, saving_type_id=1)
    saving_2 = Saving(id=2, val_saving=200, cycle_id=1, saving_type_id=1)
    saving_3 = Saving(id=3, val_saving=300, cycle_id=2, saving_type_id=2)
    saving_4 = Saving(id=4, val_saving=300, cycle_id=3, saving_type_id=3)
    session.add(saving_1)
    session.add(saving_2)
    session.add(saving_3)
    session.add(saving_4)
    session.commit()


def test_list_savings(client: TestClient, savings):
    response = client.get("/savings/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["saving_type"]["description"] == "Saving 1"
    assert response.json()[1]["val_saving"] == 100


def test_list_savings_different_cycle(client: TestClient, savings):
    response = client.get("/savings/?cycle_id=2")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["saving_type"]["description"] == "Saving 2"


def test_create_saving_no_cycle(client: TestClient, cycles):
    response = client.post(
        "/savings/", json={"description": "Saving 4", "val_saving": 400}
    )
    assert response.status_code == 201
    assert response.json()["saving_type"]["description"] == "Saving 4"


def test_create_saving_with_cycle(client: TestClient, cycles):
    response = client.post(
        "/savings/",
        json={"description": "Saving 5", "val_saving": 500, "cycle_id": 2},
    )
    assert response.status_code == 201
    assert response.json()["saving_type"]["description"] == "Saving 5"


def test_create_saving_no_owned_cycle(client: TestClient, cycles):
    response = client.post(
        "/savings/",
        json={"description": "Saving 6", "val_saving": 600, "cycle_id": 3},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cycle not found"


def test_create_saving_with_recurrent_saving(
    client: TestClient, cycles, session
):
    response = client.post(
        "/savings/",
        json={
            "description": "Saving 7",
            "val_saving": 600,
            "create_recurrent_saving": True,
        },
    )
    recurrent_saving = session.exec(
        select(RecurrentSaving).where(RecurrentSaving.user_id == 1)
    ).all()
    assert response.status_code == 201
    assert response.json()["saving_type"]["description"] == "Saving 7"
    assert response.json()["is_recurrent_saving"] is True
    assert len(recurrent_saving) == 1
    assert recurrent_saving[0].saving_type.description == "Saving 7"


def test_update_saving(client: TestClient, savings, cycles):
    response = client.patch(
        "/savings/1",
        json={"description": "Saving 1 updated", "val_saving": 150},
    )
    assert response.status_code == 200
    assert response.json()["saving_type"]["description"] == "Saving 1 updated"
    assert response.json()["val_saving"] == 150


def test_update_saving_not_owned_cycle(client: TestClient, savings, cycles):
    response = client.patch(
        "/savings/3",
        json={
            "description": "Saving 3 updated",
            "val_saving": 350,
            "cycle_id": 3,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cycle not found"


def test_update_saving_not_found(client: TestClient, savings, cycles):
    response = client.patch(
        "/savings/5",
        json={"description": "Saving 5 updated", "val_saving": 550},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Saving not found"


def test_update_only_saving(client: TestClient, savings, cycles):
    response = client.patch(
        "/savings/1",
        json={"val_saving": 150},
    )
    assert response.status_code == 200
    assert response.json()["val_saving"] == 150


def test_delete_saving(client: TestClient, savings):
    response = client.delete("/savings/1")
    assert response.status_code == 200
    response = client.get("/savings/")
    assert len(response.json()) == 1
    assert response.json()[0]["saving_type"]["description"] == "Saving 1"


def test_delete_saving_other_user(client: TestClient, savings):
    response = client.delete("/savings/4")
    assert response.status_code == 404
    assert response.json()["detail"] == "Saving not found"
    response = client.get("/savings/")
    assert len(response.json()) == 2
