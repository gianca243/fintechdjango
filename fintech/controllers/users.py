from fintech.domain.repository import UserRepository
from fintech.domain.user import User
from fintech.domain.exceptions import EmailIsRegistered, NotParamsProvided
from decimal import Decimal

class UserController:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, request_data: dict):
        # Logic to create a new user in the database
        name = request_data.get('name')
        email = request_data.get('email')

        user = User(
            name=name,
            email=email,
            balance= Decimal("0")
        )

        if self.user_repo.exists_by_email(email):
            raise EmailIsRegistered(email=email)
        
        new_user = self.user_repo.save(user)

        return new_user

    def get_data(self, request_data: dict):
        # Logic to retrieve user data from the database
        _id = request_data.get('id')
        if _id is None:
            raise NotParamsProvided('id')

        return self.user_repo.get_by_id(_id)