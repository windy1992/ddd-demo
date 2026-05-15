# coding: utf-8

import time
from functools import wraps

from demo.util.time import utc_now


def auto_update_time(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)

        # 自动更新时间
        if hasattr(self, "updated_at"):
            self.touch()

        return result

    return wrapper


def auto_update_time_async(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        result = await func(self, *args, **kwargs)

        if hasattr(self, "updated_at"):
            self.touch()

        return result

    return wrapper


class BaseEntity:
    def __init__(
        self,
        u_id: str,
    ):

        self.u_id: str = u_id
        self.created_at = utc_now()
        self.updated_at = utc_now()

        self.deleted_at: int = 0

    def touch(self):
        """手动更新时间"""
        self.updated_at = utc_now()

    @auto_update_time_async
    async def delete(self):
        self.deleted_at = int(time.time() * 1000)
