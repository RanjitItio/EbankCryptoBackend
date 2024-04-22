from blacksheep.server.controllers import post, APIController
from Models.schemas import UserLoginSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Admin
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token
from app.auth import check_password



class AdminLoginController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/admin/login'
    
    @classmethod
    def class_name(cls):
        return "Admin login"
    
    @post()
    async def login_user(self,user :UserLoginSchema,request: Request):
        try:
            
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Admin).where(Admin.email == user.email))
                first_user = existing_user.scalars().first()
                
                print(f"User {first_user.email} logged in successfully!")
                if first_user and check_password(user.password,first_user.password):
                    return json({
                   
                        'access_token': generate_access_token(first_user.id),
                        'refresh_token': generate_refresh_token(first_user.id)
                    })
                else:
                    return json({'msg': 'Invalid credentials'}, 400)
        
        except SQLAlchemyError as e:
            return json({"Error": str(e)})
