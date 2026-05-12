from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from demo.core.error.error import ValueErrorException
from demo.core.error.exception_handler_factory import http_exception_handler_factory
from demo.core.observability import instrument_app, uninstrument_app
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


def include_router(app: FastAPI):
    iam.router_register_to(app)


def add_exception_handler(app: FastAPI):
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(ValueErrorException, http_exception_handler_factory(400))
    iam.exception_handler_register_to(app)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_env()
    instrument_app(app)
    try:
        yield
    finally:
        uninstrument_app(app)

app = FastAPI(lifespan=lifespan)
include_router(app)
add_exception_handler(app)


if __name__ == "__main__":
    uvicorn.run("demo.main:app", host="0.0.0.0", port=8000, reload=True)
