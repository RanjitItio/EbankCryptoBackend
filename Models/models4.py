from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import event



# All Deposit Transaction Model for FIAT
class DepositTransaction(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    transaction_id: str         = Field(index=True, unique=True)
    created_At: datetime        = Field(default=datetime.now())
    amount: float               = Field(default_factory=0.00)
    currency: int               = Field(foreign_key="currency.id")
    transaction_fee: float      = Field(default=0.00)
    payout_amount:float         = Field(default=0.0)
    status: str                 = Field(default='Pending', nullable=True) # Pending, Approved, Cancelled, Hold
    payment_mode: str           = Field(default='')
    is_completed: bool          = Field(default=False, nullable=True)
    selected_wallet: int        = Field(foreign_key='wallet.id', nullable=True)
    credited_amount: float      = Field(default=0.00 , nullable=True)
    credited_currency: str      = Field(nullable=True, default='')

    def assign_current_datetime(self):
        self.created_At = datetime.now()



# Transfer Transaction Model for FIAT
class TransferTransaction(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    transaction_id: str         = Field(index=True, unique=True)
    receiver: int               = Field(foreign_key="users.id", default=None, nullable=True)
    amount: float               = Field(default_factory=0.00)
    transaction_fee: float      = Field(default=0.00)
    payout_amount:float         = Field(default=0.0)
    currency: int               = Field(foreign_key="currency.id")
    massage: str                = Field(default='', nullable=True)
    status: str                 = Field(default='Pending', nullable=True) # Pending, Approved, Cancelled, Hold
    payment_mode: str           = Field(default='')
    receiver_payment_mode: str  = Field(default="", nullable=True)
    receiver_currency: int      = Field(foreign_key="currency.id", nullable=True)
    receiver_detail: int        = Field(foreign_key='receiverdetails.id', nullable=True)
    credited_amount: float      = Field(default=0.00 , nullable=True)
    credited_currency: str      = Field(nullable=True, default='')
    is_completed: bool          = Field(default=False, nullable=True)
    created_At: datetime        = Field(default=datetime.now())


    def assign_current_datetime(self):
        self.created_At = datetime.now()



# Withdrawal Model for FIAT
class FiatWithdrawalTransaction(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    transaction_id: str         = Field(index=True, unique=True)
    amount: float               = Field(default_factory=0.00)
    total_amount: float         = Field(default=0.00)   ## Total withdrawal amount including fee and withdrawal amount
    transaction_fee: float      = Field(default=0.00)
    wallet_currency: int        = Field(foreign_key="currency.id")  # Withdrawal Currency
    withdrawal_currency: int    = Field(foreign_key="currency.id")  # Convert Currency
    status: str                 = Field(default='Pending', nullable=True) # Pending, Approved, Cancelled, Hold, Success
    debit_currency: str         = Field(nullable=True, default='')  ## Selected wallet currency
    credit_amount: float        = Field(nullable=True, default=0.00) # Credit Amount
    credit_currency: str        = Field(nullable=True, default='')  ## Credited Currency
    is_completed: bool          = Field(default=False, nullable=True)
    created_At: datetime        = Field(default=datetime.now())


    def assign_current_datetime(self):
        self.created_At = datetime.now()



# Exchange Money table
class FIATExchangeMoney(SQLModel, table=True):
    id: int | None          = Field(default=None, primary_key=True)
    user_id: int            = Field(foreign_key="users.id")
    from_currency: int      = Field(foreign_key="currency.id")
    to_currency: int        = Field(foreign_key="currency.id")
    exchange_amount: float  = Field(default=0.00)
    converted_amount: float = Field(default=0.00)
    transaction_fee: float  = Field(default=0.00, nullable=True)
    status: str             = Field(default='Pending', nullable=True) # Approved, Pending, Cancelled, Hold
    is_completed: bool      = Field(default=False, nullable=True)
    created_At: datetime    = Field(default=datetime.now())


    def assign_current_datetime(self):
        self.created_At = datetime.now()





# Assign current date time when the transaction gets created
@event.listens_for(DepositTransaction, 'before_insert')
def assign_deposit_transaction_time_listener(mapper, connection, target):
    target.assign_current_datetime()


# Assign current date time when the transaction gets created
@event.listens_for(TransferTransaction, 'before_insert')
def assign_transfer_transaction_time_listener(mapper, connection, target):
    target.assign_current_datetime()


# Assign current date time when the transaction gets created
@event.listens_for(FiatWithdrawalTransaction, 'before_insert')
def assign_withdrawal_transaction_time_listener(mapper, connection, target):
    target.assign_current_datetime()

