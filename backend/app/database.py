import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db(max_retries: int = 30, retry_delay: int = 2):
    """Initialize database with retry logic for Docker Swarm."""
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                # Enable pgvector extension
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database connection established successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise
