from typing import List, Optional, Dict
from dataclasses import dataclass, field



@dataclass
class AdminWithdrawalUpdateSchema:
    status: str
    withdrawal_id: int



@dataclass
class AdminUpdateMerchantRefundSchema:
    merchant_id: int
    refund_id: int
    transaction_id: str
    status: str

    