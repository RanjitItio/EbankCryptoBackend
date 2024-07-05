from sqlmodel import SQLModel, Field, Relationship
from Models.models import Currency
from datetime import date
from sqlalchemy import event
from typing import List, Optional



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
    name: str       = Field(default='')


#Credit card, Debit Card, UPI etc.
class PIPEType(SQLModel, table=True):
    id: int | None  = Field(primary_key=True, default=None)
    name: str       = Field(default='')




class PIPE(SQLModel, table=True):
    id: int | None          = Field(primary_key=True, default=None, index=True)
    name: str               = Field(default='')
    created_at: date        = Field(default=date.today(), nullable=True)
    status: str             = Field(default='Inactive')
    is_active: bool         = Field(default=False)

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



#Merchant Fee Connector wise
class MerchantPIPE(SQLModel, table=True):
    id: int | None    = Field(primary_key=True, default=None)
    merchant: int     = Field(foreign_key='users.id', index=True)
    pipe: int         = Field(foreign_key='pipe.id')
    fee: float        = Field(default=0.00)
    is_active: bool   = Field(default=False, nullable=True)
    assigned_on: date = Field(default=date.today(), nullable=True)

    def assign_current_date(self):
        self.assigned_on = date.today()




@event.listens_for(PIPE, 'before_insert')
def pipe_created_date_listener(mapper, connection, target):
    target.assign_current_date()



@event.listens_for(MerchantPIPE, 'before_insert')
def Merchant_pipe_assigned_date_listener(mapper, connection, target):
    target.assign_current_date()
    


