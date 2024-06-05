from sqlmodel import SQLModel, Field, Column, String, Integer
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import selectinload, Relationship
from sqlalchemy import event



class Group(SQLModel, table=True):
    id: int | None     = Field(primary_key=True, default=None)
    name: str          = Field(default='None')


class Users(SQLModel, table=True):
    id: int | None                 = Field(default=None, primary_key=True)
    first_name: str                = Field(default='NA')
    lastname: str                  = Field(default='NA')
    full_name: str | None          = None
    email: str                     = Field(index=True, unique=True)
    phoneno: str 
    password: str
    default_wallets: Optional[int] = None
    address1: str                  = Field(default='Address1')
    address2: str                  = Field(default='Address2')
    city: str                      = Field(default='City')
    state: str                     = Field(default='State')
    country: str                   = Field(default='Country')
    picture: str                   = Field(default='Picture')
    dogecoin_address: str          = Field(default='Doge Coin Address')
    bitcoin_address: str           = Field(default='Bitcoin Address')
    litcoin_address: str           = Field(default='Litcoin Address')
    is_merchent: bool              = Field(default=False)
    is_verified: bool              = Field(default=False,nullable=True)
    is_active: bool                = Field(default=False ,nullable=True)
    is_admin: bool                 = Field(default=False, nullable=True)
    is_suspended: bool             = Field(default=False, nullable=True)
    lastlogin: datetime            = Field(nullable=True)
    ipaddress: str                 = Field(default='0.0.0.0', nullable=True)
    group: int                     = Field(foreign_key='group.id', nullable=True)


    def assign_full_name(self):
        self.full_name = self.first_name + " " + self.lastname

    


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field()
    lastname: str = Field()
    email: str = Field(index=True, unique=True)    
    password: str
    picture: str = Field(default='Update it later')
    is_admin: bool = False


