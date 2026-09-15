from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    balance: Decimal
    id: Optional[int] = None