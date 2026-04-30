from demo.core.db.mysql import get_async_engine

from demo.core.repository.repository import metadata
import pytest


@pytest.mark.asyncio
async def test_create():
    async with get_async_engine().begin() as conn:
        await conn.run_sync(metadata.create_all)
