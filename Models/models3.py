from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from sqlalchemy import event




# Payment Button Table
class MerchantPaymentButton(SQLModel, table=True):
    id: int | None              = Field(primary_key=True, default=None)
    merchant_id: int | None     = Field(foreign_key='users.id', default=None, index=True)
    button_id: str              = Field(unique=True, index=True)
    button_title: str           = Field(default='')
    businessName: str           = Field(default='Business Name')
    redirectURL: str            = Field(default='', nullable=True)
    isFixedAmount: bool         = Field(default=False, nullable=True)
    fixedAmountLabel: str       = Field(default='', nullable=True)
    fixedAmount: float          = Field(default=0.00, nullable=True)
    fixedAmountCurrency: str    = Field(default='', nullable=True)
    isCustomerAmount: bool      = Field(default=False, nullable=True)
    customerAmountLabel: str    = Field(default='', nullable=True)
    customerAmount: float       = Field(default=0.00, nullable=True)
    customerAmountCurrency: str = Field(default='', nullable=True)
    emailLabel: str             = Field(default='')
    phoneNoLable: str           = Field(default='')
    cretedAt: datetime          = Field(default=datetime.now(), nullable=True)
    is_active: bool             = Field(default=True, nullable=True)

    def assign_current_datetime(self):
        self.cretedAt = datetime.now()



# Payment Button styles table
class MerchantPaymentButtonStyles(SQLModel, table=True):
    id: int | None    = Field(primary_key=True, default=None)
    button_id: str    = Field(foreign_key='merchantpaymentbutton.button_id', index=True, unique=True)
    buttonLabel: str  = Field(default='Pay Now')
    buttonColor: str  = Field(default='white')
    buttonBgColor:str = Field(default='#2196f3')




# All merchant withdrawals
class MerchantWithdrawals(SQLModel, table=True):
    id: int | None         = Field(primary_key=True, default=None)
    merchant_id: int       = Field(foreign_key='users.id')
    bank_id: int           = Field(foreign_key='merchantbankaccount.id')
    amount: float          = Field(default=0.00)
    currency: int          = Field(foreign_key='currency.id', nullable=True)
    bank_currency: int     = Field(foreign_key='currency.id')
    createdAt: datetime    = Field(default=datetime.now())
    status: str            = Field(default='Pending', nullable=True) # Pending, Approved, Rejected
    is_completed: bool     = Field(default=False, nullable=True)
    is_active:bool         = Field(default=False) # not in use
    

    def AssigncreatedTime(self):
        self.createdAt = datetime.now()



# Merchant API Logs Table
class MerchantAPILogs(SQLModel, table=True):
    id: int | None             = Field(default=None, primary_key=True)
    merchant_id: int           = Field(foreign_key='users.id')
    createdAt: datetime        = Field(datetime.now())
    end_point: str             = Field(default='')
    error: str                 = Field(default='')
    request_header: str        = Field(default='')
    request_body: str          = Field(default='')
    response_header: str       = Field(default='')
    response_body: dict | None = Field(sa_column=Column(JSON), default={})

    def AssigncreatedTime(self):
        self.createdAt = datetime.now()



# Merchant Refund Transaction Table
class MerchantRefund(SQLModel, table=True):
    id: int | None               = Field(primary_key=True, default=None)
    merchant_id: int | None      = Field(foreign_key='users.id', default=None)
    transaction_id: int | None   = Field(foreign_key='merchantprodtransaction.id', default=None)
    amount: float                = Field(default=0.00)
    currency: int | None         = Field(foreign_key='currency.id')
    comment: str                 = Field(default=str)
    instant_refund: bool         = Field(default=False)
    instant_refund_amount: float = Field(default=0.00)
    createdAt: datetime          = Field(datetime.now())
    status: str                  = Field(default='Pending', nullable=True) ## Pending, Approved, on Hold, Rejected
    is_completed: bool           = Field(default=False)


    def AssigncreatedTime(self):
        self.createdAt = datetime.now()







# Auto assign current date and time when created
@event.listens_for(MerchantPaymentButton, 'before_insert')
def MerchantPaymentButton_time_listener(mapper, connection, target):
    target.assign_current_datetime()


# Auto assign Current date time when created
@event.listens_for(MerchantWithdrawals, 'before_insert')
def AssignWithdrawalTime(mapper, connection, target):
    target.AssigncreatedTime()


# Auto assign Current date time when created
@event.listens_for(MerchantRefund, 'before_insert')
def AssignRefundTime(mapper, connection, target):
    target.AssigncreatedTime()



# Auto assign Current date time when API Log created
@event.listens_for(MerchantAPILogs, 'before_insert')
def AssignAPILogTime(mapper, connection, target):
    target.AssigncreatedTime()


