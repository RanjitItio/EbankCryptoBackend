from sqlmodel import SQLModel, Field, Column, String, Integer
from typing import Optional
import datetime



class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field(default='Default User First Name')
    lastname: str = Field(default='Default User Last Name')
    email: str = Field(index=True, unique=True)
    phoneno: str 
    password: str
    default_wallets: Optional[int] = None
    address1: str = Field(default='Update it later')
    address2: str = Field(default='Update it later')
    city: str = Field(default='Update it later')
    state: str = Field(default='Update it later')
    country: str = Field(default='Update it later')
    picture: str = Field(default='Update it later')
    dogecoin_address: str = Field(default='Update it later')
    bitcoin_address: str = Field(default='Update it later')
    litcoin_address: str = Field(default='Update it later')
    is_merchent: bool = Field(default=False)
    is_active: bool = Field(default=False)
    


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
    balance: float = Field(default=0.0)
    is_active: bool = Field(default=True)
    
    
    
    
class Transection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    txdid: str = Field(index=True, unique=True)
    txddate: datetime.datetime = Field(default=datetime.datetime.now())
    user_id: int = Field(foreign_key="users.id")
    txdtype: str  # deposit, withdraw, transfer
    amount: float
    txdfee: float
    totalamount:float = Field(default=0.0)
    txdcurrency: int = Field(foreign_key="currency.id")
    txdrecever: int = Field(foreign_key="users.id")
    txdmassage: str = Field(default='')
    txdstatus: bool = Field(default=False)
    
class ExternalTransection(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    txdid: str = Field(index=True, unique=True)
    txddate: datetime.datetime = Field(default=datetime.datetime.now())
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
    firstname: str = Field(default='Update it later')
    lastname: str = Field(default='Update it later')
    dateofbirth: datetime.date = Field(default=datetime.date.today())
    gander: str = Field(default='Update it later')
    marital_status: str = Field(default='Update it later')
    email : str
    phoneno : str
    address: str = Field(default='Update it later')
    landmark : str = Field(default='Update it later')
    city: str = Field(default='Update it later')
    zipcode: str = Field(default='Update it later')
    state: str = Field(default='Update it later')
    country: str = Field(default='Update it later')
    nationality: str = Field(default='Update it later')
    id_type: str = Field(default='Update it later')
    id_number: str = Field(default='Update it later')
    id_expiry_date: datetime.date = Field(default=datetime.date.today())
    uploaddocument: str = Field(default='Update it later')
   
    
    
    
    



# class TokenTable(SQLModel, table=True):
#     __tablename__ = "token"
#     # user_id = Column(Integer)
#     user_id = Column(Integer)
#     access_toke = Column(String(500), primary_key=True)
#     refresh_toke = Column(String(500),nullable=False)
    