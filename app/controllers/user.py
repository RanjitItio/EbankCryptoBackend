from http.client import HTTPException
from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import UserCreateSchema ,ConfirmMail, AdminUserCreateSchema, UserDeleteSchema, AdminUpdateUserSchema
from sqlmodel import Session, select
from Models.models import Users ,Currency ,Wallet, Transection, Kycdetails
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from Models.cryptoapi import Dogecoin
from ..settings import CRYPTO_CONFIG, SECURITIES_CODE
from app.auth import encrypt_password , encrypt_password_reset_token,send_password_reset_email ,decrypt_password_reset_token, decode_token, send_welcome_email
from app.module import createcurrencywallet
from blacksheep import FromJSON, FromQuery
from typing import List
from app.docs import docs
from decouple import config


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
    

    @post()
    async def create_user(self, request: Request, user: UserCreateSchema):
        try:
            async with AsyncSession(async_engine) as session:
                
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()
                except Exception as e:
                    return json({'error': f'user fetch error {str(e)}'})
                
                try:
                    existing_mobieno = await session.execute(select(Users).where(Users.phoneno == user.phoneno))
                    mobileno = existing_mobieno.scalars().first()
                except Exception as e:
                    return json({'msg': 'Mobile no fetche error', 'error': f'{str(e)}'}, 400)

                if first_user:
                    return json({'msg': f"{first_user.email} already exists"}, 400)
                
                if mobileno:
                    return json({'msg': f"{mobileno.phoneno} number already exists"}, 400)
                
                if user.password != user.password1:
                    return json({"msg":"Password is not same Please try again"} ,status=403)   
                
                # # dogeaddress=Dogecoin(CRYPTO_CONFIG["dogecoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # # bitaddress=Dogecoin(CRYPTO_CONFIG["bitcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # # litaddress=Dogecoin(CRYPTO_CONFIG["litcoin_api_key"],SECURITIES_CODE).create_new_address(user.email)
                # dogeaddress = bitaddress = litaddress = "nahi hai"

                try:
                    user_instance = Users(
                        first_name=user.firstname,
                        lastname=user.lastname,
                        email=user.email,
                        phoneno=user.phoneno,
                        password=encrypt_password(user.password1),
                        # dogecoin_address=dogeaddress,
                        # bitcoin_address=bitaddress,
                        # litcoin_address=litaddress
                    )
                    session.add(user_instance)
                    await session.commit()
                    await session.refresh(user_instance)
                except Exception as e:
                    return json({'msg': f'user create error {str(e)}'})
            
                try:
                    initial_balance=0.0
                    userID = user_instance.id
                    user_first_name = user_instance.first_name
                    user_last_name  = user_instance.lastname

                    try:                
                        all_currency = await session.execute(select(Currency))
                        currency_list = all_currency.scalars().all()
                    except Exception as e:
                        return json({'error': f'Currency error {str(e)}'})

                    if currency_list:
                        for currency_obj in currency_list:
                            wallet = Wallet(
                                user_id = userID,
                                currency = currency_obj.name,
                                balance=initial_balance,
                                currency_id = currency_obj.id
                            )
                            session.add(wallet)

                        await session.commit()
                        await session.refresh(wallet)
                        
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
            return json({"Error": str(e)})




