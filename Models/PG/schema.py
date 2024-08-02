from typing import List, Optional, Dict
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
    fixedAmountLabel: str
    fixedAmount: float
    customerAmountLabel: str
    customerAmount: float
    customerEmailLabel: str
    customerPhoneLabel: str

    

