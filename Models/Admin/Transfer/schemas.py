from dataclasses import dataclass, field
from typing import Optional



@dataclass
class AdminTransferTransactionFilterSchema:
    from_date: str
    to_date:   str
    currency:  Optional[str]  = field(default=None)
    status:    Optional[str]  = field(default=None)
    user_name: Optional[str]  = field(default=None)


@dataclass
class AdminFilterTransferTransaction:
    date_time: str  = field(default=None)
    email: str      = field(default=None)
    status: str     = field(default=None)
    currency: str   = field(default=None)
