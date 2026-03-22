import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = None
db_available = False
db_error_message = ""


def init_database() -> None:
    global engine, SessionLocal, db_available, db_error_message

    settings = get_settings()
    mysql_url = settings.mysql_url
    if not mysql_url:
        db_available = False
        db_error_message = "MYSQL_URL not configured. Running in in-memory mode."
        logger.warning(db_error_message)
        return

    try:
        engine = create_engine(mysql_url, pool_pre_ping=True, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        from app.models.product import Product  # noqa: F401
        from app.models.session import ChatSession  # noqa: F401
        from app.models.task_log import TaskLog  # noqa: F401

        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=Session,
            expire_on_commit=False,
        )
        db_available = True
        db_error_message = ""
        logger.info("Database connected successfully.")
    except Exception as exc:
        db_available = False
        db_error_message = f"Database unavailable: {exc}"
        logger.warning(db_error_message)


def get_db() -> Generator[Session | None, None, None]:
    if not db_available or SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_status() -> dict:
    return {
        "available": db_available,
        "message": "ok" if db_available else db_error_message,
    }

