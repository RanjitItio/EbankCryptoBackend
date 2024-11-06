from dataclasses import dataclass, field


@dataclass
class AdminUpdateCryptoExchange:
    exchange_id: int
    status: str


@dataclass
class AdminFilterCryptoExchangeSchema:
    dateTime: str    = field(default=None)
    email: str       = field(default=None)
    crypto: str      = field(default=None)
    status: str      = field(default=None)
    start_date: str  = field(default=None)
    end_date: str    = field(default=None)
