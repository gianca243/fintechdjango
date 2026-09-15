from typing import Protocol
from fintech.domain.user import User

class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User:
        ...

    def get_by_email(self, email: str) -> User:
        ...

    def save(self, user: User) -> User:
        ...