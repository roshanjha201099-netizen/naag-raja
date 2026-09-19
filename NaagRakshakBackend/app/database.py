import logging
from urllib.parse import urlparse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

logger = logging.getLogger("naagrakshak.database")

class Base(DeclarativeBase):
    pass

_engine = None
_sessionmaker = None
active_db_type = "postgresql"

def mask_db_url(url: str) -> str:
    try:
        clean_url = url.replace("+asyncpg", "").replace("+aiosqlite", "")
        parsed = urlparse(clean_url)
        netloc = parsed.netloc
        if "@" in netloc:
            user_pass, host_port = netloc.split("@", 1)
            user = user_pass.split(":")[0] if ":" in user_pass else user_pass
            masked_netloc = f"{user}:****@{host_port}"
        else:
            masked_netloc = netloc
        return f"{parsed.scheme}://{masked_netloc}{parsed.path}"
    except Exception:
        return "[MASKED_URL]"

def get_engine():
    global _engine, active_db_type
    if _engine is not None:
        return _engine

    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        masked_target = mask_db_url(db_url)
        logger.info(f"Connecting to database target: {masked_target}")

        _engine = create_async_engine(
            db_url,
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

async def verify_db_connection():
    engine = get_engine()
    masked_url = mask_db_url(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT current_database(), inet_server_addr(), current_user;"))
            row = res.fetchone()
            if row:
                active_db, server_ip, current_user = row
                logger.info(
                    f"[RUNTIME DB SANITY CHECK SUCCESS] "
                    f"Active DB: '{active_db}' | "
                    f"Server IP: '{server_ip}' | "
                    f"User: '{current_user}' | "
                    f"Target Host: '{masked_url}'"
                )
                return {
                    "database": active_db,
                    "server_ip": str(server_ip),
                    "user": current_user,
                    "url": masked_url
                }
    except Exception as e:
        logger.error(f"[RUNTIME DB SANITY CHECK FAILED] Could not verify database connection to {masked_url}: {e}")
        raise e

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

def AsyncSessionLocal():
    sm = get_sessionmaker()
    return sm()

async def get_db():
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        finally:
            await session.close()

