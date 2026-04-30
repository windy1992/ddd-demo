# coding: utf-8

import logging
import json
import aio_pika

logger = logging.getLogger(__name__)


class Producer:
    """RabbitMQ Producer class for sending messages to a queue."""

    def __init__(self, host: str, queue_name: str):
        self.host = host
        self.queue_name = queue_name

        self._connection = None
        self._queue = None
        self._channel = None

    async def __aenter__(self):
        self._connection = await aio_pika.connect_robust(self.host)
        await self._connection.__aenter__()
        self._channel = await self._connection.channel()
        self._queue = await self._channel.declare_queue(self.queue_name, durable=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._connection.__aexit__(exc_type, exc, tb)

    async def send(self, message: dict):
        """Send a message to the RabbitMQ queue."""
        if not self._connection or self._connection.is_closed:
            raise RuntimeError("Connection is not established.")

        msg_str = json.dumps(message)

        await self._channel.default_exchange.publish(
            aio_pika.Message(
                body=msg_str.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=self._queue.name,
        )
        logger.info("msg: %s sent to q: %s", msg_str, self._queue.name)
