from dataclasses import dataclass


@dataclass
class AdminUpdateCryptoExchange:
    exchange_id: int
    status: str