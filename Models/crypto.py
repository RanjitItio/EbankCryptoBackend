from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event



## Crypto Wallet table
class CryptoWallet(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    wallet_address: str         = Field(nullable=True, default=None)
    created_At: datetime        = Field(default=datetime.now())
    crypto_name: str            = Field(default='', unique=True) # Crypto name
    balance: float              = Field(default=0.00)
    status: str                 = Field(default='Pending', nullable=True) ## Pending, Approved, Rejected
    is_approved: bool           = Field(default=False)

    def assign_current_datetime(self):
        self.created_At = datetime.now()




## Assign current date time when the transaction gets created
@event.listens_for(CryptoWallet, 'before_insert')
def assign_crypto_wallet_time_listener(mapper, connection, target):
    target.assign_current_datetime()