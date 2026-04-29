class BaseAppException(Exception):
    """所有业务异常基类"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ValueErrorException(BaseAppException):
    pass
