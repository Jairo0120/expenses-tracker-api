from datetime import date, datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from freezegun import freeze_time
from ..models import (
    Budget,
    Cycle,
    Expense,
    RecurrentExpense,
    Saving,
    SavingType,
    utcnow,
)
import pytest


@pytest.fixture(name="data")
def data_fixture(session: Session, users):
    """User 1: an old and a current cycle, a budget, expenses, a saving."""
    old = Cycle(
        description="Jan", start_date=date(2021, 1, 1),
        end_date=date(2021, 1, 31), is_active=False, user_id=1,
    )
    current = Cycle(
        description="Feb", start_date=date(2021, 2, 1),
        end_date=date(2021, 2, 28), is_active=True, user_id=1,
    )
    other_user = Cycle(
        description="Feb", start_date=date(2021, 2, 1),
        end_date=date(2021, 2, 28), is_active=True, user_id=3,
    )
    session.add_all([old, current, other_user])
    session.flush()
    budget = Budget(description="Food", val_budget=100, cycle_id=current.id)
    saving_type = SavingType(description="Car", user_id=1)
    recurrent = RecurrentExpense(description="Rent", val_expense=50, user_id=1)
    session.add_all([budget, saving_type, recurrent])
    session.flush()
    session.add_all([
        Expense(description="Old", val_expense=1, cycle_id=old.id),
        Expense(
            description="Lunch", val_expense=10, cycle_id=current.id,
            budget_id=budget.id,
        ),
        Expense(description="Theirs", val_expense=3, cycle_id=other_user.id),
        Saving(val_saving=5, cycle_id=old.id, saving_type_id=saving_type.id),
    ])
    session.commit()
    return {
        "old": old, "current": current, "other_user": other_user,
        "budget": budget, "saving_type": saving_type, "recurrent": recurrent,
    }


def pull(client: TestClient, **params):
    response = client.get("/sync", params=params)
    assert response.status_code == 200
    return response.json()


def push(client: TestClient, *changes):
    response = client.post("/sync", json={"changes": list(changes)})
    assert response.status_code == 200
    return response.json()["results"]


def change(entity, data=None, uuid=None, updated_at=None, deleted=False):
    return {
        "entity": entity,
        "uuid": uuid or str(uuid4()),
        "updated_at": (updated_at or utcnow()).isoformat() + "Z",
        "deleted": deleted,
        "data": data or {},
    }


def descriptions(changes, entity):
    return sorted(r["description"] for r in changes.get(entity, []))


def test_pull_returns_the_users_records_with_uuid_references(
    client: TestClient, data
):
    result = pull(client)
    changes = result["changes"]
    assert result["has_more"] is False
    assert list(changes) == [
        "cycles", "saving_types", "recurrent_expenses", "budgets",
        "expenses", "savings",
    ]
    assert descriptions(changes, "expenses") == ["Lunch", "Old"]
    lunch = next(r for r in changes["expenses"] if r["description"] == "Lunch")
    assert lunch["cycle_uuid"] == data["current"].uuid
    assert lunch["budget_uuid"] == data["budget"].uuid
    assert lunch["deleted_at"] is None
    saving = changes["savings"][0]
    assert saving["saving_type_uuid"] == data["saving_type"].uuid


def test_pull_since_cursor_returns_only_later_changes(
    client: TestClient, data
):
    cursor = pull(client)["cursor"]
    assert pull(client, since=cursor)["changes"] == {}

    lunch = next(
        e for e in data["current"].expenses if e.description == "Lunch"
    )
    client.patch(f"/expenses/{lunch.id}", json={"val_expense": 12})
    result = pull(client, since=cursor)
    assert [r["val_expense"] for r in result["changes"]["expenses"]] == [12]
    assert result["cursor"] > cursor


def test_pull_includes_deletions(client: TestClient, data):
    cursor = pull(client)["cursor"]
    lunch = next(
        e for e in data["current"].expenses if e.description == "Lunch"
    )
    assert client.delete(f"/expenses/{lunch.id}").status_code == 200
    deleted = pull(client, since=cursor)["changes"]["expenses"]
    assert deleted[0]["uuid"] == lunch.uuid
    assert deleted[0]["deleted_at"] is not None


