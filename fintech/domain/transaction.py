from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from enum import Enum
from datetime import datetime
from fintech.domain.exceptions import NotAValidValue

class Status(Enum):
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

class Direction(Enum):
    DEPOSIT = 'DEPOSIT'
    WITHDRAWAL = 'WITHDRAWAL'

@dataclass
class Transaction:
    user_id: int
    amount: Decimal
    status: Status
    direction: Direction
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def __post_init__(self):
        if self.amount <= 0:
            raise NotAValidValue(
                value=self.amount,
                key='amount',
                cause='we can not receive negative values or 0 values'
            )

