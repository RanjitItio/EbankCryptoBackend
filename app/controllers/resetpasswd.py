from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema, UserLoginSchema ,ResetPassword ,ResetPasswdSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
from app.controllers.controllers import get, post, put, delete



class UserResetPasswdController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/reset_passwd'

    @classmethod
    def class_name(cls):
        return "Users reset"
    
    @post()
    async def resetpassword(self, user: ResetPasswdSchema, request: Request):
        
        try:
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Users).where(Users.email == user.email))
                first_user = existing_user.scalars().first()
                
                if first_user :
                    password_reset_token = encrypt_password_reset_token(first_user.id)
                    reseturl = f"https://example.com/user/reset-password?token={password_reset_token}"
                    send_password_reset_email(first_user.email,"reset password",reseturl)
                    return json({
                        'msg': 'Password reset instructions have been sent to your email address.'
                    }, 200)
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except SQLAlchemyError as e:
            return json({"Error": str(e)})


class UserChangePasswordController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/change_password'
    @classmethod
    def class_name(cls):
        return "Users change password"
    @post()
    async def change_password(self, data: ResetPassword, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Decode the password reset token to get the user ID
                user_id = decode_token(data.token)['user_id']
                # Find the user based on the user ID
                user = await session.execute(select(Users).where(Users.id == user_id))
                first_user = user.scalars().first()
                if first_user:
                    # Check if the password reset token is still valid
                    if data.new_password == data.confirm_password:
                        # Update the user's password
                        first_user.password = encrypt_password(data.new_password)
                        session.add(first_user)
                        await session.commit()
                        await session.refresh(first_user)
                        return json({
                            'msg': 'Password has been reset successfully.'
                        }, 200)
                    else:
                        return json({'msg': 'Passwords do not match.'}, 400)
                else:
                    return json({'msg': 'Invailed request.'}, 400)
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)