from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSQLModelSession

from api.config import config

engine = None


def get_engine(db_url: str | None = None):
    global engine
    if engine is None:
        url = db_url or config.DB_URL
        engine = create_async_engine(url)
    return engine


async def create_db_and_tables(db_url: str | None = None):
    e = get_engine(db_url)
    async with e.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session(db_url: str | None = None):
    e = get_engine(db_url)
    async with AsyncSQLModelSession(e) as session:
        yield session
