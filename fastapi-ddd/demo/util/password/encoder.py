from passlib.context import CryptContext


class PasswordEncoder:
    _ctx = CryptContext(schemes=["argon2"], deprecated="auto")

    @classmethod
    def encode(cls, raw: str) -> str:
        return cls._ctx.hash(raw)

    @classmethod
    def matches(cls, raw: str, hashed: str) -> bool:
        return cls._ctx.verify(raw, hashed)
