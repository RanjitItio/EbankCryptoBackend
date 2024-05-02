from http.client import HTTPException
from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema
from sqlmodel import Session, select
from Models.models import Users
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG, SECURITIES_CODE
from app.auth import encrypt_password



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
                
                return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname} of ID {user_instance.id}'}, 201)
        
        except SQLAlchemyError as e:
            return json({"Error": str(e)})
