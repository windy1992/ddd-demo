# coding: utf-8
from typing import AsyncIterator, Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncConnection

Engine: Optional[AsyncEngine] = None


def set_up(
    dsn: str, *, pool_size: int = 50, max_overflow: int = 10, pool_recycle: int = 3600
):
    global Engine

    Engine = create_async_engine(
        dsn,
        echo=False,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
    )


def get_async_engine() -> AsyncEngine:
    return Engine


async def get_async_conn() -> AsyncIterator[AsyncConnection]:
    async with get_async_engine().begin() as conn:
        yield conn
