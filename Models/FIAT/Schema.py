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

