# coding: utf-8
from typing import Callable, Iterable, Optional

from fastapi import Depends
from demo.iam.api.middleware import (
    get_current_user as _iam_get_current_user,
    require_any as _iam_require_any,
)
from demo.iam.application.jwt_encoder import UserContext as _IamUserContext
from demo.core.acl.user_context import UserContext


def _adapt(iam_user: _IamUserContext) -> UserContext:
    return UserContext(
        user_id=iam_user.user_id,
        role_names=iam_user.role_names,
        permission_codes=iam_user.permission_codes,
    )


def get_current_user(
    iam_user: _IamUserContext = Depends(_iam_get_current_user),
) -> UserContext:
    return _adapt(iam_user)


def require_any(
    roles: Optional[Iterable[str]] = None,
    permissions: Optional[Iterable[str]] = None,
) -> Callable:
    iam_checker = _iam_require_any(roles=roles, permissions=permissions)

    def checker(iam_user: _IamUserContext = Depends(iam_checker)) -> UserContext:
        return _adapt(iam_user)

    return checker
