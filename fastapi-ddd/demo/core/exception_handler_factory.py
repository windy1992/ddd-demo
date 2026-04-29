from fastapi import Request
from fastapi.responses import JSONResponse

from demo.core.error import BaseAppException


def http_exception_handler_factory(http_code: str):
    async def exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=http_code,
            content={
                "code": exc.code,
                "message": exc.message,
            },
        )

    return exception_handler
