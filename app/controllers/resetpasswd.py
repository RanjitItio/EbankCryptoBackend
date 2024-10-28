from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema, ResetPasswdSMailchema ,ResetPasswdSchema
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
from blacksheep.server.authorization import auth



IS_DEVELOPMENT = config('IS_DEVELOPMENT')


if IS_DEVELOPMENT == 'True':
    mail_send_url = 'http://localhost:5173/'
else:
    mail_send_url = 'https://react-payment.oyefin.com/'


if IS_DEVELOPMENT == 'True':
    uat_mail_send_url = 'http://localhost:5173/'
else:
    uat_mail_send_url = 'https://react-uat.oyefin.com/'



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

                reseturl = f"{mail_send_url}reset/password/?token={password_reset_token}"

                body = f"""
                        <html>
                        <body>
                            <b>Dear</b>

                            <p>Click the link below to Reset your forgot password, The link will remain valid for 15 minutes.</p>
                            <a href="{reseturl}">Reset your password</a>

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



# Forgot password mail send for Fiat Crypto user
class CryptoFiatForgotPasswordMainSend(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/fiat/crypto/forgot/password/mail/'

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

                reseturl = f"{uat_mail_send_url}reset/password/?token={password_reset_token}"

                body = f"""
                        <html>
                        <body>
                            <b>Dear</b>

                            <p>Click the link below to Reset your forgot password, The link will remain valid for 15 minutes.</p>
                            <a href="{reseturl}">Reset your password</a>

                            <p>Thank you for choosing Itio Innovex Pvt. Ltd. We look forward to providing you with the best possible experience.</p>

                            <p><b>Best Regards,</b><br>
                            <b>Itio Innovex Pvt. Ltd.</b></p>
                            
                        </body>
                        </html>
                        """
                try:
                    send_password_reset_email(first_user.email, "Reset Your Password", body)
                except Exception as e:
                    pass

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
    async def reset_password(self, schema: ResetPasswdSchema, request: Request):
        """
          Reset Forgot Password
        """
        try:
            async with AsyncSession(async_engine) as session:
                token     = schema.token
                password1 = schema.password1
                password2 = schema.password2
                user_id   = verify_password_reset_token(token)

                try:
                    existing_user = await session.execute(select(Users).where(Users.id == int(user_id)))
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
                await session.refresh(first_user)

                return json({'msg': 'Password has been reset successfully'}, 200)
                
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)




        
