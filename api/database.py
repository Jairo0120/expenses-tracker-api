from functools import lru_cache
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, event, inspect
from . import config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
# The schema as it was before migrations were introduced.
BASELINE_REVISION = "0001"


@lru_cache
def get_settings():
    return config.Settings()


def run_migrations(database_url: str | None = None):
    """
    Bring the database schema up to date. A database created before migrations
    existed (tables but no recorded revision) is first marked as the baseline.
    Safe to call on every start: it does nothing when already up to date.
    """
    url = database_url or f"sqlite:///{get_settings().sqlite_database_url}"
    print(f"Migrating {url}")
    alembic_config = Config()
    alembic_config.set_main_option("script_location", str(MIGRATIONS_DIR))
    alembic_config.set_main_option("sqlalchemy.url", url)
    # A long busy timeout lets a second Lambda starting at the same time wait
    # for the first one's migration instead of failing.
    engine = create_engine(url, connect_args={"timeout": 60})
    _make_transactional(engine)
    try:
        with engine.begin() as connection:
            alembic_config.attributes["connection"] = connection
            current = MigrationContext.configure(
                connection
            ).get_current_revision()
            tables = inspect(connection).get_table_names()
            if current is None and "user" in tables:
                command.stamp(alembic_config, BASELINE_REVISION)
            command.upgrade(alembic_config, "head")
    finally:
        engine.dispose()


def _make_transactional(engine):
    """
    Python's sqlite3 driver runs CREATE/ALTER outside transactions, so a failed
    migration would leave a half-migrated database. Take over transaction
    control so the whole migration commits or rolls back as one (SQLite
    supports transactional DDL). IMMEDIATE takes the write lock up front.
    """

    @event.listens_for(engine, "connect")
    def _disable_driver_transactions(dbapi_connection, _record):
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin_immediate(connection):
        connection.exec_driver_sql("BEGIN IMMEDIATE")