def test_pull_pages(client: TestClient, data):
    everything = pull(client)["changes"]
    total = sum(len(records) for records in everything.values())
    seen, cursor, pages = [], 0, 0
    while True:
        result = pull(client, since=cursor, limit=2)
        page = [r for records in result["changes"].values() for r in records]
        seen += [r["uuid"] for r in page]
        assert result["cursor"] > cursor
        cursor, pages = result["cursor"], pages + 1
        if not result["has_more"]:
            break
    assert len(seen) == len(set(seen)) == total
    assert pages > 1


def test_pull_window_keeps_all_savings(client: TestClient, data):
    changes = pull(client, window_start="2021-02-01")["changes"]
    assert descriptions(changes, "expenses") == ["Lunch"]
    # The saving is in the old cycle, but savings totals need all of them.
    assert len(changes["savings"]) == 1
    assert len(changes["cycles"]) == 2


def test_push_creates_records_with_client_uuids(
    client: TestClient, session: Session, data
):
    cycle_uuid, expense_uuid = str(uuid4()), str(uuid4())
    results = push(
        client,
        change("cycles", {
            "description": "Mar", "start_date": "2021-03-01",
            "end_date": "2021-03-31",
        }, uuid=cycle_uuid),
        change("expenses", {
            "description": "Taxi", "val_expense": 7,
            "date_expense": "2021-03-02T15:00:00-05:00",
            "cycle_uuid": cycle_uuid,
        }, uuid=expense_uuid),
    )
    assert [r["status"] for r in results] == ["applied", "applied"]
    assert results[1]["record"]["cycle_uuid"] == cycle_uuid
    expense = session.exec(
        select(Expense).where(Expense.uuid == expense_uuid)
    ).one()
    # Offsets are converted to naive UTC.
    assert expense.date_expense == datetime(2021, 3, 2, 20, 0)


def test_push_latest_edit_wins(client: TestClient, data):
    budget = data["budget"]
    older = budget.updated_at - timedelta(minutes=5)
    stale = push(client, change(
        "budgets", {"val_budget": 1}, uuid=budget.uuid, updated_at=older
    ))[0]
    assert stale["status"] == "stale"
    assert stale["record"]["val_budget"] == 100

    newer = utcnow() + timedelta(seconds=1)
    applied = push(client, change(
        "budgets", {"val_budget": 150}, uuid=budget.uuid, updated_at=newer
    ))[0]
    assert applied["status"] == "applied"
    assert applied["record"]["val_budget"] == 150


def test_push_delete_wins(client: TestClient, session: Session, data):
    budget = data["budget"]
    deleted = push(client, change("budgets", uuid=budget.uuid, deleted=True))
    assert deleted[0]["status"] == "applied"
    later_edit = push(client, change(
        "budgets", {"val_budget": 1}, uuid=budget.uuid,
        updated_at=utcnow() + timedelta(hours=1),
    ))[0]
    assert later_edit["status"] == "stale"
    assert later_edit["record"]["deleted_at"] is not None
    # Its expenses no longer point at it.
    lunch = session.exec(
        select(Expense).where(Expense.description == "Lunch")
    ).one()
    session.refresh(lunch)
    assert lunch.budget_id is None


def test_push_merges_a_cycle_for_an_existing_month(
    client: TestClient, session: Session, data
):
    client_cycle = str(uuid4())
    results = push(
        client,
        change("cycles", {
            "description": "Feb (offline)", "start_date": "2021-02-01",
            "end_date": "2021-02-28",
        }, uuid=client_cycle),
        # Still references the client's uuid for the cycle.
        change("expenses", {
            "description": "Taxi", "val_expense": 7,
            "date_expense": "2021-02-02T10:00:00Z", "cycle_uuid": client_cycle,
        }),
    )
    assert results[0]["status"] == "merged"
    assert results[0]["record"]["uuid"] == data["current"].uuid
    assert results[1]["status"] == "applied"
    assert results[1]["record"]["cycle_uuid"] == data["current"].uuid


