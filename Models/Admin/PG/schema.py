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


@dataclass
class AllTransactionFilterSchema:
    date: str  = field(default=None)
    transaction_id: str = field(default=None)
    transaction_amount: float = field(default=None)
    business_name: str = field(default=None)
    

@dataclass
class AllSandboxTransactionFilterSchema:
    date: str = field(default=None)
    transaction_id: str = field(default=None)
    transaction_amount: float = field(default=None)
    business_name: str = field(default=None)


@dataclass
class FilterMerchantWithdrawalsSchema:
    date: str = field(default=None)
    email: str = field(default=None)
    status: str = field(default=None)
    amount: float = field(default=None)



@dataclass
class FilterMerchantRefunds:
    date: str = field(default=None)
    email: str = field(default=None)
    currency: str = field(default=None)
    amount: float = field(default=None)



@dataclass
class FilterBusinsessPage:
    date: str = field(default=None)
    merchant_name: str = field(default=None)
    business_name: str = field(default=None)
    status: str = field(default=None)


@dataclass
class MerchantBalancePeriodUpdateSchema:
    merchant_id: int
    settlement_period: str
    minimum_withdrawal_amt: float
    