from contextvars import ContextVar
from typing import Callable, Iterable, Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer


from demo.iam.application.exception_handler import (
    access_denied_exception_callback,
    authentication_exception_callback,
)
from demo.iam.application.jwt_encoder import (
    JwtEncoder,
    UserContext,
)

oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


class SecurityContext:
    _user: ContextVar[Optional[UserContext]] = ContextVar("user", default=None)

    @classmethod
    def set(cls, user: UserContext):
        cls._user.set(user)

    @classmethod
    def get(cls) -> Optional[UserContext]:
        return cls._user.get()


def get_current_user(token: str = Depends(oauth2)) -> UserContext:

    try:
        user_context = JwtEncoder.decode(token)

        SecurityContext.set(user_context)
        return user_context

    except Exception as exc:
        authentication_exception_callback(exc)


def require_any(
    roles: Optional[Iterable[str]] = None,
    permissions: Optional[Iterable[str]] = None,
) -> Callable:

    role_set = set(roles or [])
    perm_set = set(permissions or [])

    def checker(user: UserContext = Depends(get_current_user)) -> UserContext:

        if not role_set and not perm_set:
            return user

        # OR 逻辑
        has_role = bool(role_set.intersection(user.role_names))
        has_perm = bool(perm_set.intersection(user.permission_codes))

        if not (has_role or has_perm):
            access_denied_exception_callback()
        return user

    return checker
