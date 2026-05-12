# coding: utf-8
import json
import logging
import asyncio
from typing import Any, Callable, Awaitable, Optional
import aio_pika

logger = logging.getLogger(__name__)


class Consumer:
    """RabbitMQ 消费者：支持直连持久化队列，或通过 fanout 交换机订阅（fan-out 模式）。"""

    def __init__(
        self,
        host: str,
        queue_name: str,
        prefetch_count: int = 1,
        *,
        exchange_name: Optional[str] = None,
    ):
        self.host = host
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self.exchange_name = exchange_name

    def _log_queue_label(self) -> str:
        if self.exchange_name:
            if self.queue_name:
                return f"exchange={self.exchange_name}, queue={self.queue_name}"
            return f"exchange={self.exchange_name}, queue=<exclusive anonymous>"
        return self.queue_name

    async def run(
        self,
        task_func: Callable[[dict], Awaitable[Any]],
        *,
        max_messages: Optional[int] = None,
        consume_timeout: Optional[float] = 30.0,
    ):
        if max_messages is not None and max_messages < 1:
            raise ValueError("max_messages 须为正整数")

        done = asyncio.Event()
        processed = 0

        async def on_message(message: aio_pika.IncomingMessage):
            nonlocal processed
            try:
                msg = json.loads(message.body.decode())
                logger.info("msg: %s received (%s)", msg, self._log_queue_label())
                await task_func(msg)
                logger.info("msg: %s done (%s)", msg, self._log_queue_label())
                await message.ack()
                processed += 1
                if max_messages is not None and processed >= max_messages:
                    done.set()
            except Exception as e:
                logger.error("处理消息时出错，重新入队: %s", e, exc_info=True)
                await message.reject(requeue=True)

        connection = await aio_pika.connect_robust(self.host)
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=self.prefetch_count)

        if self.exchange_name:
            exchange = await channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
            )
            if self.queue_name:
                queue = await channel.declare_queue(self.queue_name, durable=True)
            else:
                queue = await channel.declare_queue("", exclusive=True)
            await queue.bind(exchange)
        else:
            if not self.queue_name:
                raise ValueError("直连队列模式下 queue_name 不能为空")
            queue = await channel.declare_queue(self.queue_name, durable=True)

        logger.info("Waiting for messages (%s)", self._log_queue_label())
        consumer_tag = await queue.consume(on_message)
        try:
            if max_messages is None:
                await asyncio.Future()
            else:
                if consume_timeout is None:
                    await done.wait()
                else:
                    await asyncio.wait_for(
                        done.wait(), timeout=consume_timeout
                    )
        finally:
            if max_messages is not None:
                await queue.cancel(consumer_tag)
                await connection.close()
