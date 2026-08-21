import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

logger = logging.getLogger("naagrakshak.database")

class Base(DeclarativeBase):
    pass

_engine = None
_sessionmaker = None
active_db_type = "postgresql"

def get_engine():
    global _engine, active_db_type
    if _engine is not None:
        return _engine

    try:
        # Test connecting to PostgreSQL database
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True,
            pool_size=10,
            max_overflow=20
        )
        active_db_type = "postgresql"
        logger.info("Initialized Async PostgreSQL Engine")
    except Exception as e:
        logger.warning(f"PostgreSQL engine initialization failed: {e}. Falling back to SQLite.")
        _engine = create_async_engine(
            settings.SQLITE_URL,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False}
        )
        active_db_type = "sqlite"

    return _engine

def get_sessionmaker():
    global _sessionmaker
    if _sessionmaker is not None:
        return _sessionmaker
    engine = get_engine()
    _sessionmaker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return _sessionmaker

async def get_db():
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        finally:
            await session.close()
