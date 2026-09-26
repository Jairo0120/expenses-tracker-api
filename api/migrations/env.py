from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
import api.models  # noqa: F401 (registers the tables on SQLModel.metadata)

config = context.config
target_metadata = SQLModel.metadata

# `alembic -x url=sqlite:///other.db …` targets another database (e.g. an empty
# one for autogenerate, or a copy of prod to test a migration).
url_override = context.get_x_argument(as_dictionary=True).get("url")
if url_override:
    config.set_main_option("sqlalchemy.url", url_override)
elif not config.get_main_option("sqlalchemy.url"):
    from api.dependencies import get_settings

    config.set_main_option(
        "sqlalchemy.url", f"sqlite:///{get_settings().sqlite_database_url}"
    )


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            _run(connection)
    else:
        _run(connectable)


def _run(connection):
    # SQLite can't alter columns in place; batch mode recreates tables.
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
