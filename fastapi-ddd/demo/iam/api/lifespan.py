

import asyncio

from demo.iam.infrastructure.message import create_role_deleted_message_subscriber, create_user_deleted_message_subscriber


async def start_up():
    asyncio.create_task(create_user_deleted_message_subscriber().run_forever())
    asyncio.create_task(create_role_deleted_message_subscriber().run_forever())

async def shutdown():
    pass