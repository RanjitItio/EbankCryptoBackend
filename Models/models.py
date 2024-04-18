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
    address1: str = Field(default='Update it later')
    address2: str = Field(default='Update it later')
    city: str = Field(default='Update it later')
    state: str = Field(default='Update it later')
    country: str = Field(default='Update it later')
    picture: str = Field(default='Update it later')
    dogecoin_address: str = Field(default='Update it later')
    bitcoin_address: str = Field(default='Update it later')
    litcoin_address: str = Field(default='Update it later')
    is_merchent: bool = False
    # is_active: bool = False
    


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str = Field()
    lastname: str = Field()
    email: str = Field(index=True, unique=True)    
    password: str
    picture: str = Field(default='Update it later')
    is_admin: bool = False



# class TokenTable(SQLModel, table=True):
#     __tablename__ = "token"
#     # user_id = Column(Integer)
#     user_id = Column(Integer)
#     access_toke = Column(String(500), primary_key=True)
#     refresh_toke = Column(String(500),nullable=False)
    