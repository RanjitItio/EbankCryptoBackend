from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdminDepositTransactionFilterSchema:
    from_date: str
    to_date:   str
    currency:  Optional[str]  = field(default=None)
    status:    Optional[str]  = field(default=None)
    user_name: Optional[str]  = field(default=None)
    pay_mode:  Optional[str]  = field(default=None)


