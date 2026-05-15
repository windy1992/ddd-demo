# coding: utf-8
from pydantic import BaseModel


class UserContext(BaseModel):
    user_id: str
    role_names: list[str]
    permission_codes: list[str]
