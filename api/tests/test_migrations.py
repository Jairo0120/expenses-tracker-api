from pathlib import Path
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel
from ..database import MIGRATIONS_DIR, run_migrations
import pytest


@pytest.fixture(name="db_url")
def db_url_fixture(tmp_path: Path):
    return f"sqlite:///{tmp_path / 'test.db'}"


def upgrade_to(url: str, revision: str):
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, revision)


def current_revision(url: str):
    with create_engine(url).connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_fresh_database_matches_models(db_url):
    run_migrations(db_url)
    with create_engine(db_url).connect() as connection:
        diff = compare_metadata(
            MigrationContext.configure(connection), SQLModel.metadata
        )
    assert diff == []


def test_database_from_before_migrations_is_stamped_and_upgraded(db_url):
    # The baseline schema without alembic's bookkeeping, like prod before this.
    upgrade_to(db_url, "0001")
    with create_engine(db_url).begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))
    run_migrations(db_url)
    assert current_revision(db_url) == "0002"
    run_migrations(db_url)  # a second start is a no-op
    assert current_revision(db_url) == "0002"


def test_upgrade_merges_duplicate_cycles_and_backfills(db_url):
    upgrade_to(db_url, "0001")
    engine = create_engine(db_url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO user (id, created_at, updated_at, email, name,"
            " auth0_id, is_active, start_cycle_day, end_cycle_day) VALUES"
            " (1, '2024-01-01', '2024-01-01', 'a@b.c', 'A', 'auth0|1', 1,"
            " 1, 31)"
        ))
        # Three cycles for November: only 12 has records, 11 set a flag.
        for cycle_id, flag in [(11, 1), (12, 0), (13, 0)]:
            connection.execute(text(
                "INSERT INTO cycle (id, created_at, updated_at, description,"
                " start_date, end_date, is_active,"
                " is_recurrent_incomes_created, is_recurrent_expenses_created,"
                " is_recurrent_savings_created, is_recurrent_budgets_created,"
                " user_id) VALUES (:id, '2024-11-01', '2024-11-01', 'Nov',"
                " '2024-11-01', '2024-11-30', 0, :flag, 0, 0, 0, 1)"
            ), {"id": cycle_id, "flag": flag})
        connection.execute(text(
            "INSERT INTO cycle (id, created_at, updated_at, description,"
            " start_date, end_date, is_active, is_recurrent_incomes_created,"
            " is_recurrent_expenses_created, is_recurrent_savings_created,"
            " is_recurrent_budgets_created, user_id) VALUES (14, '2024-12-01',"
            " '2024-12-01', 'Dec', '2024-12-01', '2024-12-31', 1, 0, 0, 0, 0,"
            " 1)"
        ))
        connection.execute(text(
            "INSERT INTO expense (id, created_at, updated_at, description,"
            " val_expense, date_expense, source, categories,"
            " is_recurrent_expense, cycle_id) VALUES (1, '2024-11-02',"
            " '2024-11-02', 'Taxi', 10, '2024-11-02', 'app', '', 0, 12)"
        ))

    run_migrations(db_url)

    with engine.connect() as connection:
        cycles = connection.execute(text(
            "SELECT id, is_recurrent_incomes_created FROM cycle ORDER BY id"
        )).fetchall()
        assert [tuple(row) for row in cycles] == [(12, 1), (14, 0)]
        assert connection.execute(
            text("SELECT cycle_id FROM expense")
        ).scalar_one() == 12
        rows = connection.execute(text(
            "SELECT uuid, sync_version FROM cycle UNION ALL "
            "SELECT uuid, sync_version FROM expense UNION ALL "
            'SELECT uuid, sync_version FROM "user"'
        )).fetchall()
        assert len({uuid for uuid, _ in rows}) == 4
        assert sorted(version for _, version in rows) == [1, 2, 3, 4]
        assert connection.execute(
            text("SELECT last_version FROM syncstate")
        ).scalar_one() == 4


def test_failed_migration_leaves_the_database_untouched(db_url):
    upgrade_to(db_url, "0001")
    engine = create_engine(db_url)
    with engine.begin() as connection:
        # A leftover batch-mode table: the upgrade only fails when it reaches
        # the expense table, after creating syncstate and altering the rest.
        connection.execute(
            text("CREATE TABLE _alembic_tmp_expense (id INTEGER)")
        )

    with pytest.raises(Exception):
        run_migrations(db_url)

    assert current_revision(db_url) == "0001"
    with engine.connect() as connection:
        tables = inspect(connection).get_table_names()
        user_columns = [
            column["name"]
            for column in inspect(connection).get_columns("user")
        ]
    assert "syncstate" not in tables
    assert "uuid" not in user_columns

    # Once the leftover is gone, the next start migrates normally.
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE _alembic_tmp_expense"))
    run_migrations(db_url)
    assert current_revision(db_url) == "0002"
