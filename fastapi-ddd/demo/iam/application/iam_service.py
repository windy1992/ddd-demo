from pydantic import BaseModel
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncConnection
from demo.iam.domain.auth_service import AuthService
from demo.iam.domain.entity import Permission, Role
from demo.iam.domain.error import (
    AuthenticationException,
    PermissionExistException,
    RoleExistException,
    UserExistException,
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
        permission = Permission(self.role_repo.next_id(), code)
        try:
            await self.permission_repo.save(permission)
        except sqlalchemy.exc.IntegrityError as exc:
            raise PermissionExistException() from exc

    async def assign_roles_to_user(self, user_name: str, role_ids: list[str]):
        await self.rbac_service.assign_roles_to_user(user_name, role_ids)

    async def revoke_roles_from_user(self, user_id: str, role_ids: list[str]):
        for role_id in role_ids:
            user_role = await self.user_role_repo.find_by_user_id_and_role_id(
                user_id, role_id
            )
            if user_role:
                user_role.revoke()
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
                role_permission.revoke()
                await self.role_permission_repo.save(role_permission)

    async def list_user(self) -> list[UserInfoDTO]:
        users = await self.user_repo.list_user_info()
        return [UserInfoDTO(**user.model_dump()) for user in users]

    async def list_role(self) -> list[RoleInfoDTO]:
        roles = await self.role_repo.list_role_info()
        return [RoleInfoDTO(**role.model_dump()) for role in roles]

    async def list_permission(self) -> list[PermissionBaseInfoDTO]:
        permissions = await self.permission_repo.list_all()
        return [
            PermissionBaseInfoDTO(permission_id=permission.u_id, code=permission.code)
            for permission in permissions
        ]
