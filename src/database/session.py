"""
Enabling access to database sessions.
"""

from contextlib import contextmanager

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from config import DB_CONFIG


class EngineSingleton:
    """Making sure the engine is created only once."""

    __monostate = None

    def __init__(self):
        if not EngineSingleton.__monostate:
            EngineSingleton.__monostate = self.__dict__
            self.engine = create_engine(db_url(), echo=False, pool_recycle=3600)
        else:
            self.__dict__ = EngineSingleton.__monostate

    def patch(self, engine: Engine):
        self.__monostate["engine"] = engine  # type: ignore


def db_url(including_db=True):
    username = DB_CONFIG.get("name", "root")
    password = DB_CONFIG.get("password", "ok")
    host = DB_CONFIG.get("host", "demodb")
    port = DB_CONFIG.get("port", 3306)
    database = DB_CONFIG.get("database", "aiod")
    if including_db:
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    return f"mysql://{username}:{password}@{host}:{port}"


@contextmanager
def DbSession() -> Session:
    """
    Returning a SQLModel session bound to the (configured) database engine.

    Alternatively, we could have used FastAPI Depends, but that only works for FastAPI - while
    the synchronization, for instance, also needs a Session, but doesn't use FastAPI.
    """
    session = Session(EngineSingleton().engine)
    try:
        yield session
    finally:
        session.close()