class Currency(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str      = Field(index=True)
    symbol: str
    fee : float = Field(default=0.0)
    decimal_places: int = Field



class Wallet(SQLModel, table=True):
    id: int | None         = Field(default=None, primary_key=True)
    user_id: int           = Field(foreign_key="users.id")
    currency_id: int       = Field(foreign_key="currency.id")
    currency: str          = Field(default='None', nullable=True)
    balance: float         = Field(default=0.0)
    is_active: bool        = Field(default=True)
    created_data: date     = Field(default=date.today(), nullable=True)
    wallet_id: str         = Field(nullable=True)

    def assign_wallet_id(self):
        wallet_id_mapping = {
            'USD': '1111-000-2222',
            'EUR': '4545-9090-6767',
            'INR': '1212-2323-8989',
            'GBP': '3030-4554-8998'
        }
        
        self.wallet_id = wallet_id_mapping.get(self.currency, '0000-0000-0000')
    # wallet_id
    # user: Optional[Users] = Relationship(back_populates="wallets")
    # currency: Optional[Cusrrency] = Relationship(back_populates="wallets")



class ReceiverDetails(SQLModel, table=True):
    id: int | None         = Field(default=None, primary_key=True)
    currency: int          = Field(foreign_key="currency.id", nullable=True)
    full_name: str         = Field(default='')
    email:str              = Field(default='')
    mobile_number: str     = Field(default='')
    amount: float          = Field(default=0.00, nullable=True)
    pay_via: str           = Field(default='')
    bank_name: str         = Field(default='', nullable=True)
    acc_number: str        = Field(default='', nullable=True)
    ifsc_code: str         = Field(default='', nullable=True)
    add_info: str          = Field(default='', nullable=True)
    address: str           = Field(default='', nullable=True)
    card_number: str       = Field(default='', nullable=True)
    card_cvv: str          = Field(default='', nullable=True)
    card_expiry: str       = Field(default='', nullable=True)


#Not used yet
class SenderDetails(SQLModel, table=True):
    id: int | None         = Field(default=None, primary_key=True)
    bank_name: str         = Field(default='', nullable=True)
    acc_number: str        = Field(default='', nullable=True)
    ifsc_code: str         = Field(default='', nullable=True)
    add_info: str          = Field(default='', nullable=True)
    address: str           = Field(default='', nullable=True)
    card_number: str       = Field(default='', nullable=True)
    card_cvv: str          = Field(default='', nullable=True)
    card_expiry: str       = Field(default='', nullable=True)




class Transection(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    txdid: str                  = Field(index=True, unique=True)
    txddate: date               = Field(default=date.today(), nullable=True)
    txdtime: str                = Field(default=datetime.now().strftime('%H:%M:%S'), nullable=True)
    amount: float               = Field(default_factory=0)
    txdcurrency: int            = Field(foreign_key="currency.id")
    txdfee: float               = Field(default=0.0)
    totalamount:float           = Field(default=0.0)
    txdrecever: int             = Field(foreign_key="users.id", default=None, nullable=True)
    txdmassage: str             = Field(default='message')
    txdstatus: str              = Field(default='Pending', nullable=True)
    payment_mode: str           = Field(default='None')
    txdtype: str                = Field(default='None')
    is_completed: bool          = Field(default=False, nullable=True)
    wallet_id: int              = Field(foreign_key='wallet.id', nullable=True)
    rec_currency: int           = Field(foreign_key="currency.id", nullable=True)
    rec_detail: int             = Field(foreign_key='receiverdetails.id', nullable=True)
    send_detail: int            = Field(foreign_key='senderdetails.id', nullable=True)
    rec_pay_mode: str           = Field(default='', nullable=True)
    credited_amount: int        = Field(nullable=True, default=0)
    credited_currency: str      = Field(nullable=True, default='')



class ExternalTransection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    txdid: str = Field(index=True, unique=True)
    txddate: datetime = Field(default=datetime.now())
    user_id: int = Field(foreign_key="users.id")
    txdtype: str  # deposit, withdraw, transfer
    amount: float
    txdfee: float
    totalamount:float = Field(default=0.0)
    txdcurrency: int = Field(foreign_key="currency.id")
    recipientcurrency: int = Field(foreign_key="currency.id")
    recipientfullname : str = Field(default='')
    recipientemail: str = Field(default='')
    recipientmobile: str = Field(default='')
    recipientbanktransfer: str = Field(default='')
    recipientbankname: str = Field(default='')
    recipientbankaccountno: str = Field(default='')
    recipientbankifsc: str = Field(default='')
    recipientaddress: str = Field(default='')
    
    
class Kycdetails(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    firstname: str
    lastname: str
    dateofbirth: date = Field(default=date.today())
    gander: str
    marital_status: str 
    email : str
    phoneno : str
    address: str
    landmark : str 
    city: str
    zipcode: str
    state: str
    country: str
    nationality: str
    id_type: str
    id_number: str
    id_expiry_date: date = Field(default=date.today())
    uploaddocument: str
    status: str = Field(default='Pending', nullable=True)
   

class RequestMoney(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    recipient_id: int = Field(foreign_key="users.id")
    amount: float
    currency_id: int = Field(foreign_key="currency.id")
    message: str = Field(default='')
    active: bool = Field(default=True)
    status: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.now())
    



class TestModel(SQLModel, table=True):
    id: int | None         = Field(default=None, primary_key=True)
    created_date: date     = Field(default=date.today())
    created_time: str      = Field(default=datetime.now().strftime('%H:%M:%S'), nullable=True)
    currency:  str         = Field(nullable=True)
    test_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None


    def assign_test_id(self):
        test_id_mapping = {
            'USD': '111-000-9090',
            'EUR': '222-900-3030',
            'INR': '123-870-2004'
        }
        
        self.test_id = test_id_mapping.get(self.currency, '0000-0000-0000')

    def assign_full_name(self):
        self.full_name = self.first_name + " " + self.last_name


@event.listens_for(TestModel, "before_insert")
def before_insert_listener(mapper, connection, target):
    target.assign_test_id()


@event.listens_for(TestModel, "before_insert")
def before_insert_listener(mapper, connection, target):
    target.assign_full_name()


@event.listens_for(Users, "before_insert")
def before_insert_listener(mapper, connection, target):
    target.assign_full_name()


@event.listens_for(Wallet, "before_insert")
def before_insert_listener(mapper, connection, target):
    target.assign_wallet_id()


    



# class TokenTable(SQLModel, table=True):
#     __tablename__ = "token"
#     # user_id = Column(Integer)
#     user_id = Column(Integer)
#     access_toke = Column(String(500), primary_key=True)
#     refresh_toke = Column(String(500),nullable=False)
    