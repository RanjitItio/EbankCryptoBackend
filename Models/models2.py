from pydantic import validator
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import date
from sqlalchemy import event
from typing import Optional
from datetime import datetime
import json
from sqlalchemy.ext.mutable import MutableDict






#2D, Wallet, 3D Card payements etc.
class PIPEChannelType(SQLModel, table=True):
    id: int | None  = Field(primary_key=True, default=None)
    name: str       = Field(default='')



#Direct, Redirect, Whitelisting etc.
class PIPEConnectionMode(SQLModel, table=True):
    id: int | None  = Field(primary_key=True, default=None)
    name: str       = Field(default='')


#Countries
class Country(SQLModel, table=True):
    id: int | None  = Field(primary_key=True, default=None)
    name: str       = Field(default='', index=True)


#Credit card, Debit Card, UPI etc.
class PIPEType(SQLModel, table=True):
    id: int | None  = Field(primary_key=True, default=None)
    name: str       = Field(default='')



# Acquirer Model
class PIPE(SQLModel, table=True):
    id: int | None          = Field(primary_key=True, default=None, index=True)
    name: str               = Field(default='')
    created_at: date        = Field(default=date.today(), nullable=True)
    status: str             = Field(default='Inactive')
    is_active: bool         = Field(default=False)
    payment_medium: str     = Field(default='', nullable=True) # Card, UPI, Net Banking, Wallet

    connection_mode: str    = Field(default='', nullable=True)  # Redirect(Get), POST, Curl, Whitelisting

    prod_url: str           = Field(default='', nullable=True)
    test_url: str           = Field(default='')
    status_url: str         = Field(default='', nullable=True)
    refund_url: str         = Field(default='', nullable=True)
    refund_policy: str      = Field(default='', nullable=True)  # Full, Manual, Partial etc.
    whitelist_domain: str   = Field(default='', nullable=True)
    whitelisting_ip: str    = Field(default='', nullable=True)
    webhook_url: str        = Field(default='', nullable=True)
    
    auto_refund: bool       = Field(default=False,  nullable=True)
   
    process_country: str    = Field(default='', nullable=True)
    block_country: str      = Field(default='', nullable=True)

    # Processing credentials
    headers: str            = Field(default='', nullable=True)
    body: str               = Field(default='', nullable=True)
    query: str              = Field(default='', nullable=True)
    auth_keys: str          = Field(default='', nullable=True)

    redirect_msg: str       = Field(default='', nullable=True)
    checkout_label: str     = Field(default='', nullable=True)
    checkout_sub_label: str = Field(default='', nullable=True)
    comments: str           = Field(default='', nullable=True)

    #Processing Mode
    process_mode: str       = Field(default='') #Test or live
    process_curr: int       = Field(foreign_key='currency.id')

    settlement_period: str  = Field(default='', nullable=True)  # Settlement period
    
    #Bank Response
    bank_max_fail_trans_allowed: int = Field(default=0, nullable=True)
    bank_down_period: str            = Field(default='', nullable=True)
    bank_success_resp: str           = Field(default='', nullable=True)
    bank_fail_resp: str              = Field(default='', nullable=True)
    bank_pending_res: str            = Field(default='', nullable=True)
    bank_status_path: str            = Field(default='', nullable=True)

    #Bank Transaction
    bank_min_trans_limit: int        = Field(default=0, nullable=True)
    bank_max_trans_limit: int        = Field(default=0, nullable=True)
    bank_scrub_period: str           = Field(default='', nullable=True)
    bank_trxn_count: int             = Field(default=0, nullable=True)
    bank_min_success_cnt: int        = Field(default=0,  nullable=True)
    bank_min_fail_count: int         = Field(default=0,  nullable=True)


    def assign_current_date(self):
        self.created_at = date.today()



# Pipe type association
class PIPETypeAssociation(SQLModel, table=True):
    pipe_id: Optional[int]      = Field(default=None, foreign_key="pipe.id", primary_key=True)
    pipe_type_id: Optional[int] = Field(default=None, foreign_key="pipetype.id", primary_key=True)



#Merchant Assigned pipe table
class MerchantPIPE(SQLModel, table=True):
    id: int | None    = Field(primary_key=True, default=None)
    merchant: int     = Field(foreign_key='users.id', index=True)
    pipe: int         = Field(foreign_key='pipe.id')
    fee: float        = Field(default=0.00)
    is_active: bool   = Field(default=False, nullable=True)
    assigned_on: date = Field(default=date.today(), nullable=True)

    def assign_current_date(self):
        self.assigned_on = date.today()


