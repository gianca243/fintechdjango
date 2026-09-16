from fintech.domain.repository import UserRepository
from fintech.domain.user import User
from decimal import Decimal

class UserController:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, request_data: dict):
        # Logic to create a new user in the database
        user = self.user_repo.save(
            User(
                name=request_data.get('name'),
                email=request_data.get('email'),
                balance= Decimal("0")
            )
        )
        return user

    def get_data(self):
        # Logic to retrieve user data from the database
        pass