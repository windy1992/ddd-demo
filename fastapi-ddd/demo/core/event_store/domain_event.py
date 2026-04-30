from abc import ABC
from contextvars import ContextVar
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel


class DomainEvent(BaseModel):
    occurred_at: datetime


T = TypeVar("T", bound=DomainEvent)


class DomainEventSubscriber(ABC, Generic[T]):
    async def handle_event(self, event: T): ...

    def subscribed_to_event_type(self) -> type[T]: ...


class DomainEventPublisher:
    subscribers: ContextVar[list[DomainEventSubscriber] | None] = ContextVar(
        "subscribers",
    )

    @classmethod
    async def publish(cls, event: T):
        event_type = event.__class__

        coro_subscribers = cls.subscribers.get([])
        for sub in coro_subscribers:
            if sub.subscribed_to_event_type() in [event_type, DomainEvent]:
                await sub.handle_event(event)

    @classmethod
    def subscribe(cls, subscriber: DomainEventSubscriber):
        coro_subscribers = cls.subscribers.get([])
        if not coro_subscribers:
            coro_subscribers = [subscriber]
        else:
            coro_subscribers.append(subscriber)

        cls.subscribers.set(coro_subscribers)
