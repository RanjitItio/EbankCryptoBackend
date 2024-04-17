from http.client import HTTPException
from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema
from sqlmodel import Session, select
from database.db import async_engine, AsyncSession
from Models.models import Users
from blacksheep import Request
from blacksheep import  json
from sqlalchemy.exc import SQLAlchemyError
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG ,SECURITIES_CODE



class UserController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/register'
    
    @classmethod
    def class_name(cls):
        return "Users Data"
    

    @get()
    async def get_user(email: str):
        with Session(async_engine) as session:
            users = []
            get_email = email
            statement = select(Users).where(Users.email == get_email)
            results = session.exec(statement)
            for op in results:
                users.append(op)

            return json({'users': users})


    @post()
    async def add_user(self, request: Request, user: UserCreateSchema):
        try:
            async with AsyncSession(async_engine, expire_on_commit=False) as session:
                existing_user_result = await session.execute(select(Users).where(Users.email == user.email))
                existing_user = existing_user_result.scalar()
                if existing_user:
                    if existing_user.email:
                        return json({'msg':f"{existing_user.email} already exists"}, 400)
                if user.password1 != user.password2:
                    return json({'msg': 'Password did not match'})
                if len(user.phoneno) < 10:
                    return json({'msg': 'Phone number must be 10 digit'})
                else:
                    user_instance = Users(first_name=user.firstname,lastname=user.lastname, email=user.email, phoneno=user.phoneno, password=user.password1 )
                    session.add(user_instance)
                    await session.commit()
                    return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)

        except SQLAlchemyError as e:
            return json({"Error": str(e)}, status=405)
    

