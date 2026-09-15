from fintech.models.user import User

class UserController:
    def __init__(self, user: User):
        self.user = user

    def create_user(self, request_data):
        # Logic to create a new user in the database
        pass

    def get_data(self):
        # Logic to retrieve user data from the database
        return {
            "username": self.user.name,
            "email": self.user.email,
            "balance": self.user.balance
        }