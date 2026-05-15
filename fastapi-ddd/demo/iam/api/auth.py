from typing import Annotated
from fastapi import APIRouter, Body, Depends, Form, Path, Query
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncConnection

from demo.core.event_store import get_async_conn_and_sub_event
from demo.iam.api.middleware import require_any
from demo.iam.application import (
    IamService,
    PermissionBaseInfoDTO,
    RoleInfoDTO,
    Token,
    UserInfoDTO,
)
from demo.util.pagination import PaginatedDTO
from demo.util.text import optional_search
from demo.iam.application.jwt_encoder import UserContext

router = APIRouter(prefix="/auth", tags=["auth"])


class UserInfo(BaseModel):
    username: str = Field(..., min_length=1, strip_whitespace=True, description="用户名")
    password: str = Field(..., min_length=1, strip_whitespace=True)


@router.post("/login")
async def login(
    username: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = Form(...),
    password: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = Form(...),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
) -> Token:
    iam_service = IamService(conn)

    return await iam_service.login(username, password)


@router.post("/user")
async def register_user(
    req: UserInfo, conn: AsyncConnection = Depends(get_async_conn_and_sub_event)
):
    iam_service = IamService(conn)

    return await iam_service.register_user(req.username, req.password)


@router.get("/users", response_model=list[UserInfoDTO] | PaginatedDTO[UserInfoDTO])
async def list_user(
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=200),
    name: str | None = Query(
        None, description="用户名精确匹配，仅在非分页（不传 page_size）时生效"
    ),
):
    iam_service = IamService(conn)
    if page_size is None:
        return await iam_service.list_user(name=optional_search(name))
    return await iam_service.list_user_paged(page, page_size)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str = Path(...),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)
    await iam_service.delete_user(user_id)


@router.post("/role")
async def new_role(
    role_name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.new_role(role_name)


@router.get("/roles", response_model=list[RoleInfoDTO] | PaginatedDTO[RoleInfoDTO])
async def list_role(
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=200),
    name: str | None = Query(
        None, description="角色名精确匹配，仅在非分页（不传 page_size）时生效"
    ),
):
    iam_service = IamService(conn)
    if page_size is None:
        return await iam_service.list_role(name=optional_search(name))
    return await iam_service.list_role_paged(page, page_size)


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: str = Path(...),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)
    await iam_service.delete_role(role_id)


@router.post("/permission")
async def new_permission(
    code: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.new_permission(code)


@router.get(
    "/permissions",
    response_model=list[PermissionBaseInfoDTO]
    | PaginatedDTO[PermissionBaseInfoDTO],
)
async def list_permission(
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=200),
    code: str | None = Query(
        None, description="权限 code 精确匹配，仅在非分页（不传 page_size）时生效"
    ),
):
    iam_service = IamService(conn)
    if page_size is None:
        return await iam_service.list_permission(code=optional_search(code))
    return await iam_service.list_permission_paged(page, page_size)


@router.delete("/permissions/{permission_id}", status_code=204)
async def delete_permission(
    permission_id: str = Path(...),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)
    await iam_service.delete_permission(permission_id)


@router.post("/users/{user_id}/roles")
async def assign_roles_to_user(
    user_id: str = Path(...),
    role_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.assign_roles_to_user(user_id, role_ids)


@router.delete("/users/{user_id}/roles")
async def revoke_roles_from_user(
    user_id: str = Path(...),
    role_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.revoke_roles_from_user(user_id, role_ids)


@router.post("/roles/{role_id}/permissions")
async def assign_permission_to_role(
    role_id: str = Path(...),
    permission_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.assign_permissions_to_role(role_id, permission_ids)


@router.delete("/roles/{role_id}/permissions")
async def revoke_permissions_from_role(
    role_id: str = Path(...),
    permission_ids: list[str] = Body(..., embed=True),
    conn: AsyncConnection = Depends(get_async_conn_and_sub_event),
    user: UserContext = Depends(require_any(roles=["admin"])),
):
    iam_service = IamService(conn)

    return await iam_service.revoke_permissions_from_role(role_id, permission_ids)
