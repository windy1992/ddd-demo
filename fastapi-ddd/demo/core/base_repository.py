from typing import Generic, Protocol, TypeVar

from demo.core.entity import BaseEntity


T = TypeVar("T", bound=BaseEntity)


class BaseRepository(Protocol, Generic[T]):

    def next_id(self) -> str: ...

    async def list_all(self) -> list[T]: ...

    async def find_by_id(self, id: str) -> T | None: ...

    async def find_by_ids(self, ids: list[str]) -> list[T]: ...

    async def save(self, obj: T): ...
