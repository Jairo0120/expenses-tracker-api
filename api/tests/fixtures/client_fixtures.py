from fastapi.testclient import TestClient
from sqlmodel import Session
from ...dependencies import get_session, get_current_active_user
from ...main import app
from ...models import User
import pytest


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    def get_current_active_user_override():
        return User(
            id=1,
            email='test@test.com',
            name='Test',
            auth0_id='auth1',
            is_active=True
        )

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_current_active_user] = \
        get_current_active_user_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
