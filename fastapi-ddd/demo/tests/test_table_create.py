from demo.init_env import init_env
init_env()

from demo.core.db.mysql import get_async_engine

from demo.core.repository.repository import metadata
# from demo.iam.infrastructure.message.role_deleted import tl_role_deleted_consume_tracker
# from demo.iam.infrastructure.message.user_deleted import tl_user_deleted_consume_tracker
# from demo.core.message import tl_message_publish_cursor

import pytest


@pytest.mark.asyncio
async def test_create():
    async with get_async_engine().begin() as conn:
        await conn.run_sync(metadata.create_all)
