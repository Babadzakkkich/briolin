from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.postgres.url,
    echo=settings.postgres.echo,
    pool_size=settings.postgres.pool_size,
    max_overflow=settings.postgres.max_overflow,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async def dispose_engine():
    await engine.dispose()