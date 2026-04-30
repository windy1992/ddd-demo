# coding: utf-8
import json
import logging
import asyncio
from typing import Any, Callable, Awaitable
import aio_pika

logger = logging.getLogger(__name__)


class Consumer:
    """RabbitMQ Consumer class for receiving messages from a queue."""

    def __init__(self, host: str, queue_name: str, prefetch_count=1):
        self.host = host
        self.queue_name = queue_name

        self.prefetch_count = prefetch_count  # 限制并发度

    async def run(self, task_func: Callable[[dict], Awaitable[Any]]):

        async def on_message(message: aio_pika.IncomingMessage):
            try:
                msg = json.loads(message.body.decode())
                logger.info("msg: %s received from q: %s", msg, self.queue_name)
                await task_func(msg)
                logger.info(
                    "msg: %s received from q: %s has done", msg, self.queue_name
                )
                await message.ack()
            except Exception as e:
                logger.error("处理消息时出错，重新入队: %s", e, exc_info=True)
                await message.reject(requeue=True)  # ⬅ 关键点：失败重回队列

        connection = await aio_pika.connect_robust(self.host)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=self.prefetch_count)

        queue = await channel.declare_queue(self.queue_name, durable=True)

        logger.info("q: %s Waiting for messages", self.queue_name)
        await queue.consume(on_message)
        await asyncio.Future()  # Keep running
