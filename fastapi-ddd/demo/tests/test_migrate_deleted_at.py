"""
迁移脚本：
  Step 1 - 将所有业务表的 is_deleted (TINYINT/Boolean) 字段
           改名并变更类型为 deleted_at (BIGINT, 默认 0)。
  Step 2 - 将旧的单列唯一约束替换为与 deleted_at 的组合唯一约束，
           并为关联表新增组合唯一约束。

涉及表：
  tl_user / tl_role / tl_permission / tl_user_role / tl_role_permission

执行方式：
  pytest demo/tests/test_migrate_deleted_at.py -s -v
"""
from demo.init_env import init_env

init_env()

from demo.core.db.mysql import get_async_engine
from sqlalchemy import text

import pytest

_TABLES = [
    "tl_user",
    "tl_role",
    "tl_permission",
    "tl_user_role",
    "tl_role_permission",
]

_ALTER_COLUMN_SQL = (
    "ALTER TABLE `{table}` "
    "CHANGE COLUMN `is_deleted` `deleted_at` BIGINT NOT NULL DEFAULT 0"
)

# Step 2: 旧单列唯一约束 → 新组合唯一约束
# 格式: (table, drop_index, new_constraint_name, new_columns)
# drop_index=None 表示原来没有单列唯一约束，只需新增
_UNIQUE_MIGRATIONS = [
    # ("tl_user",            "name",  "uq_name_deleted_at",            ("name",        "deleted_at")),
   # ("tl_role",            "name",  "uq_name_deleted_at",            ("name",        "deleted_at")),
    # ("tl_permission",      "code",  "uq_code_deleted_at",            ("code",        "deleted_at")),
    ("tl_user_role",       None,    "uq_user_id_role_id_deleted_at", ("user_id",     "role_id",     "deleted_at")),
    ("tl_role_permission", None,    "uq_role_id_permission_id_deleted_at", ("role_id", "permission_id", "deleted_at")),
]


@pytest.mark.asyncio
async def test_migrate_is_deleted_to_deleted_at():
    """Step 1: 字段改名 + 类型变更"""
    async with get_async_engine().begin() as conn:
        for table in _TABLES:
            await conn.execute(text(_ALTER_COLUMN_SQL.format(table=table)))
            print(f"  ✓ {table}.is_deleted → deleted_at BIGINT")


@pytest.mark.asyncio
async def test_migrate_unique_constraints():
    """Step 2: 重建唯一约束"""
    async with get_async_engine().begin() as conn:
        for table, drop_index, new_name, new_cols in _UNIQUE_MIGRATIONS:
            # 删除旧的单列唯一索引
            if drop_index:
                await conn.execute(
                    text(f"ALTER TABLE `{table}` DROP INDEX `{drop_index}`")
                )
                print(f"  ✓ {table}: DROP INDEX {drop_index}")

            # 添加新的组合唯一约束
            cols_sql = ", ".join(f"`{c}`" for c in new_cols)
            await conn.execute(
                text(
                    f"ALTER TABLE `{table}` "
                    f"ADD CONSTRAINT `{new_name}` UNIQUE ({cols_sql})"
                )
            )
            print(f"  ✓ {table}: ADD UNIQUE {new_name} ({', '.join(new_cols)})")