#Add new user by Admin
class AdminUserCreateController(APIController):

    @classmethod
    def route(cls):
        return 'api/v1/admin/add/user/'
    

    @classmethod
    def class_name(cls) -> str:
        return 'Create new user by Admin'
    
    @post()
    async def create_newuser(self, request: Request, user_create_schema: FromJSON[AdminUserCreateSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                data = user_create_schema.value

                #Authenticate the user
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                        
                    header_value_str = header_value.decode("utf-8")
                    parts = header_value_str.split()

                    #Decode the token
                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]
        
                except Exception as e:
                    return json({'msg': 'Authentication Failed'}, 400)
            
                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can create users'}, 400)

                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)


                #Check the user is Default user or merchant
                if data.group == 'Default User':
                    try:
                        existing_user = await session.execute(select(Users).where(Users.email == data.email))
                        first_user    = existing_user.scalars().first()
                    except Exception as e:
                        return json({'error': f'user fetch error {str(e)}'})
                    
                    try:
                        existing_mobieno = await session.execute(select(Users).where(Users.phoneno == data.phoneno))
                        mobileno = existing_mobieno.scalars().first()
                    except Exception as e:
                        return json({'msg': 'Mobile no fetche error', 'error': f'{str(e)}'}, 400)
                    
                    if first_user:
                        return json({'msg': f"{first_user.email} already exists"}, 400)
                    
                    if mobileno:
                        return json({'msg': f"This {mobileno.phoneno} number already exists"}, 400)
                
                    if data.password != data.confirm_password:
                        return json({"msg":"Password did not match"} ,status=403) 
                    
                    #Create the user if the status is active
                    if data.status == 'Active':
                        try:
                            user_instance = Users(
                                first_name   = data.first_name,
                                lastname     = data.last_name,
                                email        = data.email,
                                phoneno      = data.phoneno,
                                password     = encrypt_password(data.password),
                                is_verified  = True,
                                is_active    = True
                                )
                            
                            session.add(user_instance)
                            await session.commit()
                            await session.refresh(user_instance)

                        except Exception as e:
                            return json({'msg': f'user create error {str(e)}'})
                        
                        #Create wallets for the user
                        try:
                            initial_balance = 0.0
                            userID          = user_instance.id
                            user_first_name = user_instance.first_name
                            user_last_name  = user_instance.lastname

                            try:                
                                all_currency = await session.execute(select(Currency))
                                currency_list = all_currency.scalars().all()
                            except Exception as e:
                                return json({'error': f'Currency error {str(e)}'})

                            if currency_list:
                                for currency_obj in currency_list:
                                    wallet = Wallet(
                                        user_id = userID,
                                        currency = currency_obj.name,
                                        balance=initial_balance,
                                        currency_id = currency_obj.id
                                    )
                                    session.add(wallet)

                                await session.commit()
                                await session.refresh(wallet)

                                return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                            
                        except Exception as e:
                            return json({'msg': f'Wallet create error {str(e)}'}, 400)
                        
                    
                    elif data.status == 'Inactive':

                        #Create Inactive user
                        try:
                            user_instance = Users(
                                first_name   = data.first_name,
                                lastname     = data.last_name,
                                email        = data.email,
                                phoneno      = data.phoneno,
                                password     = encrypt_password(data.password),
                                is_verified  = False,
                                is_active    = False
                                )
                            
                            session.add(user_instance)
                            await session.commit()
                            await session.refresh(user_instance)

                        except Exception as e:
                            return json({'msg': f'user create error {str(e)}'})
                        
                        #Create wallets for the user
                        try:
                            initial_balance = 0.0
                            userID          = user_instance.id
                            user_first_name = user_instance.first_name
                            user_last_name  = user_instance.lastname

                            try:                
                                all_currency = await session.execute(select(Currency))
                                currency_list = all_currency.scalars().all()
                            except Exception as e:
                                return json({'error': f'Currency error {str(e)}'})

                            if currency_list:
                                for currency_obj in currency_list:
                                    wallet = Wallet(
                                        user_id = userID,
                                        currency = currency_obj.name,
                                        balance=initial_balance,
                                        currency_id = currency_obj.id
                                    )
                                    session.add(wallet)

                                await session.commit()
                                await session.refresh(wallet)

                                return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                            
                        except Exception as e:
                            return json({'msg': f'Wallet create error {str(e)}'}, 400)
                        
                    else: 
                        return json({'msg': 'User did not get created'}, 200)
                

                #Create Merchant according to the status
                elif data.group == 'Merchant':
                    return json({'msg': 'In progress'}, 200)
                
                else:
                    return json({'msg': 'Please provide a valid user type Merchant or Default user'}, 404)

                return json({'msg': data})
            
        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



