from sqlmodel import Session, select
from ..models import RecurrentIncome, SyncState


def add_income(session: Session, description: str) -> RecurrentIncome:
    income = RecurrentIncome(description=description, val_income=1, user_id=1)
    session.add(income)
    session.commit()
    session.refresh(income)
    return income


def test_inserts_get_increasing_versions(session: Session, users):
    first = add_income(session, "A")
    second = add_income(session, "B")
    assert 0 < first.sync_version < second.sync_version
    state = session.exec(select(SyncState)).one()
    assert state.last_version == second.sync_version


def test_updates_get_a_new_version_and_touch_updated_at(
    session: Session, users
):
    first = add_income(session, "A")
    second = add_income(session, "B")
    first_updated_at = first.updated_at

    first.val_income = 2
    session.add(first)
    session.commit()
    session.refresh(first)

    assert first.sync_version > second.sync_version
    assert first.updated_at > first_updated_at


def test_unchanged_records_keep_their_version(session: Session, users):
    income = add_income(session, "A")
    version = income.sync_version
    income.val_income = income.val_income  # no real change
    session.add(income)
    session.commit()
    session.refresh(income)
    assert income.sync_version == version
