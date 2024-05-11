from pydantic import BaseModel
import datetime
from typing import Optional



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
    currency: str
    transfer_amount: float
    recivermail:str
    note: str
    fee: float
    total_amount: float


class WithdrawlAndDeposieSchema(BaseModel):
    currency: str
    deposit_amount: float
    fee: float
    total_amount: float
    payment_mode: str
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

class ResetPasswdSchema(BaseModel):
    email: str
    
class Kycschema(BaseModel):
    user_id: int
    firstname: str 
    lastname: str 
    dateofbirth: datetime.date 
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
    id_expiry_date: datetime.date 
    uploaddocument: str 
   
class ConfirmMail(BaseModel):
       
       token: str

class RequestMoneySchemas(BaseModel):
    user_id: int
    recipient_user_id: int
    currency: int
    amount: float
    note: str


class CurrencySchemas(BaseModel):
    name: str
    symbol: str
    fee: float
    decimal_places: int


class CreateWalletSchemas(BaseModel):
    email: str
    currency: int
    balance: float

class GenerateToken(BaseModel):
    user_id: int


class UpdateCurrencySchema(BaseModel):
    name: str
    symbol: Optional[str]
    fee: Optional[str]


class UpdateKycSchema(BaseModel):
    status: str
    kyc_id: int
