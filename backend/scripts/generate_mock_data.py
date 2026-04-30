"""Script to create mock data in the database."""

import asyncio

from sqlmodel.ext.asyncio.session import AsyncSession

from api.config import config
from api.db import create_db_and_tables, get_engine
from api.services.annotations import create_mock_data


async def main():
    """Create mock data in the database."""
    # Ensure tables exist
    await create_db_and_tables()

    # Create a session and run the mock data creation
    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await create_mock_data(session)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
