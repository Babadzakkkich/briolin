from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.database.models import Base  # Импортируем Base из models

# Engine для своей БД (search_sessions)
own_engine = create_async_engine(
    settings.own_db_url,
    echo=settings.own_db_echo,
    pool_size=settings.own_db_pool_size,
    max_overflow=settings.own_db_max_overflow,
)

# Engine для БД profile-service (только чтение)
profile_engine = create_async_engine(
    settings.profile_db_url,
    echo=settings.profile_db_echo,
    pool_size=settings.profile_db_pool_size,
    max_overflow=settings.profile_db_max_overflow,
)

# Сессия для своей БД (search_sessions)
own_session_factory = async_sessionmaker(
    bind=own_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# Сессия для БД profile-service (только чтение)
profile_session_factory = async_sessionmaker(
    bind=profile_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


async def dispose_engines():
    """Закрытие всех соединений с БД"""
    await own_engine.dispose()
    await profile_engine.dispose()


async def init_db():
    """Создание таблицы search_sessions только в своей БД (для разработки)"""
    from app.database.models import SearchSession

    # Создаем только таблицу search_sessions
    async with own_engine.begin() as conn:
        # Создаем только таблицу search_sessions, если она не существует
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[SearchSession.__table__]  # Только таблица SearchSession
            )
        )