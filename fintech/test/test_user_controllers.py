import pytest
from fintech.domain.user import User
from fintech.domain.exceptions import (
    UserNotFound, 
    EmailIsRegistered, 
    NotAValidUser,
    NotParamsProvided
)
from fintech.controllers.users import UserController
from fintech.test.fake_repository import FakeUserRepository

class TestUserController:
    def test_insert_user(self):
        user_controller = UserController(FakeUserRepository())
        user_result = user_controller.create_user({
            "name": 'test',
            "email": 'test@mail.com',
        })

        assert user_result.balance == 0
        assert user_result.name == 'test'
        assert user_result.email == 'test@mail.com'

    def test_email_is_already_registered(self):
        user_controller = UserController(FakeUserRepository())
        user_result = user_controller.create_user({
            "name": 'test',
            "email": 'test@mail.com',
        })

        assert user_result.balance == 0
        assert user_result.name == 'test'
        assert user_result.email == 'test@mail.com'

        with pytest.raises(EmailIsRegistered) as excinfo:
            user_result_2 = user_controller.create_user({
                "name": 'test2',
                "email": 'test@mail.com',
            })
        assert excinfo.value.email == 'test@mail.com'

    def test_user_does_not_have_attributes(self):
        user_controller = UserController(FakeUserRepository())
        with pytest.raises(NotAValidUser) as excinfo:
            user_controller.create_user({})

        assert excinfo.value.fields == ['name', 'email']

    def test_get_user(self):
        email = 'test@mail.com'
        user_controller = UserController(FakeUserRepository())
        new_user = user_controller.create_user({
            "name": 'test',
            "email": email,
        })
        result = user_controller.get_data({
            "id": new_user.id
        })

        assert result.id is not None
        assert isinstance(result.id, int)
        assert result.balance == 0
        assert result.name == 'test'
        assert result.email == email

    def test_get_user_without_id(self):
        user_controller = UserController(FakeUserRepository())
        with pytest.raises(NotParamsProvided):
            user_controller.get_data({})


