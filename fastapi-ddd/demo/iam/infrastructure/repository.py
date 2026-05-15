from demo.core.repository import BaseRepositoryMysql, create_table, unique_constraint
from demo.iam.domain.entity import (
    GrantedPermissions,
    PermissionBaseInfo,
    RoleBaseInfo,
    RoleInfo,
    RolePermission,
    User,
    Role,
    Permission,
    UserInfo,
    UserRole,
)

from sqlalchemy import Column, String, Index, bindparam, text

tl_user = create_table(
    "tl_user",
    Column("u_id", String(64), nullable=False, unique=True),
    Column("name", String(128), nullable=False),
    Column("password", String(255), nullable=False),
    unique_constraint("name"),
)

tl_role = create_table(
    "tl_role",
    Column("u_id", String(64), nullable=False, unique=True),
    Column("name", String(128), nullable=False),
    unique_constraint("name"),
)

tl_permission = create_table(
    "tl_permission",
    Column("u_id", String(64), nullable=False, unique=True),
    Column("code", String(128), nullable=False),
    unique_constraint("code"),
)


tl_user_role = create_table(
    "tl_user_role",
    Column("u_id", String(64), nullable=False, unique=True),
    Column("user_id", String(128), nullable=False),
    Column("role_id", String(128), nullable=False),
    Index("idx_user_id", "user_id"),
    Index("idx_role_id", "role_id"),
    unique_constraint("user_id", "role_id"),

)

tl_role_permission = create_table(
    "tl_role_permission",
    Column("u_id", String(64), nullable=False, unique=True),
    Column("role_id", String(128), nullable=False),
    Column("permission_id", String(128), nullable=False),
    Index("idx_role_id", "role_id"),
    Index("idx_permission_id", "permission_id"),
    unique_constraint("role_id", "permission_id"),
)


