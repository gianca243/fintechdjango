from fintech.domain.user import User
from fintech.domain.exceptions import UserNotFound
class FakeUserRepository:
    def __init__(self):
        self._by_id = {}
        self._by_email = {}
        self.rows = 0

    def get_by_id(self, user_id: int) -> User:
        temp_result = self._by_id.get(str(user_id), None)
        if temp_result is None:
            raise UserNotFound(user_id, 'user_id')
        return self._to_domain_with_user(temp_result)

    def get_by_email(self, email: str) -> User:
        temp_result = self._by_email.get(str(email), None)
        if temp_result is None:
            raise UserNotFound(email, 'email')
        return self._to_domain_with_user(temp_result)

    def save(self, user: User) -> User:
        self.rows += 1
        user_id = user.id if user.id is not None else self.rows
        temp_result = dict(
            id= user_id,
            name=user.name,
            email=user.email,
            balance=user.balance
        )
        self._by_id[str(user_id)] = temp_result
        self._by_email[user.email] = temp_result
        return self._to_domain_with_user(temp_result)

    def exists_by_email(self, email: str) -> bool:
        return self._by_email.get(email) is not None

    def _to_domain_with_user(self, user_model: dict) -> User:
        return User(
            id=user_model.get('id'),
            name=user_model.get('name'),
            email=user_model.get('email'),
            balance=user_model.get('balance')
        )

class FakeTransactionRepository:
    pass