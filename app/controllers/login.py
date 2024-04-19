from blacksheep.server.controllers import post, APIController
from Models.schemas import UserCreateSchema, UserLoginSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password
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
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Users).where(Users.email == user.email))
                first_user = existing_user.scalars().first()
                
                print(f"User {first_user.email} logged in successfully!")
                if first_user and check_password(user.password,first_user.password):
                    if first_user.is_active:
                        
                        return json({
                            'user': first_user,
                            'access_token': generate_access_token(first_user.id),
                            'refresh_token': generate_refresh_token(first_user.id)
                        })
                    else:
                        return json({'msg': 'Your account is not active. Please contact the administrator.'}, 403)
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
    async def refreshtoken(self, request: Request):
        token = request.cookies.get("refresh_token")

        if not token:
            return json({'msg': 'Refresh token not provided'}, 400)

        try:
            payload = decode_token(token)
            
            if payload['exp'] < time.time():
                return json({'msg': 'Refresh token expired'}, 400)
            else:
                return json({
                    'user': payload['user_id'],
                    'access_token': generate_access_token(payload['user_id']),
                    'refresh_token': generate_refresh_token(payload['user_id'])
                })

        except Exception as e:
            return json({'msg': 'Invalid refresh token'}, 400)
