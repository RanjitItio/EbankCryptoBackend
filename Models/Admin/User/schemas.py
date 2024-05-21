from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class EachUserTransactionSchema:
    user_id: int



@dataclass
class TransactionSearchSchema:
    searched_text: str | float
    userid       : int


@dataclass
class EachUserWalletSchema:
    user_id: int



@dataclass
class UserTransactionFilterSchema:
    user_id:   int
    from_date: Optional[str] = field(default=None)
    to_date:   Optional[date] = field(default=None)
    currency:  Optional[str]  = field(default=None)
    status:    Optional[str]  = field(default=None)
    type:      Optional[str]  = field(default=None)
