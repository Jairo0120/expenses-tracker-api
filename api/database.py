from functools import lru_cache
from sqlmodel import SQLModel, create_engine
from . import config


@lru_cache
def get_settings():
    return config.Settings()


sqlite_url = f"sqlite:///{get_settings().sqlite_database_url}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
