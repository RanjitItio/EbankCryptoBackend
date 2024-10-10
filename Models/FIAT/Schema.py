from dataclasses import dataclass



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