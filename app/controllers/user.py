from http.client import HTTPException
from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema ,ConfirmMail
from sqlmodel import Session, select
from Models.models import Users ,Currency ,Wallet
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG, SECURITIES_CODE
from app.auth import encrypt_password , encrypt_password_reset_token,send_password_reset_email ,decrypt_password_reset_token
from app.module import createcurrencywallet




class UserController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/register'
    
    @classmethod
    def class_name(cls):
        return "Users Data"
    
    @post()
    async def add_user(self, request: Request, user: UserCreateSchema):
        try:
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Users).where(Users.email == user.email))
                first_user = existing_user.scalars().first()

                if first_user:
                    return json({'msg': f"{first_user.email} already exists"}, 400)
                
                if user.password != user.password1:
                    return json({"msg":"Password is not same Please try again"} ,status=403)                    
                all_currency = await session.execute(select(Currency))
                currency_list = all_currency.scalars().all()
                
                
                # dogeaddress=Dogecoin(CRYPTO_CONFIG["dogecoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # bitaddress=Dogecoin(CRYPTO_CONFIG["bitcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # litaddress=Dogecoin(CRYPTO_CONFIG["litcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                dogeaddress = bitaddress = litaddress = "nahi hai"
                
                user_instance = Users(
                    first_name=user.firstname,
                    lastname=user.lastname,
                    email=user.email,
                    phoneno=user.phoneno,
                    password=encrypt_password(user.password1),
                    dogecoin_address=dogeaddress,
                    bitcoin_address=bitaddress,
                    litcoin_address=litaddress
                )
                session.add(user_instance)
                await session.commit()
                await session.refresh(user_instance)
                wall= await createcurrencywallet(user_instance.id)
                if wall:
                    print("done done done done done done done")
                
                link=f"www.example.com/{encrypt_password_reset_token(user_instance.id)}"
                send_password_reset_email(user.email,"confirm mail",link)
                
                return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname} of ID {user_instance.id}'}, 201)
        
        except SQLAlchemyError as e:
            return json({"Error": str(e)})


class ConfirmMail(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/confirm_mail'

    @classmethod
    def class_name(cls):
        return "Confirm User Email"

    @post()
    async def confirm_email(self, data: ConfirmMail, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_id = decrypt_password_reset_token(data.token)['user_id']
                user = await session.get(Users, user_id)
                if user:
                    user.is_verified = True
                    await session.commit()
                    
                    return json({'msg': 'Email confirmed successfully'}, 200)
                else:
                    return json({'msg': 'Invalid token'}, 400)
        except Exception as e:
            return json({'Error': str(e)}, 500)