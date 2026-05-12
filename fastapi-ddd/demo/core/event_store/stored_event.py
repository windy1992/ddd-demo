from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import TEXT, BigInteger, Column, DateTime, String, Table
from sqlalchemy.ext.asyncio import AsyncConnection


from demo.core.event_store.domain_event import DomainEvent, DomainEventSubscriber
from demo.core.repository.repository import metadata


class StoredEvent(BaseModel):
    id: str | None = Field(default=None)
    body: str
    type: str
    occurred_at: datetime


tl_stored_event = Table(
    "tl_stored_event",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("body", TEXT, nullable=False),
    Column("type", String(128), nullable=False),
    Column("occurred_at", DateTime, nullable=False),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4",
)

T = TypeVar("T", bound=DomainEvent)


class EventStore:
    tl = tl_stored_event

    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def append(self, event: T):
        stored_event = StoredEvent(
            body=event.model_dump_json(),
            occurred_at=event.occurred_at,
            type=event.__class__.__name__,
        )
        await self.conn.execute(self.tl.insert().values(**stored_event.model_dump()))


class DefaultDomainEventSubscriber(DomainEventSubscriber[DomainEvent]):
    def __init__(self, conn: AsyncConnection):
        super().__init__()
        self.event_store = EventStore(conn)

    async def handle_event(self, event: DomainEvent):
        await self.event_store.append(event)

    def subscribed_to_event_type(self) -> type[DomainEvent]:
        return DomainEvent
