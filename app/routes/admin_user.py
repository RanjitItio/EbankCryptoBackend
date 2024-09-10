from blacksheep.server.controllers import APIController
from Models.schemas import UserDeleteSchema, AdminUpdateUserSchema, AdminUserCreateSchema
from blacksheep import FromJSON, Request, json, delete, put, get, post
from database.db import AsyncSession, async_engine
from app.auth import encrypt_password, send_email
from Models.models import Users, Kycdetails, Transection, Wallet, Currency, TestModel, Group
from blacksheep.server.authorization import auth
from sqlmodel import select, and_
from datetime import datetime
from app.docs import docs
from typing import List
from decouple import config



SERVER_MODE = config('IS_DEVELOPMENT')
DEVELOPMENT_URL = config('DEVELOPMENT_URL_MEDIA')
PRODUCTION_URL  = config('PRODUCTION_URL_MEDIA')


if SERVER_MODE == 'True':
    media_url = DEVELOPMENT_URL
else:
    media_url = PRODUCTION_URL


if SERVER_MODE == 'True':
    url = 'http://localhost:5173'
else:
    url = 'https://react-payment.oyefin.com'



#Delete User by Admin
@docs(responses={200: 'All the data related to user (Transactions, Wallet, Kyc) will be deleted'})
@auth('userauth')
@post('/api/v1/admin/del/user/')
async def delete_user(self, request: Request, delete_user: FromJSON[UserDeleteSchema]):
    """
     Delete the user and its related Data, Only admin can access the path, Provide user_id which is to be deleted
    """

    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            user      = delete_user.value
            user_id   = user.user_id
        
            #Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == adminID))
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
                user_kyc     = await session.execute(select(Kycdetails).where(Kycdetails.user_id == user_id))
                user_kyc_obj = user_kyc.scalars()

                if not user_kyc_obj:
                    return json({'msg': 'Kyc of user not available'}, 404)
                
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
                user_wallets     = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
                user_wallets_obj = user_wallets.scalars().all()
            except Exception as e:
                return json({'msg': 'Wallet fetch error', 'error': f'{str(e)}'}, 400)
            
            #Delete the Transaction related to the Selected wallet
            try:
                for wallet in user_wallets_obj:
                    user_selected_wallet     = await session.execute(select(Transection).where(Transection.wallet_id == wallet.id))
                    user_selected_wallet_obj = user_selected_wallet.scalar_one_or_none()

                    if user_selected_wallet_obj:
                        await session.delete(user_selected_wallet_obj)
                        await session.commit()

            except Exception as e:
                return json({'msg': 'Selected wallet Transaction error', 'error': f'{str(e)}'}, 500)
            

            if user_kyc_obj:
                try:
                    for kyc in user_kyc_obj:
                        await session.delete(kyc)
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


            return json({'msg': 'User Deleted successfully'}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Update user kyc by Admin
@docs(responses={200: 'Update user profile and kyc status'})
@auth('userauth')
@put('/api/v1/admin/update/user/')
async def update_user(self, request: Request, user_update_schema: FromJSON[AdminUpdateUserSchema]):
    """
     Update the merchant user profile and kyc, Only admin can access the url
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as Admin
            user_identity    = request.identity  
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            # Admin authentication
            try:
                user_obj      = await session.execute(select(Users).where(Users.id == adminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can create users'}, 400)

            except Exception as e:
                return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            #Autnentication ends here

            # Get the payload values
            value = user_update_schema.value

            # Get the datetime value and convert into datetime format
            dob_str  = value.dob
            dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()

            # Get the group
            group_obj = await session.execute(select(Group).where(
                Group.id == value.group
            ))
            user_group = group_obj.scalar()

            # Assign user is merchant or not according to the group
            if user_group:
                if user_group.name == 'Default User':
                    merchant = False
                elif user_group.name == 'Merchant Regular':
                    merchant = True
                else:
                    merchant = False
            else:
                merchant = False


            #Get the user by user ID
            try:
                user_data     = await session.execute(select(Users).where(Users.id == value.user_id))
                user_data_obj = user_data.scalar()
            except Exception as e:
                return json({'msg': 'User data fetch error', 'error': f'{str(e)}'}, 400)
            
        
            #chek the provided mail ID exists or not
            try:
                existing_mail     = await session.execute(select(Users).where(Users.email == value.email))
                existing_mail_obj = existing_mail.scalar()
            except Exception as e:
                return json({'msg': 'Mail fetch error', 'error': f'{str(e)}'}, 400)
            

            #Chek the provided Mobile number exists or not
            try:
                existing_mobile_number     = await session.execute(select(Users).where(Users.phoneno == value.phoneno))
                existing_mobile_number_obj = existing_mobile_number.scalar()

            except Exception as e:
                return json({'msg': 'Mail fetch error', 'error': f'{str(e)}'}, 400)
            
            # If the same mobile number exists for another user
            if existing_mail_obj:
                if existing_mail_obj.email != user_data_obj.email:
                    return json({'msg': 'Provided mail ID already exists'}, 200)
            
            # If the same Email ID exists for another user
            if existing_mobile_number_obj:
                if existing_mobile_number_obj.phoneno != user_data_obj.phoneno:
                    return json({'msg': 'Provided Mobile No already exists'}, 200)
            

            #Get the Kyc details of the user
            try:
                stmt       = select(Kycdetails).where(Kycdetails.user_id == value.user_id)
                result     = await session.execute(stmt)
                kyc_detail = result.scalar()
            except Exception as e:
                return json({'msg': 'Unable to locate kyc', 'error': f'{str(e)}'}, 400)
            
            #Update the user data
            try:
                # if value.group == 'Default User':
                if value.status == 'Active':
                    #Update user data
                    user_data_obj.first_name   = value.first_name
                    user_data_obj.lastname     = value.last_name
                    user_data_obj.phoneno      = value.phoneno
                    user_data_obj.email        = value.email
                    user_data_obj.full_name    = value.first_name + ' ' + value.last_name
                    user_data_obj.is_active    = True
                    user_data_obj.is_verified  = True
                    user_data_obj.is_suspended = False
                    user_data_obj.group        = value.group
                    user_data_obj.is_merchent  = merchant

                    session.add(user_data_obj)
                    
                    #Update Kyc status
                    if kyc_detail:
                        date_format = "%Y-%m-%d"
                        date_of_birth = datetime.strptime(value.dob, date_format).date()

                        try:
                            kyc_detail.status      = 'Approved'
                            kyc_detail.dateofbirth = dob_date
                            kyc_detail.gander      = value.gender
                            kyc_detail.state       = value.state
                            kyc_detail.city        = value.city
                            kyc_detail.landmark    = value.landmark
                            kyc_detail.address     = value.address
                            kyc_detail.firstname   = value.first_name
                            kyc_detail.lastname    = value.last_name
                            kyc_detail.email       = value.email
                            kyc_detail.phoneno     = value.phoneno
                            kyc_detail.dateofbirth = date_of_birth

                            session.add(kyc_detail)
                            await session.commit()
                            await session.refresh(kyc_detail)
                            await session.refresh(user_data_obj)

                        except Exception as e:
                            return json({'msg': 'Error while updating KYC details', 'error': f'{str(e)}'}, 400)
                        
                        # Send mail to merchant

                        link = f'{url}/signin/'

                        body = f"""
                              <html>
                                <body>
                                    <b>Dear {user_data_obj.first_name} {user_data_obj.lastname},</b>

                                    <p>We are pleased to inform you that your KYC verification has been successfully completed. 
                                    Your details have been authenticated, and your account is now active</p>
                                    <p>You can now <a href="{link}">Login</a> to our system using your credentials. 
                                    Please note that your login details are confidential, and we advise you to keep them secure.</p>

                                    <p>If you have any questions or need assistance, feel free to reach out to us.</p>
                                    <p>Thank you for choosing Itio Innovex Pvt. Ltd. We look forward to providing you with the best possible experience.</p>

                                    <p><b>Best Regards,</b><br>
                                    <b>Itio Innovex Pvt. Ltd.</b></p>
                                </body>
                                </html>
                                """
                        await send_email(user_data_obj.email, "KYC Verification Successful - Login Credentials Activated", body)
    
                #If the status is inactive
                elif value.status == 'Inactive':

                    #Update user data according to Inactive status
                    try:
                        user_data_obj.first_name  = value.first_name
                        user_data_obj.lastname    = value.last_name
                        user_data_obj.phoneno     = value.phoneno
                        user_data_obj.email       = value.email
                        user_data_obj.full_name    = value.first_name + ' ' + value.last_name
                        user_data_obj.is_active   = False
                        user_data_obj.is_verified = False
                        user_data_obj.group       = value.group
                        user_data_obj.is_merchent  = merchant

                        session.add(user_data_obj)
                        await session.commit()

                    except Exception as e:
                        return json({'msg': 'Error while updating inactive user data', 'error': f'{str(e)}'}, 400)
                    
                    #Update Kyc status
                    if kyc_detail:
                        date_format = "%Y-%m-%d"
                        date_of_birth = datetime.strptime(value.dob, date_format).date()

                        try:
                            kyc_detail.dateofbirth = dob_date
                            kyc_detail.gander      = value.gender
                            kyc_detail.state       = value.state
                            kyc_detail.city        = value.city
                            kyc_detail.landmark    = value.landmark
                            kyc_detail.address     = value.address
                            kyc_detail.firstname   = value.first_name
                            kyc_detail.lastname    = value.last_name
                            kyc_detail.email       = value.email
                            kyc_detail.phoneno     = value.phoneno
                            kyc_detail.dateofbirth = date_of_birth

                            session.add(kyc_detail)
                            await session.commit()
                            await session.refresh(kyc_detail)
                        except Exception as e:
                            return json({'msg': 'Error while updating KYC details', 'error': f'{str(e)}'}, 400)

                elif value.status == 'Suspended':
                    try:
                        user_data_obj.first_name   = value.first_name
                        user_data_obj.lastname     = value.last_name
                        user_data_obj.phoneno      = value.phoneno
                        user_data_obj.email        = value.email
                        user_data_obj.full_name    = value.first_name + ' ' + value.last_name
                        user_data_obj.is_active    = True
                        user_data_obj.is_verified  = True
                        user_data_obj.is_suspended = True
                        user_data_obj.group        = value.group
                        user_data_obj.is_merchent  = merchant

                        session.add(user_data_obj)
                        await session.commit()

                    except Exception as e:
                        return json({'msg': 'Error while updating user data', 'error': f'{str(e)}'}, 400)
                    
                    #Update Kyc status
                    if kyc_detail:
                        date_format = "%Y-%m-%d"
                        date_of_birth = datetime.strptime(value.dob, date_format).date()

                        try:
                            kyc_detail.status      = 'Approved'
                            kyc_detail.dateofbirth = dob_date
                            kyc_detail.gander      = value.gender
                            kyc_detail.state       = value.state
                            kyc_detail.city        = value.city
                            kyc_detail.landmark    = value.landmark
                            kyc_detail.address     = value.address
                            kyc_detail.firstname   = value.first_name
                            kyc_detail.lastname    = value.last_name
                            kyc_detail.email       = value.email
                            kyc_detail.phoneno     = value.phoneno
                            kyc_detail.dateofbirth = date_of_birth

                            session.add(kyc_detail)
                            await session.commit()
                            await session.refresh(kyc_detail)
                        except Exception as e:
                            return json({'msg': 'Error while updating KYC details', 'error': f'{str(e)}'}, 400)
                        
                else:
                    # In any condition if No status or any Invalid status provided in payload
                    return json({'msg': 'Please provide valid user status'}, 400)

            except Exception as e:
                return json({'msg': 'User update error', 'error': f'{str(e)}'}, 400)

            # SUccess Response
            return json({'msg': 'User data updated successfully'}, 200)
        
    # For any internal error response
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Search users
@docs(responses={200: 'Search Merchantss'})
@auth('userauth')
@get('/api/v1/admin/user/search/')
async def get_searchedeusers(request: Request, query: str = ''):
    """
     Search merchant users
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity    = request.identity
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            # Admin authentication
            user_obj = await session.execute(select(Users).where(Users.id == adminID))
            user_obj_data = user_obj.scalar()

            if not user_obj_data.is_admin:
                return json({'msg': 'Admin authorization failed'}, 400)
            # Authentication Ends here

            data = query

            # # If search contain group data
            group_query = None
            if query.lower ==  'merchant regular':
                group_query_obj = await session.execute(select(Group).where(Group.name == query))
                group_query = group_query_obj.scalar()


            if data.lower() == 'active':
                searched_user_obj = await session.execute(select(Users).where(
                    and_(Users.is_active == True,
                     Users.is_merchent == True)
                ))
            
            elif data.lower() == 'inactive':
                searched_user_obj = await session.execute(select(Users).where(
                                and_(Users.is_active == False, 
                                Users.is_verified    == False,
                                Users.is_merchent    == True
                                )))
            
            elif group_query:
                searched_user_obj = await session.execute(select(Users).where(
                    and_(Users.group == group_query.id,
                         Users.is_merchent    == True
                         )))
                
            else:
                try:
                    searched_user_obj = await session.execute(select(Users).where(
                        and_((Users.first_name.ilike(data)) |
                        (Users.lastname.ilike(data))   |
                        (Users.full_name.ilike(data))  |
                        (Users.email.ilike(data))      |
                        (Users.phoneno.ilike(data)),
                        Users.is_merchent == True
                        )
                    ))

                except Exception as e:
                    return json({'msg': 'Search error', 'error': f'{str(e)}'}, 400)

            all_users: List[Users] = searched_user_obj.scalars().all()

            user_data = []
            kyc_data  = []

            for user in all_users:
                group_query = select(Group).where(Group.id == user.group)
                group_result = await session.execute(group_query)
                group_data = group_result.scalar()

                group_name = group_data.name if group_data else None

                user_data.append({
                    "user_id": user.id,
                    "firstname": user.first_name,
                    "lastname": user.lastname,
                    "email": user.email,
                    "phoneno": user.phoneno,
                    'ip_address': user.ipaddress, 
                    'lastlogin': user.lastlogin, 
                    'merchant': user.is_merchent, 
                    'admin': user.is_admin,
                    'active': user.is_active,
                    'verified': user.is_verified,
                    'group': user.group,
                    'group_name': group_name,
                    'status': 'Active' if user.is_active else 'Inactive',
                    'document': f'{media_url}/{user.picture}'
                })

                merchant_kyc_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == user.id
                ))
                merchant_kyc_ = merchant_kyc_obj.scalars().all()

                if merchant_kyc_:
                    for kyc in merchant_kyc_:
                        
                        kyc_data.append({
                            "gander": kyc.gander,
                            "state":  kyc.state,
                            "status": kyc.status,
                            "marital_status": kyc.marital_status,
                            "country": kyc.country,
                            "email": kyc.email,
                            "nationality": kyc.nationality,
                            "user_id": kyc.user_id,
                            "firstname": kyc.firstname,
                            "phoneno": kyc.phoneno,
                            "id_type": kyc.id_type,
                            "address": kyc.address,
                            "id_number": kyc.id_number,
                            "id_expiry_date": kyc.id_expiry_date,
                            "id": kyc.id,
                            "landmark": kyc.landmark,
                            "lastname": kyc.lastname,
                            "city": kyc.city,
                            "uploaddocument": f'{media_url}/{kyc.uploaddocument}',
                            "dateofbirth": kyc.dateofbirth,
                            "zipcode": kyc.zipcode
                        })

            return json({
                    'all_Kyc': kyc_data if kyc_data else [],
                    'all_users': user_data if user_data else [],
                    }, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    




#Add new user by Admin
@docs(responses={200: 'Create new user, Only for Admin'})
@auth('userauth')
@post('/api/v1/admin/add/user/')
async def create_newuser(self, request: Request, user_create_schema: FromJSON[AdminUserCreateSchema]):
    """
    The group field will have (Default User, Merchant) and status field should have (Active, Inactive)
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity    = request.identity
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            data = user_create_schema.value
        
            #Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == adminID))
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

                            # return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                        
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

                            # return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
                        
                    except Exception as e:
                        return json({'msg': f'Wallet create error {str(e)}'}, 400)
                    
                else: 
                    return json({'msg': 'User did not get created'}, 200)
            

            #Create Merchant according to the status
            elif data.group == 'Merchant':
                return json({'msg': 'In progress'}, 200)
            
            else:
                return json({'msg': 'Please provide a valid user type Merchant or Default user'}, 404)

            # return json({'msg': 'User created Successfully', 'data': data}, 200)
            return json({'msg': f'User created successfully {user_first_name} {user_last_name} of ID {userID}'}, 201)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)


 
@get('/api/all/groups/')
async def get_groups(self, request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            try:
                all_groups    = await session.execute(select(Group))
                all_group_obj = all_groups.scalars().all()

            except Exception as e:
                return json({'msg': 'Group fetch error', 'error': f'{str(e)}'}, 400)
            
            return json({'msg': 'Group data fetched successfully', 'data': all_group_obj}, 200)

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)

