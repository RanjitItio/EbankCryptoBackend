from pydantic import BaseModel
import datetime
from typing import Optional
from dataclasses import dataclass, field



@dataclass
class AllKycByAdminSchema:
    limit: Optional[int] = field(default=10)
    offset: Optional[int] = field(default=0)


@dataclass
class UserCreateSchema:
    firstname: str
    lastname: str
    phoneno: str 
    password: str
    password1: str
    email: str
    is_merchent: bool



@dataclass
class AdminUserCreateSchema:
    first_name: str
    last_name:  str
    phoneno:    str
    email:      str
    group:      str
    password:   str
    confirm_password: str
    status:     str


class AdminCreateSchema(BaseModel):
    firstname: str
    lastname: str
    email: str
    password: str
    confirm_password: str
    phone_no: str
    # is_admin:bool

 

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


# class ResetPassword(BaseModel):
#     token: str
#     new_password: str
#     confirm_password: str   

@dataclass
class TransferMoneySchema:
    send_amount: float
    fee: float
    total_amount: float
    send_currency: str
    sender_payment_mode: str
    purpose: str
    
    rec_currency: str
    rec_full_name: str
    rec_email: str
    rec_phoneno: str
    rec_add_info: str
    rec_address: str

    rec_pay_mode: str
    rec_bank_name: Optional[str]      = field(default=None)
    rec_acc_no: Optional[str]         = field(default=None)
    rec_ifsc: Optional[str]           = field(default=None)

    # sender_bank_name: Optional[str]   = field(default=None)
    # sender_acc_no: Optional[str]      = field(default=None)
    # sender_ifsc: Optional[str]        = field(default=None)

    
    # card_no: Optional[str]     = field(default=None)
    # card_cvv: Optional[str]    = field(default=None)
    # card_expiry: Optional[str] = field(default=None)

    # currency: str
    # transfer_amount: float
    # recivermail:str
    # note: str
    # fee: float
    # total_amount: float
    # payment_mode: str


class WithdrawlAndDeposieSchema(BaseModel):
    currency: str
    deposit_amount: float
    fee: float
    total_amount: float
    payment_mode: str
    note: str

class DepositMoneySchema(BaseModel):
    currency: str
    deposit_amount: float
    fee: float
    total_amount: float
    payment_mode: str
    selected_wallet: int


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
    token:     str
    password1: str
    password2: str


class ResetPasswdSMailchema(BaseModel):
    email: str
    
class Kycschema(BaseModel):
    user_id: int
    firstname: str 
    lastname: str 
    dateofbirth: datetime.date 
    gender: str
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


from dataclasses import dataclass


@dataclass
class RequestMoneySchemas:
    recipient_mail: str
    currency:       float
    amount:         float
    note:           str = 'Request Money'


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


@dataclass
class UpdateTransactionSchema:
    status: str
    transaction_id: int

@dataclass
class UserDeleteSchema:
    user_id: int


@dataclass
class AdminUpdateUserSchema:
    user_id:          int
    first_name:       str
    last_name:        str
    phoneno:          str
    email:            str
    group:            int
    status:           str

    dob:              str
    gender:           str
    state:            str
    city:             str
    landmark:         str
    address:          str

    # password: Optional[str]         = field(default='')
    # confirm_password: Optional[str] = field(default='')

