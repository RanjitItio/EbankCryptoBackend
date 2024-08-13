from typing import List, Optional, Dict
from dataclasses import dataclass, field



@dataclass
class AdminWithdrawalUpdateSchema:
    status: str
    withdrawal_id: int
    