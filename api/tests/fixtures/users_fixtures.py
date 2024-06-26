from datetime import datetime
from ...models import User
from sqlmodel import Session
import pytest


@pytest.fixture(name='users')
def users_fixture(session: Session):
    active_user = User(
        id=1,
        email='test@test.com',
        name='Test',
        auth0_id='auth0|1',
        is_active=True,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    inactive_user = User(
        id=2,
        email='test2@test.com',
        name='Test',
        auth0_id='auth0|2',
        is_active=False,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1)
    )
    session.add(active_user)
    session.add(inactive_user)
    session.commit()
