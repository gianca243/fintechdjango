from fintech.domain.user import User
from fintech.models import User as UserModel
from fintech.domain.exceptions import UserNotFound, EmailIsRegistered

class DjangoUserRepository():

    def get_by_id(self, user_id: int) -> User:
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            raise UserNotFound(user_id, 'user_id')
        return self._to_domain(user)

    def get_by_email(self, email:str) -> User:
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise UserNotFound(email, 'email')
        return self._to_domain(user)

    def save(self, user:User) -> User:
        _user = UserModel(
            id=user.id,
            name=user.name,
            email=user.email,
            balance=user.balance
        )
        _user.save()
        return self._to_domain(_user)

    def exists_by_email(self, email: str) -> bool:
        return UserModel.objects.filter(email=email).exists()


    def _to_domain(self, user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            name=user_model.name,
            email=user_model.email,
            balance=user_model.balance
        )