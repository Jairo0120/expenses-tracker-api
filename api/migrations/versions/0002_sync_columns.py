"""sync columns, cycle month key and recurrent links

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-26

Prepares the schema for syncing with offline-capable clients:
- every table gets a unique `uuid`, a soft-delete `deleted_at` and a
  `sync_version` from the global counter in the new `syncstate` table;
- cycles become unique per user and month (duplicate empty cycles left by the
  cycle task are merged first);
- copies of recurrent entries point to their source, at most once per cycle.
"""
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TABLES = [
    "user",
    "savingtype",
    "recurrentexpense",
    "recurrentincome",
    "category",
    "cycle",
    "recurrentbudget",
    "recurrentsaving",
    "budget",
    "income",
    "saving",
    "expense",
]

CYCLE_CHILDREN = ["expense", "income", "saving", "budget"]
CYCLE_FLAGS = [
    "is_active",
    "is_recurrent_incomes_created",
    "is_recurrent_expenses_created",
    "is_recurrent_savings_created",
    "is_recurrent_budgets_created",
]

# (table, link column, source table)
RECURRENT_LINKS = [
    ("expense", "recurrent_expense_id", "recurrentexpense"),
    ("income", "recurrent_income_id", "recurrentincome"),
    ("saving", "recurrent_saving_id", "recurrentsaving"),
    ("budget", "recurrent_budget_id", "recurrentbudget"),
]


def upgrade():
    op.create_table(
        "syncstate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(
                sa.Column("uuid", sa.String(36), nullable=True)
            )
            batch_op.add_column(
                sa.Column("deleted_at", sa.DateTime(), nullable=True)
            )
            batch_op.add_column(
                sa.Column(
                    "sync_version",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )

    connection = op.get_bind()
    merge_duplicate_cycles(connection)
    backfill_uuids_and_versions(connection)

    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "uuid", existing_type=sa.String(36), nullable=False
            )
            batch_op.create_index(f"ix_{table}_uuid", ["uuid"], unique=True)
            batch_op.create_index(
                f"ix_{table}_sync_version", ["sync_version"], unique=False
            )

    with op.batch_alter_table("cycle") as batch_op:
        batch_op.create_unique_constraint(
            "uq_cycle_user_month", ["user_id", "start_date"]
        )

    for table, column, source in RECURRENT_LINKS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column(column, sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                f"fk_{table}_{column}_{source}", source, [column], ["id"]
            )
            batch_op.create_unique_constraint(
                f"uq_{table}_cycle_recurrent", ["cycle_id", column]
            )


def merge_duplicate_cycles(connection):
    """
    Keep one cycle per (user, month): the one with the most records (oldest on
    a tie). Records of the others move to it, it keeps any flag set on the
    group, and the others are deleted.
    """
    groups = connection.execute(
        sa.text(
            "SELECT user_id, start_date FROM cycle "
            "GROUP BY user_id, start_date HAVING count(*) > 1"
        )
    ).fetchall()
    for user_id, start_date in groups:
        cycles = connection.execute(
            sa.text(
                "SELECT id FROM cycle WHERE user_id = :user"
                " AND start_date = :start ORDER BY id"
            ),
            {"user": user_id, "start": start_date},
        ).scalars().all()

        def record_count(cycle_id):
            return sum(
                connection.execute(
                    sa.text(
                        f"SELECT count(*) FROM {child} WHERE cycle_id = :id"
                    ),
                    {"id": cycle_id},
                ).scalar_one()
                for child in CYCLE_CHILDREN
            )

        keeper = max(
            cycles, key=lambda cycle_id: (record_count(cycle_id), -cycle_id)
        )
        others = [cycle_id for cycle_id in cycles if cycle_id != keeper]
        placeholders = ", ".join(f":o{i}" for i in range(len(others)))
        params = {f"o{i}": cycle_id for i, cycle_id in enumerate(others)}
        for child in CYCLE_CHILDREN:
            connection.execute(
                sa.text(
                    f"UPDATE {child} SET cycle_id = :keeper "
                    f"WHERE cycle_id IN ({placeholders})"
                ),
                {"keeper": keeper, **params},
            )
        flags = ", ".join(
            f"{flag} = (SELECT max({flag}) FROM cycle "
            "WHERE user_id = :user AND start_date = :start)"
            for flag in CYCLE_FLAGS
        )
        connection.execute(
            sa.text(f"UPDATE cycle SET {flags} WHERE id = :keeper"),
            {"keeper": keeper, "user": user_id, "start": start_date},
        )
        connection.execute(
            sa.text(f"DELETE FROM cycle WHERE id IN ({placeholders})"), params
        )


def backfill_uuids_and_versions(connection):
    """Give existing rows a uuid and consecutive sync versions."""
    version = 0
    for table in TABLES:
        ids = connection.execute(
            sa.text(f'SELECT id FROM "{table}" ORDER BY id')
        ).scalars().all()
        for row_id in ids:
            version += 1
            connection.execute(
                sa.text(
                    f'UPDATE "{table}" SET uuid = :uuid, '
                    "sync_version = :version WHERE id = :id"
                ),
                {"uuid": str(uuid4()), "version": version, "id": row_id},
            )
    connection.execute(
        sa.text(
            "INSERT INTO syncstate (id, last_version) VALUES (1, :version)"
        ),
        {"version": version},
    )


def downgrade():
    # The duplicate cycles merged in upgrade() are not restored.
    for table, column, source in RECURRENT_LINKS:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(
                f"uq_{table}_cycle_recurrent", type_="unique"
            )
            batch_op.drop_constraint(
                f"fk_{table}_{column}_{source}", type_="foreignkey"
            )
            batch_op.drop_column(column)

    with op.batch_alter_table("cycle") as batch_op:
        batch_op.drop_constraint("uq_cycle_user_month", type_="unique")

    for table in TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_index(f"ix_{table}_sync_version")
            batch_op.drop_index(f"ix_{table}_uuid")
            batch_op.drop_column("sync_version")
            batch_op.drop_column("deleted_at")
            batch_op.drop_column("uuid")

    op.drop_table("syncstate")
