from sqlmodel import SQLModel, Field, Column, String, Integer
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import selectinload, Relationship
from typing import List



class Users(SQLModel, table=True):
    id: int | None                 = Field(default=None, primary_key=True)
    first_name: str                = Field(default='Default User First Name')
    lastname: str                  = Field(default='Default User Last Name')
    email: str                     = Field(index=True, unique=True)
    phoneno: str 
    password: str
    default_wallets: Optional[int] = None
    address1: str                  = Field(default='Update it later')
    address2: str                  = Field(default='Update it later')
    city: str                      = Field(default='Update it later')
    state: str                     = Field(default='Update it later')
    country: str                   = Field(default='Update it later')
    picture: str                   = Field(default='Update it later')
    dogecoin_address: str          = Field(default='Update it later')
    bitcoin_address: str           = Field(default='Update it later')
    litcoin_address: str           = Field(default='Update it later')
    is_merchent: bool              = Field(default=False)
    is_verified: bool              = Field(default=False,nullable=True)
    is_active: bool                = Field(default=False ,nullable=True)
    is_admin: bool                 = Field(default=False, nullable=True)

    


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
    name: str
    symbol: str
    fee : float = Field(default=0.0)
    decimal_places: int = Field



class Wallet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    currency_id: int = Field(foreign_key="currency.id")
    currency: str     = Field(default='None', nullable=True)
    balance: float = Field(default=0.0)
    is_active: bool = Field(default=True)

    # user: Optional[Users] = Relationship(back_populates="wallets")
    # currency: Optional[Currency] = Relationship(back_populates="wallets")
    
    

class Transection(SQLModel, table=True):
    id: int | None              = Field(default=None, primary_key=True)
    user_id: int                = Field(foreign_key="users.id")
    txdid: str                  = Field(index=True, unique=True)
    txddate: datetime           = Field(default=datetime.today(), nullable=True)
    txdtime: datetime           = Field(default=datetime.now(), nullable=True)
    amount: float               = Field(default_factory=0)
    txdcurrency: int            = Field(foreign_key="currency.id")
    txdfee: float               = Field(default=0.0)
    totalamount:float           = Field(default=0.0)
    txdrecever: int             = Field(foreign_key="users.id", default=None, nullable=True)
    txdmassage: str             = Field(default='message')
    txdstatus: str              = Field(default='Pending', nullable=True)
    payment_mode: str           = Field(default='None')
    txdtype: str                = Field(default='None')


    
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
    
    
    



# class TokenTable(SQLModel, table=True):
#     __tablename__ = "token"
#     # user_id = Column(Integer)
#     user_id = Column(Integer)
#     access_toke = Column(String(500), primary_key=True)
#     refresh_toke = Column(String(500),nullable=False)
    