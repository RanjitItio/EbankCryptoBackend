from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema
from sqlmodel import Session, select
from database.db import engine
from Models.models import Users
from blacksheep import Request
from blacksheep import  json
from sqlalchemy.exc import SQLAlchemyError
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG ,SECURITIES_CODE


class UserController(APIController):

    @classmethod
    def route(cls):
        return 'api/v1/user/'
    
    @classmethod
    def class_name(cls):
        return "Users Data"
    

    @get()
    async def get_user(email: str):
        with Session(engine) as session:
            users = []
            get_email = email
            statement = select(Users).where(Users.email == get_email)
            results = session.exec(statement)
            for op in results:
                users.append(op)

            return json({'users': users})


    @post()
    async def add_user(self, user: UserCreateSchema, request: Request):
        try:
            with Session(engine) as session:
                existing_user = session.exec(select(Users).where(Users.email == user.email)).first()
                if existing_user:
                    if existing_user.email:
                        return json({'msg':f"{existing_user.email} already exists"}, 400)
                    
                else:
                    dogeaddress=Dogecoin(CRYPTO_CONFIG["dogecoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                    bitaddress=Dogecoin(CRYPTO_CONFIG["bitcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                    litaddress=Dogecoin(CRYPTO_CONFIG["litcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                    user_instance = Users(first_name=user.firstname,lastname=user.lastname, email=user.email,phoneno=user.phoneno, password=user.password ,dogecoin_address=dogeaddress,bitcoin_address=bitaddress,litcoin_address=litaddress)
                    session.add(user_instance)
                    session.commit()
                    session.refresh(user_instance)
                    return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)
        except SQLAlchemyError as e:
            return json({"Error": str(e)})
 

    @put()
    async def update_user():
        return {'msg': 'update user'}
    


    @delete()
    async def delete_user():
        return {'msg': 'Delete user'}
    
