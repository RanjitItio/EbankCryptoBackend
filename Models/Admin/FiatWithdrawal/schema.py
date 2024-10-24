from dataclasses import dataclass, field




@dataclass
class UpdateFiatWithdrawalsSchema:
    withdrawal_id: int
    converted_amount: float
    status: str



@dataclass
class AdminFIATWithdrawalFilterSchema:
    date_time: str = field(default=None)
    email: str     = field(default=None)
    currency: str  = field(default=None)
    status: str    = field(default=None)
