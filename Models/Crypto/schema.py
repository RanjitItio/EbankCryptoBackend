from dataclasses import dataclass



@dataclass
class CreateWalletRequestSchema:
    crypto: str


@dataclass
class UpdateAdminCryptoWalletSchema:
    wallet_id: int
    status: str
    