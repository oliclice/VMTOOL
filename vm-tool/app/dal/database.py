from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from app.core.config_manager import config_manager

Base = declarative_base()

_engine = None
_SessionFactory = None


def _get_engine():
    global _engine
    if _engine is None:
        database_path = config_manager.get("database_path")
        _engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={
                "check_same_thread": False,
                "timeout": 30
            },
            poolclass=StaticPool,
            pool_pre_ping=True
        )
    return _engine


def _get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionFactory


def recreate_engine():
    global _engine, _SessionFactory
    _engine = None
    _SessionFactory = None
    _get_engine()
    _get_session_factory()


def get_db():
    session_factory = _get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
