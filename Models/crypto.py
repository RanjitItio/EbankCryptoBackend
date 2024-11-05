from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event



class Cryptos(SQLModel, table=True):
        id: int | None       = Field(default=None, primary_key=True)
        created_At: datetime = Field(default=datetime.now())
        name: str            = Field(default='')

        def assign_current_datetime(self):
            self.created_At = datetime.now()


## Crypto Wallet table
class CryptoWallet(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id", index=True)
    wallet_address: str         = Field(nullable=True, default=None)
    created_At: datetime        = Field(default=datetime.now())
    crypto_name: str            = Field(default='', unique=False) # Crypto name
    balance: float              = Field(default=0.00)
    status: str                 = Field(default='Pending', nullable=True) ## Pending, Approved, Rejected
    is_approved: bool           = Field(default=False)

    def assign_current_datetime(self):
        self.created_At = datetime.now()



## Crypto Buy Transaction Table
class CryptoBuy(SQLModel, table=True):
    id: int | None         = Field(default=None, primary_key=True)
    user_id: int           = Field(foreign_key="users.id", index=True)
    crypto_wallet_id: int  = Field(foreign_key="cryptowallet.id")
    crypto_quantity: float = Field(default=0.00)
    payment_type: str      = Field(default='')
    wallet_id: int         = Field(default=None)
    buying_currency: str   = Field(default='')
    buying_amount: float   = Field(default=0.00)
    fee_id: int            = Field(foreign_key='feestructure.id', index=True, nullable=True)
    fee_value: float       = Field(default=0.00, nullable=True)
    created_at:datetime    = Field(default=datetime.now())
    status: str            = Field(default='Pending', nullable=True)
    is_approved: bool      = Field(default=False, nullable=True)


    def assign_current_datetime(self):
        self.created_at = datetime.now()



## Crypto Sell Transaction Table
class CryptoSell(SQLModel, table=True):
    id: int | None          = Field(default=None, primary_key=True)
    user_id: int            = Field(foreign_key="users.id", index=True)
    crypto_wallet_id: int   = Field(foreign_key="cryptowallet.id")
    crypto_quantity: float  = Field(default=0.00)
    payment_type: str       = Field(default='', nullable=True)
    wallet_id: int          = Field(default=None)
    received_amount: float  = Field(default=0.00, nullable=True)  ## Converted amount from crypto
    fee_id: int             = Field(foreign_key='feestructure.id', index=True, nullable=True)
    fee_value: float        = Field(default=0.00, nullable=True)
    created_at:datetime     = Field(default=datetime.now())
    status: str             = Field(default='', nullable=True)
    is_approved: bool       = Field(default=False, nullable=True)


    def assign_current_datetime(self):
        self.created_at = datetime.now()



### Crypto Swap Table
class CryptoSwap(SQLModel, table=True):
        id: int | None             = Field(default=None, primary_key=True)
        user_id: int               = Field(foreign_key="users.id", index=True)
        transaction_id: str        = Field(default='', nullable=True)
        from_crypto_wallet_id: int = Field(foreign_key="cryptowallet.id")
        to_crypto_wallet_id: int   = Field(foreign_key="cryptowallet.id")
        swap_quantity: float       = Field(default=0.00)
        credit_quantity: float     = Field(default=0.00)
        created_at:datetime        = Field(default=datetime.now())
        status: str                = Field(default='Pending', nullable=True)
        is_approved: bool          = Field(default=False, nullable=True)
        fee_value: float           = Field(default=0.00, nullable=True)


        def assign_current_datetime(self):
            self.created_at = datetime.now()



#### Crypto Exchange Table
class CryptoExchange(SQLModel, table=True):
    id: int | None                = Field(default=None, primary_key=True)
    user_id: int                  = Field(foreign_key="users.id", index=True)
    transaction_id: str           = Field(default='', nullable=True)
    crypto_wallet: int            = Field(foreign_key="cryptowallet.id")
    fiat_wallet: int              = Field(foreign_key="wallet.id")
    exchange_crypto_amount: float = Field(default=0.0)
    converted_fiat_amount: float  = Field(default=0.00)
    created_at:datetime           = Field(default=datetime.now())
    status: str                   = Field(default='Pending', nullable=True)  ### Approved, Pending, Cancelled, Hold
    is_approved: bool             = Field(default=False, nullable=True)
    fee_value: float              = Field(default=0.00, nullable=True)


    def assign_current_datetime(self):
        self.created_at = datetime.now()



## Assign current date time when the transaction gets created
@event.listens_for(CryptoWallet, 'before_insert')
def assign_crypto_wallet_time_listener(mapper, connection, target):
    target.assign_current_datetime()



## Assign current date time when the transaction gets created
@event.listens_for(CryptoSell, 'before_insert')
def assign_crypto_sell_time_listener(mapper, connection, target):
    target.assign_current_datetime()



## Assign current date time when the transaction gets created
@event.listens_for(CryptoBuy, 'before_insert')
def assign_crypto_buy_time_listener(mapper, connection, target):
    target.assign_current_datetime()



## Assign current date time when the transaction gets created
@event.listens_for(CryptoSwap, 'before_insert')
def assign_crypto_swap_time_listener(mapper, connection, target):
    target.assign_current_datetime()



## Assign current date time when the transaction gets created
@event.listens_for(Cryptos, 'before_insert')
def assign_crypto_time_listener(mapper, connection, target):
    target.assign_current_datetime()



## Assign current date time when the transaction gets created
@event.listens_for(CryptoExchange, 'before_insert')
def assign_crypto_exchange_time_listener(mapper, connection, target):
    target.assign_current_datetime()