# All the transaction related to Sandbox
class MerchantSandBoxTransaction(SQLModel, table=True):
    id: int | None            = Field(primary_key=True, default=None)
    merchant_id: int | None   = Field(foreign_key='users.id', default=None, index=True)
    transaction_id: str       = Field(default='', nullable=True)
    status: str               = Field(default='')
    amount: int               = Field(default=0)
    currency: str             = Field(default='', nullable=True)
    payment_mode: str         = Field(default='', nullable=True)
    createdAt: datetime       = Field(default=datetime.now(), nullable=True)
    merchantOrderId: str     = Field(default='')
    merchantRedirectURl: str  = Field(default='', nullable=True)
    merchantRedirectMode: str = Field(default='', nullable=True)
    merchantCallBackURL: str  = Field(default='', nullable=True)
    merchantMobileNumber: str = Field(default='', nullable=True)
    merchantPaymentType: str  = Field(default='', nullable=True)
    business_name: str        = Field(default='', nullable=True)
    is_completd: bool         = Field(default=False)


    def assignTransactionCreatedDate(self):
        self.createdAt = datetime.now()




# All the transaction related to Production
class MerchantProdTransaction(SQLModel, table=True):
    id: int | None            = Field(primary_key=True, default=None)
    merchant_id: int | None   = Field(foreign_key='users.id', default=None, index=True)
    pipe_id: int | None       = Field(foreign_key='pipe.id', default=None, index=True)
    transaction_fee: float    = Field(default=0.00, nullable=True) # In Percentage
    fee_amount: float         = Field(default=0.00, nullable=True) # Positive Integer
    gateway_res: dict | None  = Field(sa_column=Column(JSON), default={})
    payment_mode: str | None  = Field(default='', nullable=True)
    transaction_id: str       = Field(default='', nullable=True, max_length=40, index=True)
    currency: str             = Field(default='', nullable=True)
    status: str               = Field(default='', index=True)
    amount: float             = Field(default=0.00)
    createdAt: datetime       = Field(default=datetime.now(), nullable=True)
    merchantOrderId: str      = Field(default='')
    merchantRedirectURl: str  = Field(default='', nullable=True)
    merchantRedirectMode: str = Field(default='', nullable=True)
    merchantCallBackURL: str  = Field(default='', nullable=True)
    merchantMobileNumber: str = Field(default='', nullable=True)
    merchantPaymentType: str  = Field(default='', nullable=True)
    business_name: str        = Field(default='', nullable=True)
    is_completd: bool         = Field(default=False)
    is_refunded: bool         = Field(default=False, nullable=True)
    settlement_period: str    = Field(max_length=10, default='', nullable=True)
    settlement_date: datetime = Field(nullable=True)
    balance_status: str       = Field(default='', nullable=True) # Track whether the amount is Mature or Immature


    def assignTransactionCreatedTime(self):
        current_time   = datetime.now()
        self.createdAt = current_time




# Steps for Sandbox
class MerchantSandBoxSteps(SQLModel, table=True):
    id: int | None      = Field(primary_key=True, default=None)
    merchantId: int     = Field(foreign_key='users.id', index=True)
    isBusiness: bool    = Field(default=False)
    isBank: bool        = Field(default=False)
    is_completed: bool  = Field(default=False)



# Merchant Account Balace after fee deduction
class MerchantAccountBalance(SQLModel, table=True):
    id: int | None          = Field(primary_key=True, default=None)
    merchant_id: int        = Field(foreign_key='users.id', index=True)
    mature_balance: float   = Field(default=0.00, nullable=True)
    immature_balance: float = Field(default=0.00, nullable=True)
    account_balance: float  = Field(default=0.00, nullable=True)
    currency: str           = Field(default='', index=True)
    last_updated: datetime  = Field(default=datetime.utcnow, nullable=True)


    def update_account_balance(self):
        self.account_balance = self.mature_balance + self.immature_balance




# All the collected fees of every transaction
class CollectedFees(SQLModel, table=True):
    id: int | None   = Field(primary_key=True, default=None)
    amount: float    = Field(default=0.00)
    currency: str    = Field(default='')







# Auto assign created date when row gets inserted into the table
@event.listens_for(PIPE, 'before_insert')
def pipe_created_date_listener(mapper, connection, target):
    target.assign_current_date()



# Auto assign created date when row gets inserted into the table
@event.listens_for(MerchantPIPE, 'before_insert')
def Merchant_pipe_assigned_date_listener(mapper, connection, target):
    target.assign_current_date()




# Auto assign created date when row gets inserted into the table
@event.listens_for(MerchantSandBoxTransaction, 'after_insert')
def Merchant_sandBox_transaction_date(mapper, connection, target):
    target.assignTransactionCreatedDate()




# Auto assign created time when row gets inserted into the table
@event.listens_for(MerchantProdTransaction, 'after_insert')
def Merchant_sandBox_transaction_time(mapper, connection, target):
    target.assignTransactionCreatedTime()
    



# Auto assign last update time while updating Account Balance
@event.listens_for(MerchantAccountBalance, 'before_update', propagate=True)
def account_balance_last_update_time(mapper, connection, target):
    target.last_updated = datetime.now()


# Auto assign last update time while updating Account Balance
@event.listens_for(MerchantAccountBalance, 'after_update', propagate=True)
def account_balance_update(mapper, connection, target):
    target.update_account_balance()

    # Persist the change to the account_balance back into the database
    connection.execute(
        mapper.local_table.update().where(mapper.local_table.c.id == target.id).values(
            account_balance=target.account_balance
        )
    )