class UserRepositoryMysql(BaseRepositoryMysql[User]):
    tl = tl_user

    async def list_all(self) -> list[User]:
        rows = await self.select_many()

        return [self._from_row(r) for r in rows]

    async def find_by_id(self, id: str) -> User | None:

        row = await self.select_one(self.tl.c.u_id == id)
        if not row:
            return None

        return self._from_row(row)

    async def find_by_ids(self, ids: list[str]) -> list[User]:
        rows = await self.select_many(self.in_condition(self.tl.c.u_id, ids))

        return [self._from_row(r) for r in rows]

    async def find_by_name(self, name: str) -> User | None:
        row = await self.select_one(self.tl.c.name == name)
        if not row:
            return None

        return self._from_row(row)

    async def save(self, user: User):

        data = {
            "u_id": user.u_id,
            "name": user.name,
            "password": user.password,
        }

        await self.upsert(self.dump_extra_attrs(user, data))

    def _from_row(self, data: dict) -> User:
        return self.populate_extra_attrs(
            User(
                u_id=data["u_id"],
                name=data["name"],
                password=data["password"],
            ),
            data,
        )

    async def list_granted_permissions(self, user_name) -> GrantedPermissions | None:
        query = """
            SELECT 
                u.u_id As user_id,
                r.name AS role_name,
                p.code AS permission_code
            FROM tl_user u
            LEFT JOIN tl_user_role ur 
                ON u.u_id = ur.user_id
                AND ur.deleted_at = 0
            LEFT JOIN tl_role r 
                ON ur.role_id = r.u_id
                AND r.deleted_at = 0
            LEFT JOIN tl_role_permission rp 
                ON r.u_id = rp.role_id
                AND rp.deleted_at = 0
            LEFT JOIN tl_permission p 
                ON rp.permission_id = p.u_id
                AND p.deleted_at = 0
            WHERE u.name = :user_name
            AND u.deleted_at = 0;
        """
        granted_permissions = None
        for user_id, role_name, permission_code in (
            await self.conn.execute(text(query), {"user_name": user_name})
        ).all():
            if granted_permissions is None:
                granted_permissions = GrantedPermissions(
                    user_id=user_id, role_names=[], permission_codes=[]
                )

            if role_name and role_name not in granted_permissions.role_names:
                granted_permissions.role_names.append(role_name)

            if (
                permission_code
                and permission_code not in granted_permissions.permission_codes
            ):
                granted_permissions.permission_codes.append(permission_code)

        return granted_permissions

    async def list_user_info(self, name: str | None = None) -> list[UserInfo]:
        where_extra = ""
        params: dict[str, str] = {}
        if name is not None and name != "":
            where_extra = " AND u.name = :name_exact"
            params["name_exact"] = name
        query = f"""
            SELECT 
                u.u_id AS user_id,
                u.name AS user_name,
                r.u_id AS role_id,
                r.name AS role_name
            FROM tl_user u
            LEFT JOIN tl_user_role ur 
                ON u.u_id = ur.user_id
                AND ur.deleted_at = 0
            LEFT JOIN tl_role r 
                ON ur.role_id = r.u_id
                AND r.deleted_at = 0
            WHERE u.deleted_at = 0
            {where_extra};
        """
        users: dict[str, UserInfo] = {}

        for user_id, user_name, role_id, role_name in (
            await self.conn.execute(text(query), params)
        ).all():
            user = users.get(user_id)
            if user is None:
                user = UserInfo(user_id=user_id, user_name=user_name, roles=[])
                users[user_id] = user
            if role_id is not None:
                user.roles.append(RoleBaseInfo(role_id=role_id, role_name=role_name))

        return list(users.values())

    async def list_user_info_paged(
        self, offset: int, limit: int
    ) -> tuple[list[UserInfo], int]:
        total = (
            await self.conn.execute(
                text("SELECT COUNT(*) FROM tl_user u WHERE u.deleted_at = 0")
            )
        ).scalar_one()

        id_rows = await self.conn.execute(
            text(
                """
            SELECT u.u_id FROM tl_user u
            WHERE u.deleted_at = 0
            ORDER BY u.id
            LIMIT :limit OFFSET :offset
            """
            ),
            {"limit": limit, "offset": offset},
        )
        user_ids = [row[0] for row in id_rows.all()]
        if not user_ids:
            return [], total

        detail_stmt = text(
            """
            SELECT
                u.u_id AS user_id,
                u.name AS user_name,
                r.u_id AS role_id,
                r.name AS role_name
            FROM tl_user u
            LEFT JOIN tl_user_role ur
                ON u.u_id = ur.user_id
                AND ur.deleted_at = 0
            LEFT JOIN tl_role r
                ON ur.role_id = r.u_id
                AND r.deleted_at = 0
            WHERE u.deleted_at = 0
            AND u.u_id IN :user_ids
            """
        ).bindparams(bindparam("user_ids", expanding=True))

        users: dict[str, UserInfo] = {}
        for user_id, user_name, role_id, role_name in (
            await self.conn.execute(detail_stmt, {"user_ids": user_ids})
        ).all():
            user = users.get(user_id)
            if user is None:
                user = UserInfo(user_id=user_id, user_name=user_name, roles=[])
                users[user_id] = user
            if role_id is not None:
                user.roles.append(RoleBaseInfo(role_id=role_id, role_name=role_name))

        return [users[uid] for uid in user_ids], total


