from demo.iam.domain.error import AuthenticationException
from demo.iam.domain.repository import UserRepository
from demo.util.password.encoder import PasswordEncoder
from demo.iam.domain.entity import User


class AuthService:

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, username: str, password: str):

        user = User(
            self.user_repo.next_id(), username, PasswordEncoder.encode(password)
        )

        return await self.user_repo.save(user)

    async def login(self, username: str, password: str):

        user = await self.user_repo.find_by_name(username)

        if not user:
            raise AuthenticationException("user not found or bad credentials")

        if not PasswordEncoder.matches(password, user.password):
            raise AuthenticationException("user not found or bad credentials")