class UserSearchController(APIController):

    @classmethod
    def route(cls):
        return 'api/v1/user/search/{search_query}/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Search users'
    
    @get()
    async def get_searchedeusers(self, request: Request, search_query):
        try:
            async with AsyncSession(async_engine) as session:
                data = search_query

                #Authenticate the user
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                        
                    header_value_str = header_value.decode("utf-8")
                    parts = header_value_str.split()

                    #Decode the token
                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]
        
                except Exception as e:
                    return json({'msg': 'Authentication Failed'}, 400)
            
                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can create users'}, 400)

                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                
                #Authentication Ends here



                if data == 'active' or data == 'Active':

                    try:
                        searched_user_obj = await session.execute(select(Users).where(
                            (Users.is_active   == True) | 
                            (Users.is_verified == True) 
                        ))
                    except Exception as e:
                        return json({'msg': 'Active users search error', 'error': f'{str(e)}'}, 400)
                
                elif data == 'inactive' or data == 'Inactive':

                    try:
                        searched_user_obj = await session.execute(select(Users).where(
                                        (Users.is_active   == False) | 
                                        (Users.is_verified == False) 
                                    ))
                    except Exception as e:
                        return json({'msg': 'Inactive user search error', 'error': f'{str(e)}'}, 400)
                    
                else:
                    try:
                        searched_user_obj = await session.execute(select(Users).where(
                            (Users.first_name.ilike(data)) |
                            (Users.lastname.ilike(data))   |
                            (Users.email.ilike(data))      |
                            (Users.phoneno.ilike(data))    |
                            (Users.city.ilike(data))       |
                            (Users.state.ilike(data))      |
                            (Users.country.ilike(data)) 
                        ))

                    except Exception as e:
                        return json({'msg': 'Search error', 'error': f'{str(e)}'}, 400)

                users: List[Users] = searched_user_obj.scalars().all()

                users_data = [
                    {
                        "id": user.id,
                        "first_name": user.first_name,
                        "lastname": user.lastname,
                        "email": user.email,
                        "phoneno": user.phoneno,
                        "address1": user.address1,
                        "address2": user.address2,
                        "city": user.city,
                        "state": user.state,
                        "country": user.country
                    }
                    for user in users
                ]

                return json({'user_data': users_data}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



# Delete users by Admin
class AdminUserDeleteController(APIController):

    @classmethod
    def route(cls):
        return 'api/v1/admin/del/user/'
    
    @classmethod
    def class_name(cls):
        return 'Delete User by Admin'
    
    @classmethod
    def version(cls) -> str | None:
        return 'v1'
    
    @docs(responses={200: 'All the data related to user (Transactions, Wallet, Kyc) will be deleted'})
    @delete()
    async def delete_user(self, request: Request, delete_user: FromJSON[UserDeleteSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                # request_body = await request.json()
                user      = delete_user.value
                user_id   = user.user_id

                #Authenticate the user
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                        
                    header_value_str = header_value.decode("utf-8")
                    parts = header_value_str.split()

                    #Decode the token
                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]
        
                except Exception as e:
                    return json({'msg': 'Authentication Failed'}, 400)
            
                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can create users'}, 400)

                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                #Autnentication ends here



                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_data = user_obj.scalar()
                    
                except Exception as e:
                    return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
                
                if not user_data:
                    return json({'msg': 'Requested user not found'}, 404)
                
                #Get the kyc related to the user
                try:
                    user_kyc = await session.execute(select(Kycdetails).where(Kycdetails.user_id == user_id))
                    user_kyc_obj = user_kyc.scalar()
                except Exception as e:
                    return json({'msg': 'Kyc fetch error', 'error': f'{str(e)}'}, 400)
            
                #Get all the transaction related to that user
                try:
                    sender_transactions     = await session.execute(select(Transection).where(Transection.user_id == user_id))
                    sender_transactions_obj = sender_transactions.scalars().all()
                except Exception as e:
                    return json({'msg': 'User transaction fetch error', 'error': f'{str(e)}'}, 400)

                #Get the users available Receiver transaction details
                try:
                    receiver_transaction     = await session.execute(select(Transection).where(Transection.txdrecever == user_id))
                    receiver_transaction_obj = receiver_transaction.scalars().all()
                except Exception as e:
                    return json({'msg': 'Receiver user fetch error', 'error': f'{str(e)}'}, 400)
                
                #Get the wallets related to the user
                try:
                    user_wallets = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
                    user_wallets_obj = user_wallets.scalars().all()
                except Exception as e:
                    return json({'msg': 'Wallet fetch error', 'error': f'{str(e)}'}, 400)
                

                if user_kyc_obj:
                    try:
                        await session.delete(user_kyc_obj)
                        await session.commit()
                    except Exception as e:
                        return json({'msg': 'Error while deleting the user kyc', 'error': f'{str(e)}'}, 400)
            
                if receiver_transaction_obj:
                    #Set the receiver field to None of Transactions
                    try:
                        for receivers in receiver_transaction_obj:
                            receivers.txdrecever = None

                            session.add(receivers)
                        await session.commit()
                    except Exception as e:
                        return json({'msg': 'Receiver user error', 'error': f'{str(e)}'}, 404)
                
                if user_wallets_obj:
                    # Delete the Wallets
                    try:
                        for wallet in user_wallets_obj:
                            await session.delete(wallet)

                        await session.commit()

                    except Exception as e:
                        return json({'msg': 'wallet delete error', 'error': f'{str(e)}'}, 400)
                
                if sender_transactions_obj:
                    # Delete the Transactions
                    try:
                        for transaction in sender_transactions_obj:
                            await session.delete(transaction)

                        await session.commit()
                    except Exception as e:
                        return json({'msg': 'Transaction delete error', 'error': f'{str(e)}'}, 400)
                
                #Delete the user
                try:
                    await session.delete(user_data)
                    await session.commit()
                except Exception as e:
                    return json({'msg': 'Error while deleting the user', 'error': f'{str(e)}'}, 400)
                
                # await session.commit()
                # await session.refresh(user_data)

                return json({'msg': 'Deleted successfully'}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



#Update user by Admin
class AdminUpdateUserController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return 'api/v1/admin/update/user/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Update user by Admin'
    
    @put()
    async def update_user(self, request: Request, user_update_schema: FromJSON[AdminUpdateUserSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                value = user_update_schema.value

                #Authenticate the user
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                        
                    header_value_str = header_value.decode("utf-8")
                    parts = header_value_str.split()

                    #Decode the token
                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]
        
                except Exception as e:
                    return json({'msg': 'Authentication Failed'}, 400)
            
                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can create users'}, 400)

                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                #Autnentication ends here
                

                #Get the user by user ID
                try:
                    user_data = await session.execute(select(Users).where(Users.id == value.user_id))
                    user_data_obj = user_data.scalar()
                except Exception as e:
                    return json({'msg': 'User data fetch error', 'error': f'{str(e)}'}, 400)
                

                #chek the provided mail ID exists or not
                try:
                    existing_mail = await session.execute(select(Users).where(Users.email == value.email))
                    existing_mail_obj = existing_mail.scalar()
                except Exception as e:
                    return json({'msg': 'Mail fetch error', 'error': f'{str(e)}'}, 400)
                

                #Chek the provided Mobile number exists or not
                try:
                    existing_mobile_number     = await session.execute(select(Users).where(Users.phoneno == value.phoneno))
                    existing_mobile_number_obj = existing_mobile_number.scalar()

                except Exception as e:
                    return json({'msg': 'Mail fetch error', 'error': f'{str(e)}'}, 400)


                if existing_mail_obj.email != user_data_obj.email:
                    return json({'msg': 'Provided mail ID already exists'}, 200)
                
                if existing_mobile_number_obj.phoneno != user_data_obj.phoneno:
                    return json({'msg': 'Provided Mobile No already exists'}, 200)
                

                #Check the given password matching or not
                if value.password != value.confirm_password:
                    return json({'msg': 'Password did not match'}, 400)

                
                try:
                    stmt       = select(Kycdetails).where(Kycdetails.user_id == value.user_id)
                    result     = await session.execute(stmt)
                    kyc_detail = result.scalar()
                except Exception as e:
                    return json({'msg': 'Unable to locate kyc', 'error': f'{str(e)}'}, 400)
                

                #Update the user data
                try:
                    if value.group == 'Default User':
                        if value.status == 'Active':
                            #Update user
                            try:
                                user_data_obj.first_name   = value.first_name
                                user_data_obj.lastname     = value.last_name
                                user_data_obj.phoneno      = value.phoneno
                                user_data_obj.email        = value.email
                                user_data_obj.password     = encrypt_password(value.password)
                                user_data_obj.is_active    = True
                                user_data_obj.is_verified  = True
                                user_data_obj.is_suspended = False

                                session.add(user_data_obj)
                                await session.commit()

                            except Exception as e:
                                return json({'msg': 'Error while updating user data', 'error': f'{str(e)}'}, 400)
                            
                            #Update Kyc status
                            if kyc_detail:
                                try:
                                    kyc_detail.status = 'Approved'
                                    
                                    session.add(kyc_detail)
                                    await session.commit()
                                    await session.refresh(kyc_detail)
                                except Exception:
                                    return json({'msg': 'Error while updating KYC details', 'error': f'{str(e)}'}, 400)
            
                        #If the status is inactive
                        elif value.status == 'Inactive':
                            #Update user data according to Inactive status
                            try:
                                user_data_obj.first_name = value.first_name
                                user_data_obj.lastname   = value.last_name
                                user_data_obj.phoneno    = value.phoneno
                                user_data_obj.email      = value.email
                                user_data_obj.password    = encrypt_password(value.password)

                                session.add(user_data_obj)
                                await session.commit()

                            except Exception as e:
                                return json({'msg': 'Error while updating inactive user data', 'error': f'{str(e)}'}, 400)

                        elif value.status == 'Suspended':
                            try:
                                user_data_obj.first_name   = value.first_name
                                user_data_obj.lastname     = value.last_name
                                user_data_obj.phoneno      = value.phoneno
                                user_data_obj.email        = value.email
                                user_data_obj.password     = encrypt_password(value.password)
                                user_data_obj.is_active    = True
                                user_data_obj.is_verified  = True
                                user_data_obj.is_suspended = True

                                session.add(user_data_obj)
                                await session.commit()

                            except Exception as e:
                                return json({'msg': 'Error while updating user data', 'error': f'{str(e)}'}, 400)
                            
                            #Update Kyc status
                            if kyc_detail:
                                try:
                                    kyc_detail.status = 'Approved'
                                    
                                    session.add(kyc_detail)
                                    await session.commit()
                                    await session.refresh(kyc_detail)
                                except Exception:
                                    return json({'msg': 'Error while updating KYC details', 'error': f'{str(e)}'}, 400)
                                
                        else:
                            return json({'msg': 'Please provide valid user status'}, 400)
                    
                    #If the user group is Merchant
                    elif value.group == 'Merchant Regular':
                        return json({'msg': 'Work in progress'}, 200)

                except Exception as e:
                    return json({'msg': 'User update error', 'error': f'{str(e)}'}, 400)


                return json({'msg': 'User data updated successfully'}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)



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