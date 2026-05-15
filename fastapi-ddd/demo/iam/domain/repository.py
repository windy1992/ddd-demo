from demo.iam.domain.entity import (
    GrantedPermissions,
    RoleInfo,
    RolePermission,
    User,
    Role,
    Permission,
    UserInfo,
    UserRole,
)
from demo.core.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    async def find_by_name(self, name: str) -> User | None: ...

    async def list_granted_permissions(
        self, user_name
    ) -> GrantedPermissions | None: ...

    async def list_user_info(self, name: str | None = None) -> list[UserInfo]: ...

    async def list_user_info_paged(
        self, offset: int, limit: int
    ) -> tuple[list[UserInfo], int]: ...


class RoleRepository(BaseRepository[Role]):

    async def list_role_info(self, name: str | None = None) -> list[RoleInfo]: ...

    async def list_role_info_paged(
        self, offset: int, limit: int
    ) -> tuple[list[RoleInfo], int]: ...


class PermissionRepository(BaseRepository[Permission]):

    async def list_all(self, code: str | None = None) -> list[Permission]: ...

    async def list_paged(self, offset: int, limit: int) -> tuple[list[Permission], int]: ...


class UserRoleRepository(BaseRepository[UserRole]):
    async def find_by_user_id_and_role_id(
        self, user_id: str, role_id: str
    ) -> UserRole | None: ...

    async def list_active_by_user_id(self, user_id: str) -> list[UserRole]: ...

    async def exists_active_by_role_id(self, role_id: str) -> bool: ...


class RolePermissionRepository(BaseRepository[RolePermission]):
    async def find_by_role_id_and_permission_id(
        self, role_id: str, permission_id: str
    ) -> RolePermission | None: ...

    async def list_active_by_role_id(self, role_id: str) -> list[RolePermission]: ...

    async def exists_active_by_permission_id(self, permission_id: str) -> bool: ...
