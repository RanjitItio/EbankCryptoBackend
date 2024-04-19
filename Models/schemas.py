from pydantic import BaseModel
import datetime



class UserCreateSchema(BaseModel):
    firstname: str
    lastname: str
    phoneno: str 
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



