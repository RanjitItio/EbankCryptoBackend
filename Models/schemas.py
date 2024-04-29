from pydantic import BaseModel
import datetime



class UserCreateSchema(BaseModel):
    firstname: str
    lastname: str
    phoneno: str 
    password: str
    password1: str
    email: str
    is_merchent: bool 



class AdminCreateSchema(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str
    is_admin:bool

 

class UserLoginSchema(BaseModel):
    email: str
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class changepassword(BaseModel):
    email:str
    old_password:str
    new_password:str


class TokenCreate(BaseModel):
    user_id:str
    access_token:str
    refresh_token:str
    status:bool
    created_date:datetime.datetime


class ResetPassword(BaseModel):
    token: str
    new_password: str
    confirm_password: str   

class TransferMoneySchema(BaseModel):
    user_id :int
    currency: int
    amount: float
    txdtype: str 
    recivermail:str
    note: str

class WithdrawlAndDeposieSchema(BaseModel):
    user_id :int
    currency: int
    amount: float
    txdtype: str
    note: str


class ExternalTransectionSchema(BaseModel):
    user_id: int
    txdtype: str  # deposit, withdraw, transfer
    amount: float
    txdfee: float
    totalamount:float
    txdcurrency: int 
    recipientfullname : str 
    recipientemail: str 
    recipientmobile: str
    recipientbanktransfer: str 
    recipientbankname: str 
    recipientbankaccountno: str 
    recipientbankifsc: str
    recipientaddress: str 
    recipientcurrency: int
    
class currencyExchange(BaseModel):
    user_id: int
    from_currency: int
    to_currency: int
    amount: float
    exchange_rate: float
    total_amount: float