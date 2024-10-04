from dataclasses import dataclass




@dataclass
class UpdateFiatWithdrawalsSchema:
    withdrawal_id: int
    converted_amount: float
    status: str

