from sqlmodel import Session
from fastapi.testclient import TestClient
from ..models import Category
import pytest


@pytest.fixture(name='categories')
def category_fixtures(session: Session):
    category_1 = Category(
        id=1,
        description='Category 1',
        user_id=1
    )
    category_2 = Category(
        id=2,
        description='Category 2',
        user_id=1
    )
    category_3 = Category(
        id=3,
        description='Category 3',
        user_id=2
    )
    session.add(category_1)
    session.add(category_2)
    session.add(category_3)
    session.commit()


def test_read_categories_ok(client: TestClient, categories):
    response = client.get("/categories/")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2


def test_new_category_created(client: TestClient, categories):
    req_data = {
        "description": "Category  1",
        "val_category": 100,
    }
    response = client.post("/categories/", json=req_data)
    resp_data = response.json()
    assert response.status_code == 200
    assert resp_data['description'] == "Category  1"
    assert resp_data['user_id'] == 1


def test_create_category_incomplete_data(
        client: TestClient,
        categories
):
    response = client.post("/categories/")
    assert response.status_code == 422


def test_update_category_other_user(
        client: TestClient,
        categories
):
    req_data = {
        "description": "Category  1",
    }
    response = client.patch("/categories/3", json=req_data)
    assert response.status_code == 404


def test_update_category_other_empty_values(
        client: TestClient,
        categories
):
    req_data = {
        "description": None,
    }
    response = client.patch("/categories/2", json=req_data)
    assert response.status_code == 422


def test_delete_category_other_user(
        client: TestClient,
        categories
):
    response = client.delete("/categories/3")
    assert response.status_code == 404


def test_delete_category_success(
        client: TestClient,
        categories
):
    response = client.delete("/categories/2")
    assert response.status_code == 200
    response_2 = client.delete("/categories/2")
    assert response_2.status_code == 404


def test_get_single_category_not_found(
        client: TestClient,
        categories
):
    response = client.get("/categories/100")
    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_get_single_category_ok(
        client: TestClient,
        categories
):
    response = client.get("/categories/1")
    data = response.json()
    assert response.status_code == 200
    assert data['description'] == "Category 1"
    assert data['user_id'] == 1
