# coding: utf-8
from demo.core.event_store.domain_event import DomainEvent


class UserDeleted(DomainEvent):
    user_id: str


class RoleDeleted(DomainEvent):
    role_id: str
