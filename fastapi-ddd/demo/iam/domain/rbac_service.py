from demo.iam.domain.error import (
    PermissionNotExistException,
    RoleNotExistException,
    UserNotExistException,
)
from demo.iam.domain.repository import (
    RolePermissionRepository,
    UserRepository,
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
)


class RbacService:

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        user_role_repo: UserRoleRepository,
        role_permission_repo: RolePermissionRepository,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.permission_repo = permission_repo
        self.user_role_repo = user_role_repo
        self.role_permission_repo = role_permission_repo

    async def assign_roles_to_user(self, user_name: str, role_ids: list[str]):
        user = await self.user_repo.find_by_name(user_name)
        if not user:
            raise UserNotExistException()
        for role_id in role_ids:
            role = await self.role_repo.find_by_id(role_id)
            if not role:
                raise RoleNotExistException(f"角色<{role_id}>不存在")

            await self.user_role_repo.save(
                user.assign_role(self.user_role_repo.next_id(), role)
            )

    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]):
        role = await self.role_repo.find_by_id(role_id)
        if not role:
            raise RoleNotExistException()
        for permission_id in permission_ids:
            permission = await self.permission_repo.find_by_id(permission_id)
            if not permission:
                raise PermissionNotExistException(f"权限<{permission_id}>不存在")
            await self.role_permission_repo.save(
                role.assign_permission(self.role_permission_repo.next_id(), permission)
            )
