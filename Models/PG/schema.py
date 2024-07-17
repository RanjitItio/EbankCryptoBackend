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
    

@dataclass
class PGSandboxTransactionProcessSchema:
    request: str

@dataclass
class PGMerchantPipeCheckoutSchema:
    merchant_public_key: str
