import os
from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

# Base engine configuration
GDATASEA_DB = os.environ.get("GDATASEA_DB", "sqlite:///" + str(Path.home()/".gdatasea.db"))

_engine_args = {"connect_args": {}, "max_overflow": -1}

# Specific configurations for SQLite
_engine_args["connect_args"]["check_same_thread"] = False
engine = create_engine(GDATASEA_DB, **_engine_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
