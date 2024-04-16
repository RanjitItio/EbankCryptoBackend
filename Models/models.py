from sqlmodel import SQLModel, Field, Column, String, Integer
from typing import Optional



class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field(default='Default User First Name')
    lastname: str = Field(default='Default User Last Name')
    email: str = Field(index=True, unique=True)
    phoneno: str 
    password: str
    default_wallets: Optional[int] = None
    address1: str = None
    address2: str = None
    city: str = None
    state: str = None
    country: str = None
    picture: str = None
    dogecoin_address: str = None
    bitcoin_address: str = None
    litcoin_address: str = None
    is_merchent: bool = False
    is_active: bool = False
    
class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field()
    lastname: str = Field()
    email: str = Field(index=True, unique=True)
    
    password: str
    picture: str = None
    is_admin: bool = False




# class TokenTable(SQLModel, table=True):
#     __tablename__ = "token"
#     # user_id = Column(Integer)
#     user_id = Column(Integer)
#     access_toke = Column(String(500), primary_key=True)
#     refresh_toke = Column(String(500),nullable=False)
    