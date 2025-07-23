"""
Database configuration and connection management
PostgreSQL with SQLAlchemy ORM and async support
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from typing import AsyncGenerator
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Database configuration
settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()

# Metadata for Alembic
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
Base.metadata = metadata


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Ensures proper session cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from ..models import fashion_models, generation_models, user_models
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


class DatabaseManager:
    """Database manager for handling connections and transactions."""
    
    def __init__(self):
        self.engine = engine
        self.session_maker = AsyncSessionLocal
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return AsyncSessionLocal()
    
    async def execute_transaction(self, func, *args, **kwargs):
        """Execute a function within a database transaction."""
        async with AsyncSessionLocal() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False