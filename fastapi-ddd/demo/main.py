from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from demo.core.error import ValueErrorException
from demo.core.exception_handler_factory import http_exception_handler_factory
import demo.iam.api as iam
from demo.init_env import init_env


async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务繁忙，请稍后再试",
        },
    )


def include_router():
    iam.router_register_to(app)


def add_exception_handler():
    iam.exception_handler_register_to(app)


init_env()  # 初始化环境

app = FastAPI()
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(ValueErrorException, http_exception_handler_factory(400))
include_router()
add_exception_handler()


if __name__ == "__main__":
    uvicorn.run("demo.main:app", host="0.0.0.0", port=8000, reload=True)
