import asyncio

import pytest

from demo.core.rabbitmq.consumer import Consumer
from demo.core.rabbitmq.producer import Producer


@pytest.mark.asyncio
async def test_publish():
    async with Producer(
        "amqp://admin:admin1@127.0.0.1/", "task_queue_mazh"
    ) as producer:
        for i in range(5):
            await producer.send({"task": f"task_{i}", "data": "some_data"})
            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_subscribe():
    async def sample_task(msg: dict):
        print(f"Processing message: {msg}")
        await asyncio.sleep(1)  # Simulate some processing time

    consumer = Consumer("amqp://admin:admin1@127.0.0.1/", "task_queue_mazh")
    await consumer.run(sample_task)
