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
        super().__init__("IAM_USER_EXISTS", message)


class UserNotExistException(ValueErrorException):

    def __init__(self, message: str = "用户不存在"):
        self.message = message
        super().__init__("IAM_USER_NOT_FOUND", message)


class RoleExistException(ValueErrorException):

    def __init__(self, message: str = "角色已存在"):
        self.message = message
        super().__init__("IAM_ROLE_EXISTS", message)


class RoleNotExistException(ValueErrorException):

    def __init__(self, message: str = "角色不存在"):
        self.message = message
        super().__init__("IAM_ROLE_NOT_FOUND", message)


class PermissionExistException(ValueErrorException):

    def __init__(self, message: str = "权限已存在"):
        self.message = message
        super().__init__("IAM_PERMISSION_EXISTS", message)


class PermissionNotExistException(ValueErrorException):

    def __init__(self, message: str = "权限不存在"):
        self.message = message
        super().__init__("IAM_PERMISSION_NOT_FOUND", message)


class RoleInUseException(ValueErrorException):
    """角色仍有关联用户时禁止删除"""

    def __init__(self, message: str = "角色已分配给用户，无法删除"):
        self.message = message
        super().__init__("IAM_ROLE_IN_USE", message)


class PermissionInUseException(ValueErrorException):
    """权限仍有关联角色时禁止删除"""

    def __init__(self, message: str = "权限已关联角色，无法删除"):
        self.message = message
        super().__init__("IAM_PERMISSION_IN_USE", message)
