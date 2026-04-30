from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from demo.core.db.mysql import get_async_conn
from demo.core.event_store.domain_event import DomainEventPublisher
from demo.core.event_store.stored_event import DefaultDomainEventSubscriber


async def get_async_conn_and_sub_event(
    conn: AsyncConnection = Depends(get_async_conn),
) -> AsyncIterator[AsyncConnection]:
    DomainEventPublisher.subscribe(DefaultDomainEventSubscriber(conn))
    yield conn
