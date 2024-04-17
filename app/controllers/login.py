from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema ,UserLoginSchema
from sqlmodel import Session, select
from database.db import engine
from Models.models import Users
from blacksheep import Request
from blacksheep import  json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token ,generate_refresh_token ,decode_token

import time



class UserLoginController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/login'
    
    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @post()
    async def login_user(self, user: UserLoginSchema, request: Request):
        try:
            with Session(engine) as session:
                existing_user = session.exec(select(Users).where(Users.email == user.email)).first()
                if existing_user and existing_user.password == user.password:
                    
                    return json({'user': existing_user, 'access_token': generate_access_token(existing_user.id), 'refresh_token': generate_refresh_token(existing_user.id)})
                
                else:
                    return json({'msg': 'Invalid credentials'}, 400)
        except SQLAlchemyError as e:
            return json({"Error": str(e)})



class UserRefreshController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/refreshtoken'
    
    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @post()
    async def login_user(self, user: UserLoginSchema, request: Request):
        token = request.cookies.get("refresh_token")
        payload= decode_token(token)
        if payload['exp'] < time.time():
            return json({'msg': 'Refresh token expired'}, 400)
        else:
            return json({'user': payload['user_id'], 'access_token': generate_access_token(payload['user_id']), 'refresh_token': generate_refresh_token(payload['user_id'])})

 


