from fastapi import APIRouter, Body, Depends, Form, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncConnection

from demo.iam.api.middleware import require_any
from demo.iam.application import (
    IamService,
    PermissionBaseInfoDTO,
    RoleInfoDTO,
    Token,
    UserInfoDTO,
)
from demo.core.db import get_async_conn
from demo.iam.application.jwt_encoder import UserContext

router = APIRouter(prefix="/auth", tags=["auth"])


class UserInfo(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(
    username=Form(...),
    password=Form(...),
    conn: AsyncConnection = Depends(get_async_conn),
) -> Token:
    iam_service = IamService(conn)

    return await iam_service.login(username, password)


@router.post("/user")
async def register_user(req: UserInfo, conn: AsyncConnection = Depends(get_async_conn)):
    iam_service = IamService(conn)

    return await iam_service.register_user(req.username, req.password)


@router.get("/users", response_model=list[UserInfoDTO])
async def list_user(
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.list_user()


@router.post("/role")
async def new_role(
    role_name: str = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.new_role(role_name)


@router.get("/roles", response_model=list[RoleInfoDTO])
async def list_role(
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.list_role()


@router.post("/permission")
async def new_permission(
    code: str = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.new_permission(code)


@router.get("/permissions", response_model=list[PermissionBaseInfoDTO])
async def list_permission(
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.list_permission()


@router.post("/users/{user_name}/roles")
async def assign_roles_to_user(
    user_name: str = Path(...),
    role_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.assign_roles_to_user(user_name, role_ids)


@router.delete("/users/{user_id}/roles")
async def revoke_roles_from_user(
    user_id: str = Path(...),
    role_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.revoke_roles_from_user(user_id, role_ids)


@router.post("/roles/{role_id}/permissions")
async def assign_permission_to_role(
    role_id: str = Path(...),
    permission_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.assign_permissions_to_role(role_id, permission_ids)


@router.delete("/roles/{role_id}/permissions")
async def revoke_permissions_from_role(
    role_id: str = Path(...),
    permission_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.revoke_permissions_from_role(role_id, permission_ids)
