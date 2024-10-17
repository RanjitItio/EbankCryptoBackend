from dataclasses import dataclass



@dataclass
class CreateWalletRequestSchema:
    crypto: str


@dataclass
class UpdateAdminCryptoWalletSchema:
    wallet_id: int
    status: str


@dataclass
class BuyUserCryptoSchema:
    crypto_wallet_id: int
    payment_type: str
    wallet_id: int
    buy_amount: float
    converted_crypto_quantity: float


@dataclass
class SellUserCryptoSchema:
    selling_qty: float
    crypto_wallet_id: int
    payment_type: str
    wallet_id: int
    converted_amount: float



@dataclass
class AdminUpdateCryptoBuySchema:
    crypto_buy_id: int
    status: str


@dataclass
class AdminUpdateCryptoSellSchema:
    crypto_sell_id: int
    status: str

