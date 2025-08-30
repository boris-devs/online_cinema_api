from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.config.settings import BaseAppSettings

settings = BaseAppSettings()

async_sqlite_engine = create_async_engine(f"sqlite+aiosqlite:///{settings.PATH_TO_DB}", echo=True)

AsyncSQLiteSession = sessionmaker(  # type: ignore
    bind=async_sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False)

sync_sqlite_engine = create_engine(f"sqlite:///{settings.PATH_TO_DB}", echo=False)

def get_async_sqlite_session() -> AsyncGenerator[AsyncSQLiteSession, None]:
    with AsyncSQLiteSession() as session:
        yield session

