from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema ,ConfirmMail
from sqlmodel import select
from Models.models import Users ,Currency ,Wallet, Kycdetails, Group, UserKeys
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from ..settings import CRYPTO_CONFIG, SECURITIES_CODE
from app.auth import (
    encrypt_password ,decrypt_password_reset_token, 
    send_welcome_email, generate_merchant_secret_key, generate_merchant_unique_public_key
    )
from decouple import config
from app.controllers.controllers import get, post
from blacksheep.server.authorization import auth
# from app.controllers.media import save_user_image




signup_mail_sent_url = config('SIGNUP_MAIL_URL')




class UserController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/register'
    
    @classmethod
    def class_name(cls):
        return "Users Data"
    
    
    @get()
    async def get_user(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    get_all_user     = await session.execute(select(Users))
                    get_all_user_obj = get_all_user.scalars().all()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)
                
                if not get_all_user_obj:
                    return json({'msg': "No user available to show"}, 404)
                
                return json({'msg': 'Data fetched successfully', 'data': get_all_user_obj})
            
        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)
    
    
    #Register New uer
    @post()
    async def create_user(self, request: Request, user: UserCreateSchema):
        try:
            async with AsyncSession(async_engine) as session:
 
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()
                except Exception as e:
                    return json({'error': f'user fetch error {str(e)}'}, 400)
                
                try:
                    existing_mobieno = await session.execute(select(Users).where(Users.phoneno == user.phoneno))
                    mobileno         = existing_mobieno.scalars().first()
                except Exception as e:
                    return json({'msg': 'Mobile no fetche error', 'error': f'{str(e)}'}, 400)
                
                try:
                    if user.is_merchent:
                        user_group     = await session.execute(select(Group).where(Group.name == 'Merchant Regular'))
                        user_group_obj = user_group.scalars().first()

                        if not user_group_obj:
                            user_group_id = 1
                        else:
                            user_group_id = user_group_obj.id
                    else:
                        user_group     = await session.execute(select(Group).where(Group.name == 'Default User'))
                        user_group_obj = user_group.scalars().first()

                        if not user_group_obj:
                            user_group_id = 1
                        else:
                            user_group_id = user_group_obj.id

                except Exception as e:
                    return json({'msg': 'Group assign error', 'error': f'{str(e)}'}, 400)


                if first_user:
                    return json({'msg': f"{first_user.email} already exists"}, 400)
                
                if mobileno:
                    return json({'msg': f"{mobileno.phoneno} number already exists"}, 400)
                
                if user.password != user.password1:
                    return json({"msg":"Password is not same Please try again"}, status=403)   
                

                try:
                    user_instance = Users(
                        first_name  = user.firstname,
                        lastname    = user.lastname,
                        email       = user.email,
                        phoneno     = user.phoneno,
                        password    = encrypt_password(user.password),
                        group       = user_group_id,
                        is_merchent = user.is_merchent,
                        # picture     = user_image_path if user_image_path else ''
                    )

                    session.add(user_instance)
                    await session.commit()
                    await session.refresh(user_instance)

                    # If user is a Merchant then assign Public and secret key
                    if user.is_merchent:
                        _secret_key = await generate_merchant_secret_key(user_instance.id)
                        public_key_ = await generate_merchant_unique_public_key()

                        merchant_secret_key = UserKeys(
                            user_id    = user_instance.id,
                            secret_key = _secret_key,
                            public_key = public_key_
                        )

                        session.add(merchant_secret_key)

                except Exception as e:
                    return json({'msg': f'user create error {str(e)}'}, 400)
            
                try:
                    initial_balance = 0.0
                    userID          = user_instance.id
                    user_first_name = user_instance.first_name
                    user_last_name  = user_instance.lastname

                    try:                
                        all_currency = await session.execute(select(Currency))
                        currency_list = all_currency.scalars().all()
                    except Exception as e:
                        return json({'error': f'Currency error {str(e)}'}, 400)

                    if currency_list:
                        for currency_obj in currency_list:
                            wallet = Wallet(
                                user_id     = userID,
                                currency    = currency_obj.name,
                                balance     = initial_balance,
                                currency_id = currency_obj.id
                            )
                            session.add(wallet)

                        await session.commit()
                        await session.refresh(wallet)
                        await session.refresh(merchant_secret_key)

                        link=f"{signup_mail_sent_url}/signin/"

                        body = f"""
                              <html>
                                <body>
                                    <b>Dear {user_first_name} {user_last_name},</b>
                                    <p>Welcome aboard! We are thrilled to have you join our community at Itio Innovex Pvt. Ltd.!</p>
                                    <p>To complete your registration and activate your account, please verify your email address by clicking the link below:</p>
                                    <a href="{link}">Verify Your Email Address</a>
                                    <p>If the button above doesn’t work, you can copy and paste the following URL into your web browser:</p>
                                    <p><a href="{link}">{link}</a></p>
                                    <p>Thank you for choosing Itio Innovex Pvt. Ltd. We look forward to providing you with the best possible experience.</p>

                                    <p><b>Best Regards,</b><br>
                                    <b>Itio Innovex Pvt. Ltd.</b></p>
                                </body>
                                </html>
                                """
                        send_welcome_email(user.email,"Welcome! Please Verify Your Email Address", body)

                        return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                
                except Exception as e:
                    return json({'msg': f'Wallet create error {str(e)}'}, 400)

                # if wall:
                #     print("done done done done done done done")

                # link=f"www.example.com/{encrypt_password_reset_token(user_instance.id)}"
                # send_password_reset_email(user.email,"confirm mail",link)
                
                # return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname} of ID {user_instance.id}'}, 201)
        
        except Exception as e:
            return json({"Error": str(e)}, 500)



