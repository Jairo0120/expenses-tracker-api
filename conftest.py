import pytest

pytest_plugins = [
    "api.tests.fixtures.session_db_fixtures",
    "api.tests.fixtures.client_fixtures",
    "api.tests.fixtures.users_fixtures",
]
