import logging
import asyncio


from demo.core.db.mysql import get_async_engine
from demo.iam.infrastructure.message import create_role_deleted_message_publisher


logger = logging.getLogger(__name__)

async def main():
    while True:
        try:
            await create_role_deleted_message_publisher(get_async_engine()).dispatch()
        except Exception as e:
            logger.error(f"Error publishing role deleted message: {e}")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())