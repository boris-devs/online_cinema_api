import asyncio
import os

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .celery_app import celery_app


@celery_app.task
def delete_expired_token(user_id: int):
    from database import ActivationTokenModel

    postgres_connection = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@"f"{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DB')}"

    async_postgres_engine = create_async_engine(postgres_connection, echo=True)

    AsyncPostgresqlSessionLocal = sessionmaker(  # type: ignore
        bind=async_postgres_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    async def async_delete():
        async with AsyncPostgresqlSessionLocal() as session:
            try:
                stmt = (
                    delete(ActivationTokenModel)
                    .where(ActivationTokenModel.user_id == user_id)
                )
                await session.execute(stmt)
                await session.commit()
                print(f"Token deleted for user {user_id}")
            except Exception as e:
                print(f"Error removing token for user {user_id}: {e}")
                await session.rollback()
                raise

    asyncio.run(async_delete())


@celery_app.task
def remove_activation_token_after_delay(user_id: int, delay_seconds: int):
    print(f"STARTED DELETION TOKEN IN {delay_seconds} SECONDS")

    delete_expired_token(user_id)
    print(f"Token removed after {delay_seconds} seconds for user {user_id}")
