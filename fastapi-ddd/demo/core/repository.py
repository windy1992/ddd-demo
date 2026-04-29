from abc import ABC
from typing import Generic, TypeVar
import uuid
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import BigInteger, Boolean, Column, DateTime, MetaData, Table
from sqlalchemy import select, exists, update, func, false


from demo.core.entity import BaseEntity


metadata = MetaData()
_slots = [
    ("created_at", DateTime),
    ("updated_at", DateTime),
    ("is_deleted", Boolean),
]


def create_table(name, *columns: Column):
    return Table(
        name,
        metadata,
        Column("id", BigInteger, primary_key=True, autoincrement=True),
        *columns,
        *[Column(c, t, nullable=False) for c, t in _slots],
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


T = TypeVar("T", bound=BaseEntity)


class BaseRepositoryMysql(ABC, Generic[T]):
    tl: Table

    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    def next_id(self) -> str:
        return str(uuid.uuid4())

    async def select_one(self, *conditions):
        stmt = self.tl.select().where(*conditions, self.tl.c.is_deleted == 0).limit(1)
        return (await self.conn.execute(stmt)).mappings().first()

    async def select_many(
        self,
        *conditions,
        limit: int | None = None,
        offset: int | None = None,
        order_by=None,
    ):
        stmt = self.tl.select().where(*conditions, self.tl.c.is_deleted == 0)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        return (await self.conn.execute(stmt)).mappings().fetchall()

    async def select_count(self, *conditions):
        stmt = (
            select(func.count())
            .select_from(self.tl)
            .where(*conditions, self.tl.c.is_deleted == 0)
        )
        return (await self.conn.execute(stmt)).scalar_one()

    async def select_exists(self, *conditions):
        stmt = select(exists().where(*conditions, self.tl.c.is_deleted == 0))
        return (await self.conn.execute(stmt)).scalar()

    async def upsert(self, values: dict):
        u_id = values["u_id"]

        # 1) 先查（不加锁）
        row = (
            await self.conn.execute(select(self.tl).where(self.tl.c.u_id == u_id))
        ).first()

        # 2) 查到了 → 只做 UPDATE
        if row:
            update_values = {
                k: v for k, v in values.items() if k not in ("id", "created_at")
            }
            await self.conn.execute(
                update(self.tl).where(self.tl.c.u_id == u_id).values(**update_values)
            )
            return

        # 3) 没查到 → 只做 INSERT
        await self.conn.execute(self.tl.insert().values(**values))

    def in_condition(self, column: Column, values: list):
        return column.in_(values) if values else false()

    def populate_extra_attrs(self, obj: T, data: dict) -> T:
        for c, _ in _slots:
            setattr(obj, c, data.get(c))
        return obj

    def dump_extra_attrs(self, obj: T, data: dict) -> dict:
        for c, _ in _slots:
            data[c] = getattr(obj, c)
        return data