def test_push_merges_saving_types_by_name(client: TestClient, data):
    result = push(client, change("saving_types", {"description": "car"}))[0]
    assert result["status"] == "merged"
    assert result["record"]["uuid"] == data["saving_type"].uuid


def test_push_merges_recurrent_copies(client: TestClient, data):
    copy = {
        "description": "Rent", "val_expense": 50,
        "date_expense": "2021-02-01T00:00:00Z",
        "is_recurrent_expense": True,
        "cycle_uuid": data["current"].uuid,
        "recurrent_expense_uuid": data["recurrent"].uuid,
    }
    first = push(client, change("expenses", copy))[0]
    second = push(client, change("expenses", copy))[0]
    assert first["status"] == "applied"
    assert second["status"] == "merged"
    assert second["record"]["uuid"] == first["record"]["uuid"]

    # A copy the server deleted stays deleted.
    push(client, change("expenses", uuid=first["uuid"], deleted=True))
    third = push(client, change("expenses", copy))[0]
    assert third["status"] == "stale"
    assert third["record"]["deleted_at"] is not None


@pytest.mark.parametrize(
    "entity, payload, reason",
    [
        ("goals", {"description": "x"}, "Unknown entity"),
        ("expenses", {"description": "No amount"}, "Missing"),
        ("expenses", {"extra": 1}, "Invalid data"),
        ("expenses", {
            "description": "x", "val_expense": 1,
            "date_expense": "2021-02-02T00:00:00Z", "cycle_uuid": "nope",
        }, "Unknown cycle_uuid"),
    ],
)
def test_push_rejects_invalid_changes(
    client: TestClient, data, entity, payload, reason
):
    result = push(client, change(entity, payload))[0]
    assert result["status"] == "rejected"
    assert reason in result["reason"]


def test_push_rejects_other_users_records(client: TestClient, data):
    theirs = push(client, change("expenses", {
        "description": "x", "val_expense": 1,
        "date_expense": "2021-02-02T00:00:00Z",
        "cycle_uuid": data["other_user"].uuid,
    }))[0]
    assert theirs["status"] == "rejected"
    edit_theirs = push(client, change(
        "cycles", {"description": "Mine now"}, uuid=data["other_user"].uuid
    ))[0]
    assert edit_theirs["status"] == "rejected"


def test_push_rejects_a_budget_from_another_cycle(client: TestClient, data):
    result = push(client, change("expenses", {
        "description": "x", "val_expense": 1,
        "date_expense": "2021-01-02T00:00:00Z",
        "cycle_uuid": data["old"].uuid, "budget_uuid": data["budget"].uuid,
    }))[0]
    assert result["status"] == "rejected"
    assert "another cycle" in result["reason"]


@freeze_time("2021-03-15")
def test_pushed_cycle_for_today_becomes_the_active_one(
    client: TestClient, session: Session, data
):
    push(client, change("cycles", {
        "description": "Mar", "start_date": "2021-03-01",
        "end_date": "2021-03-31",
    }))
    active = session.exec(
        select(Cycle).where(Cycle.user_id == 1).where(Cycle.is_active == 1)
    ).all()
    assert [c.start_date for c in active] == [date(2021, 3, 1)]


def test_deleted_records_disappear_from_the_rest_api(
    client: TestClient, data
):
    lunch = next(
        e for e in data["current"].expenses if e.description == "Lunch"
    )
    cycle_id = data["current"].id
    before = client.get(f"/cycles/cycle-status?cycle_id={cycle_id}").json()
    client.delete(f"/expenses/{lunch.id}")

    listed = client.get(f"/expenses?cycle_id={cycle_id}").json()
    assert lunch.id not in [e["id"] for e in listed]
    after = client.get(f"/cycles/cycle-status?cycle_id={cycle_id}").json()
    assert after["total_expenses"] == before["total_expenses"] - 10
    budgets = client.get(f"/budgets?cycle_id={cycle_id}").json()
    assert [b["total_spent"] for b in budgets] == [0]
    assert client.delete(f"/expenses/{lunch.id}").status_code == 404
