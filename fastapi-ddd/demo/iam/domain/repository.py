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

    async def list_user_info(self) -> list[UserInfo]: ...


class RoleRepository(BaseRepository[Role]):

    async def list_role_info(self) -> list[RoleInfo]: ...


class PermissionRepository(BaseRepository[Permission]):
    pass


class UserRoleRepository(BaseRepository[UserRole]):
    async def find_by_user_id_and_role_id(
        self, user_id: str, role_id: str
    ) -> UserRole | None: ...


class RolePermissionRepository(BaseRepository[RolePermission]):
    async def find_by_role_id_and_permission_id(
        self, role_id: str, permission_id: str
    ) -> RolePermission | None: ...
