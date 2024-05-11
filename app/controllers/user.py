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
    
    @get()
    async def get_user(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    get_all_user     = await session.execute(select(Users))
                    get_all_user_obj = get_all_user.scalars().all()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)
                
                if not get_all_user_obj:
                    return json({'msg': "No user available to show"}, 404)
                
                return json({'msg': 'Data fetched successfully', 'data': get_all_user_obj})
            
        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)
    

    @post()
    async def create_user(self, request: Request, user: UserCreateSchema):
        try:
            async with AsyncSession(async_engine) as session:
                
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()
                except Exception as e:
                    return json({'error': f'user fetch error {str(e)}'})

                if first_user:
                    return json({'msg': f"{first_user.email} already exists"}, 400)
                
                if user.password != user.password1:
                    return json({"msg":"Password is not same Please try again"} ,status=403)   
                
                # # dogeaddress=Dogecoin(CRYPTO_CONFIG["dogecoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # # bitaddress=Dogecoin(CRYPTO_CONFIG["bitcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # # litaddress=Dogecoin(CRYPTO_CONFIG["litcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # dogeaddress = bitaddress = litaddress = "nahi hai"

                try:
                    user_instance = Users(
                        first_name=user.firstname,
                        lastname=user.lastname,
                        email=user.email,
                        phoneno=user.phoneno,
                        password=encrypt_password(user.password1),
                        # dogecoin_address=dogeaddress,
                        # bitcoin_address=bitaddress,
                        # litcoin_address=litaddress
                    )
                    session.add(user_instance)
                    await session.commit()
                    await session.refresh(user_instance)
                except Exception as e:
                    return json({'msg': f'user create error {str(e)}'})
            
                try:
                    initial_balance=0.0
                    userID = user_instance.id
                    user_first_name = user_instance.first_name
                    user_last_name  = user_instance.lastname

                    try:                
                        all_currency = await session.execute(select(Currency))
                        currency_list = all_currency.scalars().all()
                    except Exception as e:
                        return json({'error': f'Currency error {str(e)}'})

                    if currency_list:
                        for currency_obj in currency_list:
                            wallet = Wallet(
                                user_id = userID,
                                currency = currency_obj.name,
                                balance=initial_balance,
                                currency_id = currency_obj.id
                            )
                            session.add(wallet)

                        await session.commit()
                        await session.refresh(wallet)
                        return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                except Exception as e:
                    return json({'msg': f'Wallet create error {str(e)}'}, 400)

                # if wall:
                #     print("done done done done done done done")
                    
                # link=f"www.example.com/{encrypt_password_reset_token(user_instance.id)}"
                # send_password_reset_email(user.email,"confirm mail",link)
                
                # return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname} of ID {user_instance.id}'}, 201)
        
        except Exception as e:
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