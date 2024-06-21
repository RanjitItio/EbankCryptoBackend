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



@dataclass
class MerchantWalletPaymentFormSchema:
    merchant_key: str
    merchant_id: str
    product_name: str
    order_number: str
    amount: float
    custom: str
    currency: str
    email: str
    password: str


@dataclass
class MerchantArrearPaymentMethodSchema:
    merchant_key: str
    merchant_id: str
    card_number: str
    card_expiry: str
    cvc: str
    country: str
    currency: str
    amount: int
    pay_mode: str
    product: str
    order_id: str
    msg: Optional[str] = field(default='')



@dataclass
class AdminMerchantPaymentUpdateSchema:
    id: int
    status: str

