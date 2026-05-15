# coding: utf-8
"""RoleDeleted：出队 → RabbitMQ 发布；订阅后软删角色用户关联与角色权限关联。"""
from __future__ import annotations

import json
import logging

from sqlalchemy import BigInteger, Column, DateTime, Index, String, Table, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from demo.core.config import get_config
from demo.core.config.config import RoleDeletedMessageConfig
from demo.core.db.mysql import get_async_engine
from demo.core.message import RabbitMqMessagePublisher, RabbitMqMessageSubscriber
from demo.core.repository import metadata
from demo.iam.application.iam_service import IamService
from demo.util.time import utc_now

logger = logging.getLogger(__name__)


tl_role_deleted_consume_tracker = Table(
    "tl_role_deleted_consume_tracker",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column(
        "stored_event_id",
        BigInteger,
        nullable=False,
        unique=True,
    ),
    Column("role_id", String(128), nullable=False),
    Column("consumed_at", DateTime, nullable=False),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
)

def get_role_deleted_message_config() -> RoleDeletedMessageConfig:
    return get_config().messages.role_deleted_message


def create_role_deleted_message_publisher(engine: AsyncEngine) -> RabbitMqMessagePublisher:
    return RabbitMqMessagePublisher(
        engine,
        amqp_url=get_role_deleted_message_config().amqp_url,
        exchange_name=get_role_deleted_message_config().fanout_exchange,
        event_type=get_role_deleted_message_config().event_type,
    )


def create_role_deleted_message_subscriber() -> RabbitMqMessageSubscriber:
    return RabbitMqMessageSubscriber(
        amqp_url=get_role_deleted_message_config().amqp_url,
        queue_name=get_role_deleted_message_config().queue_name,
        exchange_name=get_role_deleted_message_config().fanout_exchange,
        on_message=role_deleted_handler,
    )


async def role_deleted_handler(msg: dict) -> None:
    """先占位消费 tracker（与业务同一事务），保证同一 stored_event_id 只处理一次。"""
    if msg.get("type") != get_role_deleted_message_config().event_type:
        return
    raw_sid = msg.get("stored_event_id")
    if raw_sid is None:
        logger.warning("RoleDeleted missing stored_event_id: %s", msg)
        return
    stored_event_id = int(raw_sid)

    body = msg.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    if not isinstance(body, dict):
        return
    role_id = body.get("role_id")
    if not role_id:
        return

    try:
        async with get_async_engine().begin() as conn:
            await conn.execute(
                insert(tl_role_deleted_consume_tracker).values(
                    stored_event_id=stored_event_id,
                    role_id=role_id,
                    consumed_at=utc_now(),
                )
            )
            await IamService(conn).revoke_all_permissions_from_role(role_id)
    except IntegrityError:
        # 通常为重复 stored_event_id（已消费）；事务已由 begin 上下文回滚
        logger.debug(
            "RoleDeleted skip (integrity) stored_event_id=%s role_id=%s",
            stored_event_id,
            role_id,
        )
        return

    logger.info(
        "RoleDeleted ok role_id=%s stored_event_id=%s",
        role_id,
        stored_event_id,
    )
