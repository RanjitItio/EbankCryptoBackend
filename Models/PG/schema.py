from typing import Optional
from dataclasses import dataclass, field



class PGSandBoxPaymentInstrument:
    type: str


@dataclass
class PGSandBoxSchema:
    request: str


@dataclass
class PGProdSchema:
    request: str


@dataclass
class PGProdMasterCardSchema:
    request: str
    

# To receive payment details
@dataclass
class PGSandboxTransactionProcessSchema:
    request: str



@dataclass
class PGMerchantPipeCheckoutSchema:
    merchant_public_key: str



@dataclass
class AdminMerchantProductionTransactionUpdateSchema:
    transaction_id: str
    transaction_fee: float
    merchant_id: int
    amount: int
    currency: str
    payment_mode: str
    redirect_url: str
    webhook_url: str
    mobile_number: str
    payment_type: str
    status: str



@dataclass
class CreateNewPaymentButtonSchema:
    buttonTitle: str
    buttonColor: str
    buttonBGColor: str
    buttonLabel: str
    businessName: str

    redirectUrl: str
    
    isFixedAmount: bool
    fixedAmountLabel: str
    fixedAmount: float
    fixedAmtCurr: str

    isCustomerAmt: bool
    customerAmountLabel: str
    customerAmount: float
    customerAmtCurr: str
    
    customerEmailLabel: str
    customerPhoneLabel: str



@dataclass
class CreateMerchantWithdrawlSchma:
    bank_id: int
    bank_currency_id: int
    account_currency: str
    withdrawal_amount: float


@dataclass
class MerchantCreateRefundSchema:
    transaction_id: int
    refund_amt: float
    comment: Optional[str] = field(default='')


@dataclass
class UppdateUserProfileSchema:
    user_id: int
    first_name: str
    last_name: str
    contact_number : str
    email: str
    group: int


@dataclass
class FilterTransactionSchema:
    date: str           = field(default=None)
    order_id: str       = field(default=None)
    transaction_id: str = field(default=None)
    business_name: str  = field(default=None)


@dataclass
class FilterWithdrawalTransactionSchema:
    date: str = field(default=None)
    bank_name: str = field(default=None)
    withdrawal_currency: str = field(default=None)
    withdrawal_amount: float = field(default=None)



@dataclass
class FilterMerchantRefundSchema:
    date: str = field(default=None)
    transaction_id: str = field(default=None)
    refund_amount: float = field(default=None)

