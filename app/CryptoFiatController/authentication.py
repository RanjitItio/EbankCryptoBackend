from app.controllers.controllers import get, post
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, desc, and_
from app.auth import (
    send_welcome_email, generate_merchant_secret_key, generate_access_token,
    generate_merchant_unique_public_key, encrypt_password,check_password,
    generate_refresh_token
)
from Models.schemas import UserCreateSchema, UserLoginSchema
from Models.models import Users, Group, Wallet, Currency, UserKeys, Kycdetails
from datetime import datetime
from decouple import config


signup_mail_sent_url = config('UAT_SIGNUP_MAIL_URL')


# Register a Crypto Fiat user
class CryptoFiatUserRegisterController(APIController):
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/crypto/user/register/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Crypto Fiat User Register'
    

    @post()
    async def create_crypto_user(self, request: Request, user: UserCreateSchema):
        """
            This function creates a new user with specified details, assigns them to a 
            user group, generates keys for merchants, creates wallets for the user with initial balance, and <br/>
            sends a welcome email for account verification.<br/><br/>

            Parameters:<br/>
              - request:The `request` parameter in the `create_crypto_user` function represents the HTTP
                        request object that contains information about the incoming request such as headers, body,<br/>
                        method, URL, etc. It is used to extract data from the incoming request and interact with the
                        client making the request.<br/>
               - user(UserCreateSchema): The function takes in the user object as parameters<br/><br/>

            Returns: <br/>
                The code is returning JSON responses based on different scenarios:<br/>
                1. If the email address already exists, it returns a message stating "Email address already<br/>
                    exists" with a status code of 400.<br/>
                2. If the mobile number already exists, it returns a message stating "Mobile number already<br/>
                    exists" with a status code of 400.<br/>
                3. If the passwords do not match, it returns a message<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Check for existing mail
                existing_user_obj = await session.execute(select(Users).where(Users.email == user.email))
                existing_user     = existing_user_obj.scalars().first()
               
                existing_mobieno = await session.execute(select(Users).where(Users.phoneno == user.phoneno))
                mobileno         = existing_mobieno.scalars().first()
                
                # IF email exists
                if existing_user:
                    return json({'msg': f"Email address already exists"}, 400)
                
                # If mobile number exists
                if mobileno:
                    return json({'msg': f"Mobile number already exists"}, 400)
                
                # If password did not Match
                if user.password != user.password1:
                    return json({"msg":"Password is not same Please try again"}, status=403) 
              
                # For merchant user
                if user.is_merchent:
                    user_group     = await session.execute(select(Group).where(Group.name == 'Merchant Regular'))
                    user_group_obj = user_group.scalars().first()

                    if not user_group_obj:
                        # Create a group
                        new_group = Group(
                            name = 'Merchant Regular'
                        )

                        session.add(new_group)
                        await session.commit()
                        await session.refresh(new_group)

                        user_group_id = new_group.id
                    else:
                        user_group_id = user_group_obj.id

                # For Regular User
                else:
                    user_group     = await session.execute(select(Group).where(Group.name == 'Default User'))
                    user_group_obj = user_group.scalars().first()

                    if not user_group_obj:
                        new_group = Group(
                            name = 'Default User'
                        )

                        session.add(new_group)
                        await session.commit()
                        await session.refresh(new_group)

                        user_group_id = new_group.id
                    else:
                        user_group_id = user_group_obj.id
                
                # Create user
                try:
                    user_instance = Users(
                        first_name  = user.firstname,
                        lastname    = user.lastname,
                        email       = user.email,
                        phoneno     = user.phoneno,
                        password    = encrypt_password(user.password),
                        group       = user_group_id,
                        is_merchent = user.is_merchent,
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
               
                    all_currency = await session.execute(select(Currency))
                    currency_list = all_currency.scalars().all()
                    
                    # Assign wallet
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
                        
                        # To prevent greenlet error
                        if user.is_merchent:
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
                        
                        # Send mail
                        send_welcome_email(user.email,"Welcome! Please Verify Your Email Address", body)

                        return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                    
                except Exception as e:
                    return json({'error': 'Wallet create error', 'message': f'{str(e)}'}, 400)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


# Login a crypto user
class CryptoFiatUserLoginController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/crypto/user/login/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Crypto Fiat User Login'
    
    @post()
    async def login_crypto_user(self, user: UserLoginSchema):
        """
            This function handles the login process for crypto users. It checks the user's credentials, <br/>
            validates the KYC status, and generates access and refresh tokens for authenticated users. <br/><br/>

            Parameters:<br/>
            user (UserLoginSchema): An instance of UserLoginSchema containing the user's email and password.<br/><br/>
    
            Returns:<br/>
            JSON response with the following structure:<br/>
            - If successful login:<br/>
                {<br/>
                   &nbsp; 'is_merchant': bool,<br/>
                   &nbsp; 'user_name': str,<br/>
                   &nbsp; 'access_token': str,<br/>
                   &nbsp; 'refresh_token': str<br/>
                }<br/>
            - If any error occurs during the login process:<br/>
                {<br/>
                     &nbsp;'msg': str,<br/>
                     &nbsp;'error': str (optional)<br/>
                }
        """
        
        try:
            async with AsyncSession(async_engine) as session:

                existing_user_obj = await session.execute(select(Users).where(Users.email == user.email))
                existing_user     = existing_user_obj.scalars().first()

                # Password validation
                if existing_user and check_password(user.password,existing_user.password):

                    if existing_user.is_merchent:
                        return json({'message': 'Only crypto user allowed'}, 400)

                    # Check kyc is exist for the user
                    merchnat_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == existing_user.id
                    ))
                    merchnat_kyc_ = merchnat_kyc_obj.scalar()

                    # If kyc not submitted
                    if not existing_user.is_kyc_submitted and not existing_user.is_admin and not merchnat_kyc_:
                        return json({
                            'message': 'Kyc not submitted',  
                            'first_name':  existing_user.first_name,
                            'last_name': existing_user.lastname,
                            'contact_number': existing_user.phoneno,
                            'email': existing_user.email,
                            'user_id': existing_user.id                
                            }, 400)

                    # For active users
                    if existing_user.is_active:
                        current_time = datetime.now()
                        login_count  = existing_user.login_count
                       
                        if login_count == None:
                            login_count = 0
                            
                        try:
                            existing_user.lastlogin = current_time

                            if login_count == 0:
                                count = login_count + 1
                                existing_user.login_count = count

                            elif login_count > 0:
                                count = login_count + 1
                                existing_user.login_count = count

                            await session.commit()
                            await session.refresh(existing_user)
                            
                        except Exception as e:
                            return json({'msg': 'Login time error', 'error': f'{str(e)}'}, 400)
                        
                        response = json({
                            'is_merchant': existing_user.is_merchent,
                            'user_name': existing_user.full_name,
                            'access_token': generate_access_token(existing_user.id),
                            'refresh_token': generate_refresh_token(existing_user.id)
                        },200)

                        return response
                    
                    else:
                        return json({'msg': 'Your account is not active. Please contact the administrator'}, 400)
                    
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except Exception as e:
            return json({"Error": str(e)}, 500)
        
