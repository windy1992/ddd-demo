from demo.core.error import BaseAppException, ValueErrorException


class AuthenticationException(BaseAppException):
    """
    认证失败：未登录 / token 无效 / token 过期
    对应 HTTP 401
    """

    def __init__(self, message: str = "认证失败"):
        self.message = message
        super().__init__("AUTH_401", message)


class AccessDeniedException(BaseAppException):
    """
    权限不足：已认证但无权限访问资源
    对应 HTTP 403
    """

    def __init__(self, message: str = "权限不足"):
        self.message = message
        super().__init__("AUTH_403", message)


class UserExistException(ValueErrorException):

    def __init__(self, message: str = "用户已存在"):
        self.message = message
        super().__init__("AUTH_400", message)


class UserNotExistException(ValueErrorException):

    def __init__(self, message: str = "用户不存在"):
        self.message = message
        super().__init__("AUTH_400", message)


class RoleExistException(ValueErrorException):

    def __init__(self, message: str = "角色已存在"):
        self.message = message
        super().__init__("AUTH_400", message)


class RoleNotExistException(ValueErrorException):

    def __init__(self, message: str = "角色不存在"):
        self.message = message
        super().__init__("AUTH_400", message)


class PermissionExistException(ValueErrorException):

    def __init__(self, message: str = "权限已存在"):
        self.message = message
        super().__init__("AUTH_400", message)


class PermissionNotExistException(ValueErrorException):

    def __init__(self, message: str = "权限不存在"):
        self.message = message
        super().__init__("AUTH_400", message)
