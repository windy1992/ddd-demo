import asyncio
import uuid

import pytest

from demo.core.rabbitmq.consumer import Consumer
from demo.core.rabbitmq.producer import Producer

AMQP_URL = "amqp://admin:admin1@127.0.0.1/"


@pytest.mark.asyncio
async def test_subscribe():
    # 使用独立队列名，避免与其它进程/历史测试残留消息（含无法 JSON 解析的毒消息）
    # 抢队列导致一直 requeue，从而在 consumer 的 consume_timeout 内收不满 max_messages。
    queue_name = f"task_queue_test_{uuid.uuid4().hex[:16]}"

    async with Producer(AMQP_URL, queue_name) as producer:
        for i in range(5):
            await producer.send({"task": f"task_{i}", "data": "some_data"})

    async def sample_task(msg: dict):
        print(f"Processing message: {msg}")
        await asyncio.sleep(0.05)

    consumer = Consumer(AMQP_URL, queue_name)
    await consumer.run(sample_task, max_messages=5)


@pytest.mark.asyncio
async def test_fanout_delivers_to_each_bound_queue():
    """一条 fanout 消息经 Consumer 投递到两条独立绑定队列，各收一份。"""
    exchange_name = f"test_fanout_{uuid.uuid4().hex[:16]}"
    queue_a = f"{exchange_name}_sub_a"
    queue_b = f"{exchange_name}_sub_b"
    payload = {"fanout_key": "hello", "n": 1}
    received: list[dict] = []

    async def record(msg: dict) -> None:
        received.append(dict(msg))

    c1 = Consumer(AMQP_URL, queue_a, exchange_name=exchange_name)
    c2 = Consumer(AMQP_URL, queue_b, exchange_name=exchange_name)

    t1 = asyncio.create_task(c1.run(record, max_messages=1))
    t2 = asyncio.create_task(c2.run(record, max_messages=1))
    await asyncio.sleep(0.3)

    async with Producer(AMQP_URL, exchange_name=exchange_name) as producer:
        await producer.send(payload)

    await asyncio.gather(t1, t2)
    assert len(received) == 2
    assert all(m == payload for m in received)
