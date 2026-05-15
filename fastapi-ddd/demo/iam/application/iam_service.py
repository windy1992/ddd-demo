import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from demo.iam.domain.auth_service import AuthService
from demo.iam.domain.entity import Permission, Role
from demo.iam.domain.error import (
    AuthenticationException,
    PermissionExistException,
    PermissionInUseException,
    PermissionNotExistException,
    RoleExistException,
    RoleInUseException,
    RoleNotExistException,
    UserExistException,
    UserNotExistException,
)
from demo.iam.domain.rbac_service import RbacService
from demo.iam.domain.repository import (
    RolePermissionRepository,
    UserRepository,
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
)

from demo.iam.infrastructure.repository import (
    RolePermissionRepositoryMysql,
    UserRepositoryMysql,
    RoleRepositoryMysql,
    PermissionRepositoryMysql,
    UserRoleRepositoryMysql,
)
from demo.iam.application.jwt_encoder import JwtEncoder, UserContext
from demo.util.pagination import PaginatedDTO, offset_for_page


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInfoDTO(BaseModel):
    user_id: str
    user_name: str
    roles: list["RoleBaseInfoDTO"]


class RoleBaseInfoDTO(BaseModel):
    role_id: str
    role_name: str


class RoleInfoDTO(RoleBaseInfoDTO):
    permissions: list["PermissionBaseInfoDTO"]


class PermissionBaseInfoDTO(BaseModel):
    permission_id: str
    code: str


class IamService:

    def __init__(self, conn: AsyncConnection):
        self.user_repo: UserRepository = UserRepositoryMysql(conn)
        self.role_repo: RoleRepository = RoleRepositoryMysql(conn)
        self.permission_repo: PermissionRepository = PermissionRepositoryMysql(conn)

        self.user_role_repo: UserRoleRepository = UserRoleRepositoryMysql(conn)
        self.role_permission_repo: RolePermissionRepository = (
            RolePermissionRepositoryMysql(conn)
        )

        self.auth_service: AuthService = AuthService(self.user_repo)
        self.rbac_service: RbacService = RbacService(
            self.user_repo,
            self.role_repo,
            self.permission_repo,
            self.user_role_repo,
            self.role_permission_repo,
        )

    async def login(self, username: str, password: str) -> Token:
        await self.auth_service.login(username, password)
        granted_permissions = await self.user_repo.list_granted_permissions(username)
        if granted_permissions is None:
            raise AuthenticationException("user not found or bad credentials")
        access_token = JwtEncoder.encode(
            UserContext(
                user_id=granted_permissions.user_id,
                role_names=granted_permissions.role_names,
                permission_codes=granted_permissions.permission_codes,
            )
        )

        return Token(access_token=access_token, token_type="bearer")

    async def register_user(self, username: str, password: str):
        try:
            await self.auth_service.register(username, password)
        except sqlalchemy.exc.IntegrityError as exc:
            raise UserExistException() from exc

    async def new_role(self, role_name: str):
        role = Role(self.role_repo.next_id(), role_name)
        try:
            await self.role_repo.save(role)
        except sqlalchemy.exc.IntegrityError as exc:
            raise RoleExistException() from exc

    async def new_permission(self, code: str):
        permission = Permission(self.permission_repo.next_id(), code)
        try:
            await self.permission_repo.save(permission)
        except sqlalchemy.exc.IntegrityError as exc:
            raise PermissionExistException() from exc

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]):
        await self.rbac_service.assign_roles_to_user(user_id, role_ids)

    async def revoke_roles_from_user(self, user_id: str, role_ids: list[str]):
        for role_id in role_ids:
            user_role = await self.user_role_repo.find_by_user_id_and_role_id(
                user_id, role_id
            )
            if user_role:
                await user_role.revoke()
                await self.user_role_repo.save(user_role)

    async def revoke_all_roles_from_user(self, user_id: str):
        user_roles = await self.user_role_repo.list_active_by_user_id(user_id)
        for user_role in user_roles:
            await user_role.revoke()
            await self.user_role_repo.save(user_role)

    async def assign_permissions_to_role(self, role_id: str, permission_ids: list[str]):
        await self.rbac_service.assign_permissions_to_role(role_id, permission_ids)

    async def revoke_permissions_from_role(
        self, role_id: str, permission_ids: list[str]
    ):
        for permission_id in permission_ids:
            role_permission = (
                await self.role_permission_repo.find_by_role_id_and_permission_id(
                    role_id, permission_id
                )
            )
            if role_permission:
                await role_permission.revoke()
                await self.role_permission_repo.save(role_permission)

    async def revoke_all_permissions_from_role(self, role_id: str):
        role_permissions = await self.role_permission_repo.list_active_by_role_id(role_id)
        for role_permission in role_permissions:
            await role_permission.revoke()
            await self.role_permission_repo.save(role_permission)
            
    async def delete_user(self, user_id: str):
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotExistException()
        await user.delete()
        await self.user_repo.save(user)

    async def delete_role(self, role_id: str):
        role = await self.role_repo.find_by_id(role_id)
        if not role:
            raise RoleNotExistException()
        if await self.user_role_repo.exists_active_by_role_id(role_id):
            raise RoleInUseException()
        await role.delete()
        await self.role_repo.save(role)

    async def delete_permission(self, permission_id: str):
        permission = await self.permission_repo.find_by_id(permission_id)
        if not permission:
            raise PermissionNotExistException()
        if await self.role_permission_repo.exists_active_by_permission_id(
            permission_id
        ):
            raise PermissionInUseException()
        await permission.delete()
        await self.permission_repo.save(permission)

    async def list_user(self, name: str | None = None) -> list[UserInfoDTO]:
        users = await self.user_repo.list_user_info(name=name)
        return [UserInfoDTO(**user.model_dump()) for user in users]

    async def list_role(self, name: str | None = None) -> list[RoleInfoDTO]:
        roles = await self.role_repo.list_role_info(name=name)
        return [RoleInfoDTO(**role.model_dump()) for role in roles]

    async def list_permission(self, code: str | None = None) -> list[PermissionBaseInfoDTO]:
        permissions = await self.permission_repo.list_all(code=code)
        return [
            PermissionBaseInfoDTO(permission_id=permission.u_id, code=permission.code)
            for permission in permissions
        ]

    async def list_user_paged(
        self, page: int, page_size: int
    ) -> PaginatedDTO[UserInfoDTO]:
        offset = offset_for_page(page, page_size)
        users, total = await self.user_repo.list_user_info_paged(offset, page_size)
        return PaginatedDTO[UserInfoDTO](
            items=[UserInfoDTO(**user.model_dump()) for user in users],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_role_paged(
        self, page: int, page_size: int
    ) -> PaginatedDTO[RoleInfoDTO]:
        offset = offset_for_page(page, page_size)
        roles, total = await self.role_repo.list_role_info_paged(offset, page_size)
        return PaginatedDTO[RoleInfoDTO](
            items=[RoleInfoDTO(**role.model_dump()) for role in roles],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def list_permission_paged(
        self, page: int, page_size: int
    ) -> PaginatedDTO[PermissionBaseInfoDTO]:
        offset = offset_for_page(page, page_size)
        permissions, total = await self.permission_repo.list_paged(offset, page_size)
        return PaginatedDTO[PermissionBaseInfoDTO](
            items=[
                PermissionBaseInfoDTO(permission_id=p.u_id, code=p.code)
                for p in permissions
            ],
            total=total,
            page=page,
            page_size=page_size,
        )
