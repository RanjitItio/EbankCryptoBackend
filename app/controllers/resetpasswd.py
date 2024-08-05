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
    mail_send_url = 'https://react-uat.oyefin.com/'



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

                reseturl = f"{mail_send_url}reset-password/?token={password_reset_token}"

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
                token = schema.token
                password1 = schema.password1
                password2 = schema.password2
                user_id   = verify_password_reset_token(token)

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
    

    @docs(responses={
        200: 'Password Changed Successfully',
        403: 'Password did not match',
        400: 'Invalied request',
        500: 'Server Error'
    })
    @auth('userauth')
    @post()
    async def change_password(self, request: Request):
        """
          Change users password, Authenticated Route
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                request_body = await request.json()
                password1    = request_body['password1']
                password2    = request_body['password2']
                
                if password1 != password2:
                    return json({'msg': 'Password did not match'}, 403)
                
                user       = await session.execute(select(Users).where(Users.id == user_id))
                user_obj   = user.scalar()
                
                if user_obj:
                    encrypted_password = encrypt_password(password1)
                    user_obj.password  = encrypted_password

                    session.add(user_obj)
                    await session.commit()
                    await session.refresh(user_obj)

                    return json({
                        'msg': 'Password Changed Successfully'
                    }, 200)
                
                else:
                    return json({'msg': 'Invalied request'}, 400)
                
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        
