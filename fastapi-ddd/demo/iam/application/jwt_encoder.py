from jose import jwt
from pydantic import BaseModel
from demo.util.time import utc_after_hours

from demo.core.config import get_config


class UserContext(BaseModel):
    user_id: str
    role_names: list[str]
    permission_codes: list[str]


class JwtEncoder:

    @staticmethod
    def encode(user: UserContext) -> str:
        data = user.model_dump()
        token_config = get_config().token
        data["exp"] = int(utc_after_hours(token_config.expire_hours).timestamp())
        return jwt.encode(
            data, token_config.secret_key, algorithm=token_config.algorithm
        )

    @staticmethod
    def decode(token: str) -> UserContext:
        token_config = get_config().token
        data = jwt.decode(
            token, token_config.secret_key, algorithms=[token_config.algorithm]
        )
        data.pop("exp")
        return UserContext(**data)
