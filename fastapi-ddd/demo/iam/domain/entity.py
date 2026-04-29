# coding: utf-8
from pydantic import BaseModel

from demo.core.entity import BaseEntity


class User(BaseEntity):
    def __init__(
        self,
        u_id: str,
        name: str,
        password: str,
    ):
        super().__init__(u_id)

        self.name = name
        self.password = password

    def assign_role(self, user_role_id: str, role: "Role") -> "UserRole":
        return UserRole(user_role_id, self.u_id, role.u_id)


class Role(BaseEntity):

    def __init__(
        self,
        u_id: str,
        name: str,
    ):
        super().__init__(u_id)

        self.name = name

    def assign_permission(
        self, role_permission_id, permission: "Permission"
    ) -> "RolePermission":
        return RolePermission(role_permission_id, self.u_id, permission.u_id)


class Permission(BaseEntity):

    def __init__(
        self,
        u_id: str,
        code: str,
    ):
        super().__init__(u_id)

        self.code = code


class UserRole(BaseEntity):

    def __init__(self, u_id: str, user_id: str, role_id: str):
        super().__init__(u_id)

        self.user_id = user_id
        self.role_id = role_id

    def revoke(self):
        self.delete()


class RolePermission(BaseEntity):
    def __init__(self, u_id, role_id: str, permission_id: str):
        super().__init__(u_id)

        self.role_id = role_id
        self.permission_id = permission_id

    def revoke(self):
        self.delete()


class GrantedPermissions(BaseModel):
    user_id: str
    role_names: list[str]
    permission_codes: list[str]


class UserBaseInfo(BaseModel):
    user_id: str
    user_name: str


class UserInfo(UserBaseInfo):
    roles: list["RoleBaseInfo"]


class RoleBaseInfo(BaseModel):
    role_id: str
    role_name: str


class RoleInfo(RoleBaseInfo):
    permissions: list["PermissionBaseInfo"]


class PermissionBaseInfo(BaseModel):
    permission_id: str
    code: str
