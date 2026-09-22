import pytest
from fintech.domain.transaction import Direction, Status
from fintech.domain.user import User
from fintech.domain.exceptions import NotEnoughFunds
from decimal import Decimal

class TestUserDomain:
    def test_deposit_success(self):
        user = User(
            id=123,
            name='test',
            email='test@mail.com',
            balance=Decimal('0')
        )
        assert user.balance == 0
        transaction = user.deposit(
            amount=1000
        )
        assert user.balance == 1000
        assert transaction.direction.value == Direction.DEPOSIT.value
        assert transaction.status.value == Status.SUCCESS.value
        assert user.id == transaction.user_id

    def test_withdrawal_success(self):
        user = User(
            id=123,
            name='test',
            email='test@mail.com',
            balance=Decimal('1000')
        )
        withdrawal = user.withdraw(
            amount=500
        )
        assert withdrawal.direction.value == Direction.WITHDRAWAL.value
        assert user.balance == 500

    def test_withdrawal_without_funds(self):
        user = User(
            id=123,
            name='test',
            email='test@mail.com',
            balance=Decimal('0')
        )
        assert user.balance == 0
        with pytest.raises(NotEnoughFunds) as execinfo:
            user.withdraw(
                amount=500
            )
        assert execinfo.value.balance == 0
        assert execinfo.value.withdrawal_value == 500