class SuspendedUserCheck(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/is_suspended/'

    @classmethod
    def class_name(cls):
        return "Check Suspended user"
    
    @auth('userauth')
    @get()
    async def suspended_user_check(self, request: Request):
        """
         Check user is Suspended or not
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                try:
                    user = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj = user.scalar()
                except Exception as e:
                    return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
                
                if user_obj.is_suspended:
                    return json({'msg': 'User has been suspended'}, 401)
                
                return json({'msg': 'User is active'}, 200)
            
        except Exception as e:
            return json({'Error': str(e)}, 500)



class InactiveUserCheck(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/is_active/'

    @classmethod
    def class_name(cls):
        return "Check Inactive user"
    
    @auth('userauth')
    @get()
    async def inactive_user_check(self, request: Request):
        """
         Check user is Active or not
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                try:
                    user = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj = user.scalar()
                except Exception as e:
                    return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
                
                if not user_obj.is_active:
                    return json({'msg': 'User is not active'}, 401)
                
                return json({'msg': 'User is active'}, 200)
            
        except Exception as e:
            return json({'Error': str(e)}, 500)




#Count all avilable user From KYC
class CountAvailableUser(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/count/'

    @classmethod
    def class_name(cls):
        return "Count Users"
    
    @auth('userauth')
    @get()
    async def count_users(self, request: Request):
        """
         Check user is Active or not
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id') if user_identity else None

                # Check the user is admin or Not
        
                user_obj = await session.execute(select(Users).where(Users.id == admin_id))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            

                user_kyc_obj = await session.execute(select(Kycdetails))
                user_kyc_obj_data = user_kyc_obj.scalars().all()

                if not user_kyc_obj_data:
                    return json({'msg': 'No users Available'}, 404)
                
            
                count_users = len(user_kyc_obj_data)

            # print(count_users)

                return json({'msg': 'Success', 'total_users': count_users})
        
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
  


class ConfirmMail(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/confirm_mail'

    @classmethod
    def class_name(cls):
        return "Confirm User Email"

    @post()
    async def confirm_email(self, data: ConfirmMail, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_id = decrypt_password_reset_token(data.token)['user_id']
                user = await session.get(Users, user_id)
                if user:
                    user.is_verified = True
                    await session.commit()
                    
                    return json({'msg': 'Email confirmed successfully'}, 200)
                else:
                    return json({'msg': 'Invalid token'}, 400)
        except Exception as e:
            return json({'Error': str(e)}, 500)