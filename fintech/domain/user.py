from decimal import Decimal
from typing import Optional
from dataclasses import dataclass
from fintech.domain.exceptions import NotAValidUser

@dataclass
class User:
    name: str
    email: str
    balance: Decimal
    id: Optional[int] = None

    def __post_init__(self):
        error_list = []
        if self.name == '' or self.name is None:
            error_list.append('name')
        if self.email == '' or self.email is None:
            error_list.append('email')

        if len(error_list) > 0:
            raise NotAValidUser(error_list)