class RoleRepositoryMysql(BaseRepositoryMysql[Role]):
    tl = tl_role

    async def list_all(self) -> list[Role]:
        rows = await self.select_many()

        return [self._from_row(r) for r in rows]

    async def find_by_id(self, id: str) -> Role | None:

        row = await self.select_one(self.tl.c.u_id == id)
        if not row:
            return None

        return self._from_row(row)

    async def find_by_ids(self, ids: list[str]) -> list[Role]:
        rows = await self.select_many(self.in_condition(self.tl.c.u_id, ids))

        return [self._from_row(r) for r in rows]

    async def save(self, role: Role):
        data = {
            "u_id": role.u_id,
            "name": role.name,
        }

        await self.upsert(self.dump_extra_attrs(role, data))

    def _from_row(self, data: dict) -> Role:
        return self.populate_extra_attrs(
            Role(
                u_id=data["u_id"],
                name=data["name"],
            ),
            data,
        )

    async def list_role_info(self, name: str | None = None) -> list[RoleInfo]:
        where_extra = ""
        params: dict[str, str] = {}
        if name is not None and name != "":
            where_extra = " AND r.name = :name_exact"
            params["name_exact"] = name
        query = f"""
            SELECT 
                r.u_id AS role_id,
                r.name AS role_name,
                p.u_id AS permission_id,
                p.code AS permission_code
            from tl_role r 
            LEFT JOIN tl_role_permission rp 
                ON r.u_id = rp.role_id
                AND rp.deleted_at = 0
            LEFT JOIN tl_permission p 
                ON rp.permission_id = p.u_id
                AND p.deleted_at = 0
            WHERE r.deleted_at = 0
            {where_extra};
        """
        roles: dict[str, RoleInfo] = {}

        for role_id, role_name, permission_id, permission_code in (
            await self.conn.execute(text(query), params)
        ).all():
            role = roles.get(role_id)
            if role is None:
                role = RoleInfo(role_id=role_id, role_name=role_name, permissions=[])
                roles[role_id] = role
            if permission_id is not None:
                role.permissions.append(
                    PermissionBaseInfo(
                        permission_id=permission_id, code=permission_code
                    )
                )

        return list(roles.values())

    async def list_role_info_paged(
        self, offset: int, limit: int
    ) -> tuple[list[RoleInfo], int]:
        total = (
            await self.conn.execute(
                text("SELECT COUNT(*) FROM tl_role r WHERE r.deleted_at = 0")
            )
        ).scalar_one()

        id_rows = await self.conn.execute(
            text(
                """
            SELECT r.u_id FROM tl_role r
            WHERE r.deleted_at = 0
            ORDER BY r.id
            LIMIT :limit OFFSET :offset
            """
            ),
            {"limit": limit, "offset": offset},
        )
        role_ids = [row[0] for row in id_rows.all()]
        if not role_ids:
            return [], total

        detail_stmt = text(
            """
            SELECT
                r.u_id AS role_id,
                r.name AS role_name,
                p.u_id AS permission_id,
                p.code AS permission_code
            FROM tl_role r
            LEFT JOIN tl_role_permission rp
                ON r.u_id = rp.role_id
                AND rp.deleted_at = 0
            LEFT JOIN tl_permission p
                ON rp.permission_id = p.u_id
                AND p.deleted_at = 0
            WHERE r.deleted_at = 0
            AND r.u_id IN :role_ids
            """
        ).bindparams(bindparam("role_ids", expanding=True))

        roles: dict[str, RoleInfo] = {}
        for role_id, role_name, permission_id, permission_code in (
            await self.conn.execute(detail_stmt, {"role_ids": role_ids})
        ).all():
            role = roles.get(role_id)
            if role is None:
                role = RoleInfo(role_id=role_id, role_name=role_name, permissions=[])
                roles[role_id] = role
            if permission_id is not None:
                role.permissions.append(
                    PermissionBaseInfo(
                        permission_id=permission_id, code=permission_code
                    )
                )

        return [roles[rid] for rid in role_ids], total


class PermissionRepositoryMysql(BaseRepositoryMysql[Permission]):
    tl = tl_permission

    async def list_all(self, code: str | None = None) -> list[Permission]:
        if code is not None and code != "":
            rows = await self.select_many(self.tl.c.code == code)
        else:
            rows = await self.select_many()

        return [self._from_row(r) for r in rows]

    async def list_paged(self, offset: int, limit: int) -> tuple[list[Permission], int]:
        total = await self.select_count()
        rows = await self.select_many(
            limit=limit, offset=offset, order_by=self.tl.c.id.asc()
        )
        return [self._from_row(r) for r in rows], total

    async def find_by_id(self, id: str) -> Permission | None:
        row = await self.select_one(self.tl.c.u_id == id)
        if not row:
            return None

        return self._from_row(row)

    async def find_by_ids(self, ids: list[str]) -> list[Permission]:
        rows = await self.select_many(self.in_condition(self.tl.c.u_id, ids))

        return [self._from_row(r) for r in rows]

    async def save(self, p: Permission):

        data = {
            "u_id": p.u_id,
            "code": p.code,
        }

        await self.upsert(
            self.dump_extra_attrs(p, data),
        )

    def _from_row(self, data: dict) -> Permission:
        return self.populate_extra_attrs(
            Permission(
                u_id=data["u_id"],
                code=data["code"],
            ),
            data,
        )


