from dataclasses import dataclass, field



@dataclass
class FiatExchangeMoneySchema:
    exchange_amount: float
    convert_amount: float
    fee: float
    from_currency: str
    to_currency: str


@dataclass
class AdminUpdateExchangeMoneySchema:
    exchange_money_id: int
    converted_amount: float
    status: str




@dataclass
class UpdateFiatCryptoUserProfileSchema:
    email: str
    phoneno: str
    full_name: str
    state: str
    city: str
    landmark: str
    zipcode: str
    country: str
    address: str
    nationality: str
    dob: str
    gender: str
    marital_status: str



@dataclass
class AdminAddFeeSchema:
    fee_name: str
    fee_type: str
    tax_rate: float
    fixed_value: float


@dataclass
class AdminAddFeeSchema:
    fee_name: str
    fee_type: str
    tax_rate: float
    fixed_value: float


@dataclass
class AdminUpdateFeeSchema:
    fee_id : int
    fee_name: str
    fee_type: str
    tax_rate: float
    fixed_value: float
