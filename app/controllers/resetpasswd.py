from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema, ResetPasswdSMailchema ,ResetPassword ,ResetPasswdSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import encrypt_password_reset, verify_password_reset_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
from app.controllers.controllers import get, post, put, delete
from decouple import config
from app.docs import docs


mail_send_url = config('SIGNUP_MAIL_URL')


#Mail will sent to the users address to reset the password
class UserResetPasswdMailSendController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/reset_passwd/mail/'

    @classmethod
    def class_name(cls):
        return "Password Reset Mail Sent"
    
    @docs(responses={
        404: 'Requested mail ID does not exist',
        400: 'Unable to get the user',
        200: 'Password reset instructions have been sent to your email address',
        500: 'Server error',
        })
    @post()
    async def reset_password_mail(self, user: ResetPasswdSMailchema, request: Request):
        """
         Send mail while to Reset Forgot password, Mention all the API responses(error.response.data.msg)
        """
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user    = existing_user.scalars().first()

                    if not first_user:
                        return json({'msg': 'Requested mail ID does not exist'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to get the user', 'error': f'{str(e)}'}, 400)
                
                # if first_user :
                password_reset_token = encrypt_password_reset(first_user.id)

                reseturl = f"{mail_send_url}?token={password_reset_token}"

                body = f"""
                        <html>
                        <body>
                            <b>Dear</b>

                            <p>Click the link below to Reset your forgot password</p>
                            <a href="{reseturl}">Reset your password</a>

                            <p>If the button above doesn't work, you can copy and paste the following URL into your web browser:</p>
                            <p><a href="{reseturl}">{reseturl}</a></p>

                            <p>Thank you for choosing Itio Innovex Pvt. Ltd. We look forward to providing you with the best possible experience.</p>

                            <p><b>Best Regards,</b><br>
                            <b>Itio Innovex Pvt. Ltd.</b></p>
                            
                        </body>
                        </html>
                        """

                send_password_reset_email(first_user.email, "Reset Your Password", body)

                return json({
                    'msg': 'Password reset instructions have been sent to your email address.'
                }, 200)
            
        except Exception as e:
            return json({'msg': 'Server error', "error": str(e)}, 500)


   
class UserResetPasswdController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/reset_passwd/'

    @classmethod
    def class_name(cls):
        return "Password Reset"

    @docs(responses={404: 'Invalid token or user does not exist',
           400: 'User fetch error',
           400: 'Password did not match',
           200: 'Password has been reset successfully',
           500: 'Server Error',
           })
    @post()
    async def reset_password_mail(self, schema: ResetPasswdSchema, request: Request):
        
        try:
            async with AsyncSession(async_engine) as session:
                token = schema.token
                password1 = schema.password1
                password2 = schema.password2
                user_id = verify_password_reset_token(token)

                try:
                    existing_user = await session.execute(select(Users).where(Users.id == user_id))
                    first_user = existing_user.scalars().first()

                    if not first_user:
                        return json({'msg': 'Invalid token or user does not exist'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
                
                if password1 != password2:
                    return json({'msg': 'Password did not match'}, 400)
                
            
                first_user.password = encrypt_password(schema.password1)

                session.add(first_user)
                await session.commit()

                return json({'msg': 'Password has been reset successfully'}, 200)
                
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)




class UserChangePasswordController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/change_password'
    
    @classmethod
    def class_name(cls):
        return "Users change password"
    
    @post()
    async def change_password(self, data: ResetPassword, request: Request):
        """
         Reset Password get the response(error.response.data.msg)
        """
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