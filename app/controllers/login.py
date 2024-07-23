from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema, UserLoginSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password
import time
from datetime import datetime, timedelta
from app.controllers.controllers import get, post, put, delete



# Login user
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
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)

                if first_user and check_password(user.password,first_user.password):
                    if first_user.is_active:

                        current_time = datetime.now()
                        login_count  = first_user.login_count
                       
                        if login_count == None:
                            login_count = 0
                            
                        # formattedtime = current_time.strftime("%H:%M %p")
                        # ip = request.original_client_ip

                        try:
                            first_user.lastlogin = current_time

                            if login_count == 0:
                                count = login_count + 1
                                first_user.login_count = count

                            elif login_count > 0:
                                count = login_count + 1
                                first_user.login_count = count

                            await session.commit()
                            await session.refresh(first_user)
                            
                        except Exception as e:
                            return json({'msg': 'Login time error', 'error': f'{str(e)}'}, 400)
                        
                        response = json({
                            'is_merchant': first_user.is_merchent,
                            'user_name': first_user.full_name,
                            'access_token': generate_access_token(first_user.id),
                            'refresh_token': generate_refresh_token(first_user.id)
                        },200)

                        return response
                    
                    else:
                        return json({'msg': 'Your account is not active. Please contact the administrator.'}, 403)
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except SQLAlchemyError as e:
            return json({"Error": str(e)})




