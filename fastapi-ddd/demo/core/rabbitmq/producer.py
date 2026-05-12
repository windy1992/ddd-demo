# coding: utf-8

import logging
import json
from typing import Optional

import aio_pika

logger = logging.getLogger(__name__)


class Producer:
    """RabbitMQ 生产者：直连队列，或发布到 fanout 交换机（fan-out）。"""

    def __init__(
        self,
        host: str,
        queue_name: str = "",
        *,
        exchange_name: Optional[str] = None,
    ):
        self.host = host
        self.queue_name = queue_name
        self.exchange_name = exchange_name

        self._connection = None
        self._queue = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._channel = None

    async def __aenter__(self):
        self._connection = await aio_pika.connect_robust(self.host)
        await self._connection.__aenter__()
        self._channel = await self._connection.channel()
        if self.exchange_name:
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
            )
        else:
            if not self.queue_name:
                raise ValueError("直连队列模式下 queue_name 不能为空")
            self._queue = await self._channel.declare_queue(
                self.queue_name, durable=True
            )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._connection.__aexit__(exc_type, exc, tb)

    async def send(self, message: dict):
        """发布到队列（直连）或 fanout 交换机。"""
        if not self._connection or self._connection.is_closed:
            raise RuntimeError("Connection is not established.")

        msg_str = json.dumps(message)
        body = aio_pika.Message(
            body=msg_str.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        if self._exchange is not None:
            await self._exchange.publish(body, routing_key="")
            logger.info("msg: %s sent to fanout exchange: %s", msg_str, self.exchange_name)
        else:
            await self._channel.default_exchange.publish(
                body,
                routing_key=self._queue.name,
            )
            logger.info("msg: %s sent to q: %s", msg_str, self._queue.name)