class UserRoleRepositoryMysql(BaseRepositoryMysql[UserRole]):
    tl = tl_user_role

    async def list_all(self) -> list[UserRole]:
        rows = await self.select_many()

        return [self._from_row(r) for r in rows]

    async def find_by_id(self, id: str) -> UserRole | None:
        row = await self.select_one(self.tl.c.u_id == id)
        if not row:
            return None

        return self._from_row(row)

    async def find_by_ids(self, ids: list[str]) -> list[UserRole]:
        rows = await self.select_many(self.in_condition(self.tl.c.u_id, ids))

        return [self._from_row(r) for r in rows]

    async def save(self, ur: UserRole):

        data = {"u_id": ur.u_id, "user_id": ur.user_id, "role_id": ur.role_id}

        await self.upsert(
            self.dump_extra_attrs(ur, data),
        )

    def _from_row(self, data: dict) -> UserRole:
        return self.populate_extra_attrs(
            UserRole(
                u_id=data["u_id"], user_id=data["user_id"], role_id=data["role_id"]
            ),
            data,
        )

    async def find_by_user_id_and_role_id(
        self, user_id: str, role_id: str
    ) -> UserRole | None:
        row = await self.select_one(
            self.tl.c.user_id == user_id, self.tl.c.role_id == role_id
        )
        if not row:
            return None

        return self._from_row(row)

    async def list_active_by_user_id(self, user_id: str) -> list[UserRole]:
        rows = await self.select_many(self.tl.c.user_id == user_id)
        return [self._from_row(r) for r in rows]

    async def list_active_by_role_id(self, role_id: str) -> list[UserRole]:
        rows = await self.select_many(self.tl.c.role_id == role_id)
        return [self._from_row(r) for r in rows]

    async def exists_active_by_role_id(self, role_id: str) -> bool:
        return await self.select_exists(self.tl.c.role_id == role_id)


class RolePermissionRepositoryMysql(BaseRepositoryMysql[RolePermission]):
    tl = tl_role_permission

    async def list_all(self) -> list[RolePermission]:
        rows = await self.select_many()

        return [self._from_row(r) for r in rows]

    async def find_by_id(self, id: str) -> RolePermission | None:
        row = await self.select_one(self.tl.c.u_id == id)
        if not row:
            return None

        return self._from_row(row)

    async def find_by_ids(self, ids: list[str]) -> list[RolePermission]:
        rows = await self.select_many(self.in_condition(self.tl.c.u_id, ids))

        return [self._from_row(r) for r in rows]

    async def save(self, rp: RolePermission):

        data = {
            "u_id": rp.u_id,
            "role_id": rp.role_id,
            "permission_id": rp.permission_id,
        }

        await self.upsert(
            self.dump_extra_attrs(rp, data),
        )

    def _from_row(self, data: dict) -> RolePermission:
        return self.populate_extra_attrs(
            RolePermission(
                u_id=data["u_id"],
                role_id=data["role_id"],
                permission_id=data["permission_id"],
            ),
            data,
        )

    async def find_by_role_id_and_permission_id(
        self, role_id: str, permission_id: str
    ) -> RolePermission | None:
        row = await self.select_one(
            self.tl.c.role_id == role_id, self.tl.c.permission_id == permission_id
        )
        if not row:
            return None

        return self._from_row(row)

    async def list_active_by_role_id(self, role_id: str) -> list[RolePermission]:
        rows = await self.select_many(self.tl.c.role_id == role_id)
        return [self._from_row(r) for r in rows]

    async def exists_active_by_permission_id(self, permission_id: str) -> bool:
        return await self.select_exists(self.tl.c.permission_id == permission_id)
