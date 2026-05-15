# coding: utf-8
from __future__ import annotations

import json
import logging
from typing import Awaitable, Callable

from sqlalchemy import BigInteger, Column, DateTime, String, Table, text
from sqlalchemy.ext.asyncio import AsyncEngine

from demo.core.rabbitmq.consumer import Consumer
from demo.core.rabbitmq.producer import Producer
from demo.core.repository.repository import metadata
from demo.util.time import utc_now

logger = logging.getLogger(__name__)


# 游标表：记录每种事件类型最后发布的 stored_event_id
# 将进度查询从 O(n) LEFT JOIN 降为 O(1) PK 查询
# tl_stored_event 需配套 INDEX idx_type_id (type, id)，见 stored_event.py
tl_message_publish_cursor = Table(
    "tl_message_publish_cursor",
    metadata,
    Column("event_type", String(128), primary_key=True),
    Column("last_published_id", BigInteger, nullable=False, default=0),
    Column("updated_at", DateTime, nullable=False),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
)


MessageHandler = Callable[[dict], Awaitable[None]]


class RabbitMqMessagePublisher:
    """从 tl_stored_event outbox 增量中继发布到 RabbitMQ。

    每次 dispatch() 分三步：
    1. 读游标（O(1) PK）→ 得到 last_published_id
    2. 范围扫描 outbox（命中 (type, id) 复合索引）→ 取本批待发事件
    3. 批量发布后 UPSERT 游标

    语义与原 LEFT JOIN 方案一致（at-least-once）：若 crash 发生在发布之后、
    游标更新之前，下次重启会重发本批，消费端依赖 consume_tracker 幂等去重。
    """

    _BATCH_SIZE = 100

    def __init__(
        self,
        engine: AsyncEngine,
        *,
        amqp_url: str,
        exchange_name: str,
        event_type: str,
    ):
        self._engine = engine
        self._amqp_url = amqp_url
        self._exchange_name = exchange_name
        self._event_type = event_type

    async def dispatch(self) -> int:
        last_published_id = await self._read_cursor()

        rows = await self._fetch_pending(last_published_id)
        if not rows:
            return 0

        max_published_id = last_published_id
        async with Producer(self._amqp_url, "", exchange_name=self._exchange_name) as producer:
            for row in rows:
                body_obj = json.loads(row["body"])
                await producer.send(
                    {
                        "stored_event_id": int(row["id"]),
                        "type": row["type"],
                        "body": body_obj,
                    }
                )
                max_published_id = int(row["id"])

        await self._update_cursor(max_published_id)
        return len(rows)

    async def _read_cursor(self) -> int:
        stmt = text(
            "SELECT last_published_id FROM tl_message_publish_cursor"
            " WHERE event_type = :event_type"
        )
        async with self._engine.connect() as conn:
            row = (await conn.execute(stmt, {"event_type": self._event_type})).one_or_none()
        return int(row[0]) if row else 0

    async def _fetch_pending(self, last_published_id: int) -> list:
        stmt = text(
            "SELECT id, body, type FROM tl_stored_event"
            " WHERE type = :event_type AND id > :last_id"
            " ORDER BY id ASC"
            " LIMIT :batch_size"
        )
        async with self._engine.connect() as conn:
            result = await conn.execute(
                stmt,
                {
                    "event_type": self._event_type,
                    "last_id": last_published_id,
                    "batch_size": self._BATCH_SIZE,
                },
            )
            return result.mappings().all()

    async def _update_cursor(self, last_published_id: int) -> None:
        stmt = text(
            "INSERT INTO tl_message_publish_cursor"
            " (event_type, last_published_id, updated_at)"
            " VALUES (:event_type, :last_id, :now)"
            " ON DUPLICATE KEY UPDATE"
            " last_published_id = :last_id, updated_at = :now"
        )
        async with self._engine.begin() as conn:
            await conn.execute(
                stmt,
                {
                    "event_type": self._event_type,
                    "last_id": last_published_id,
                    "now": utc_now(),
                },
            )


class RabbitMqMessageSubscriber:
    """绑定 fanout 交换机，长期消费 ``queue_name`` 队列。"""

    def __init__(
        self,
        *,
        amqp_url: str,
        queue_name: str,
        exchange_name: str,
        on_message: MessageHandler,
    ):
        self._amqp_url = amqp_url
        self._queue_name = queue_name
        self._exchange_name = exchange_name
        self._on_message = on_message

    async def run_forever(self) -> None:
        await Consumer(
            self._amqp_url,
            self._queue_name,
            exchange_name=self._exchange_name,
        ).run(self._on_message)
