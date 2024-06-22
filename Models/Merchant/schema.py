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



@dataclass
class MerchantCreateBankAccountSchema:
    hldr_name: str
    hldr_add: str
    acc_no: str
    srt_code: str
    ifsc_code: str
    bnk_name: str
    bnk_add: str
    curr: str
    add_info: Optional[str] = field(default='')
    doc: Optional[bytes] = field(default=None)


@dataclass
class MerchantUpdateBankAccountSchema:
    mrc_bnk_id: int
    hldr_name: str
    hldr_add: str
    acc_no: str
    srt_code: str
    ifsc_code: str
    bnk_name: str
    bnk_add: str
    curr: str
    add_info: Optional[str] = field(default='')
    doc: Optional[bytes] = field(default=None)


@dataclass
class MerchantDeleteBankAccountSchema:
    mrc_bnk_id: int


@dataclass
class AdminMerchantBankApproveSchema:
    mrc_bnk_id: int
    user_id   : int
    status    : str


@dataclass
class AdminMerchantBanksSchema:
    mrc_bnk_id: int



