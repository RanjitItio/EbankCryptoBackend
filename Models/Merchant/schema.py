from dataclasses import dataclass, field
from typing import Optional



@dataclass
class MerchantDetailSchema:
    merchant_id: int


@dataclass
class MerchantFormTransaction:
    item: str
    merchant_id: int
    order_id: str
    amount: int 
    pay_mode: str
    currency: str
