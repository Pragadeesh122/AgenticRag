import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Build asyncpg connection URL
DB_USER = os.getenv("DB_ADMIN_USER", "admin")
DB_PASSWORD = os.getenv("DB_ADMIN_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "agenticrag")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
sync_session_maker = sessionmaker(
    bind=sync_engine, class_=Session, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
