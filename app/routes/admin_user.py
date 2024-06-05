from blacksheep.server.controllers import APIController
from Models.schemas import UserDeleteSchema, AdminUpdateUserSchema, AdminUserCreateSchema
from blacksheep import FromJSON, Request, json, delete, put, get, post
from database.db import AsyncSession, async_engine
from app.docs import docs
from app.auth import decode_token, encrypt_password, check_password
from Models.models import Users, Kycdetails, Transection, Wallet, Currency, TestModel, Group
from sqlmodel import select
from blacksheep.server.authorization import auth
from typing import List
from datetime import datetime





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
    



#Update user by Admin
@docs(responses={200: 'Update user profile and kyc status'})
@auth('userauth')
@put('/api/v1/admin/update/user/')
async def update_user(self, request: Request, user_update_schema: FromJSON[AdminUpdateUserSchema]):
    """
     Update the user profile and kyc, Only admin can access the url
     The status filed should contain thress type of value(Active, Inactive, Suspended) and
     the group field should contain (Default User, Merchant Regular)
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity    = request.identity
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            value = user_update_schema.value

            dob_str  = value.dob
            dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
            #Check the user is admin or Not
            try:
                user_obj      = await session.execute(select(Users).where(Users.id == adminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can create users'}, 400)

            except Exception as e:
                return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            #Autnentication ends here
            

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
            
            if existing_mail_obj:
                if existing_mail_obj.email != user_data_obj.email:
                    return json({'msg': 'Provided mail ID already exists'}, 200)
                
            if existing_mobile_number_obj:
                if existing_mobile_number_obj.phoneno != user_data_obj.phoneno:
                    return json({'msg': 'Provided Mobile No already exists'}, 200)
            
            # if value.password:
            #     password = value.password
            # else:
            #     password = user_data_obj.password

            # if  value.confirm_password:
            #     confirm_password = value.confirm_password
            # else:
            #     confirm_password = user_data_obj.password

            # print(password)

            #Check the given password matching or not
            # if password != confirm_password:
            #     return json({'msg': 'Password did not match'}, 400)

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
                    #Update user
                    try:
                        user_data_obj.first_name   = value.first_name
                        user_data_obj.lastname     = value.last_name
                        user_data_obj.phoneno      = value.phoneno
                        user_data_obj.email        = value.email
                        # user_data_obj.password     = encrypt_password(password)
                        user_data_obj.is_active    = True
                        user_data_obj.is_verified  = True
                        user_data_obj.is_suspended = False
                        user_data_obj.group        = value.group

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
    
                #If the status is inactive
                elif value.status == 'Inactive':
                    #Update user data according to Inactive status
                    try:
                        user_data_obj.first_name  = value.first_name
                        user_data_obj.lastname    = value.last_name
                        user_data_obj.phoneno     = value.phoneno
                        user_data_obj.email       = value.email
                        # user_data_obj.password    = encrypt_password(password)
                        user_data_obj.is_active   = False
                        user_data_obj.is_verified = False
                        user_data_obj.group       = value.group

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
                        # user_data_obj.password     = encrypt_password(password)
                        user_data_obj.is_active    = True
                        user_data_obj.is_verified  = True
                        user_data_obj.is_suspended = True
                        user_data_obj.group        = value.group

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
                    return json({'msg': 'Please provide valid user status'}, 400)
                
                #If the user group is Merchant
                # elif value.group == 'Merchant Regular':
                #     return json({'msg': 'Work in progress'}, 200)

            except Exception as e:
                return json({'msg': 'User update error', 'error': f'{str(e)}'}, 400)


            return json({'msg': 'User data updated successfully'}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



#Search users
@docs(responses={200: 'Search Users'})
@auth('userauth')
@get('/api/v1/admin/user/search/')
async def get_searchedeusers(self, request: Request, query: str = ''):
    """
     Search users by (First name, Last name, Active, Inactive, email, phoneno, City, State, Address)
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity    = request.identity
            adminID          = user_identity.claims.get("user_id") if user_identity else None

            data = query
        
            #Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == adminID))
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

            all_users: List[Users] = searched_user_obj.scalars().all()

            combined_data = []

            for user in all_users:
                kyc_detail     = await session.execute(select(Kycdetails).where(Kycdetails.user_id == user.id))
                kyc_detail_obj = kyc_detail.scalar()

                users_data = {
                    "id": user.id,
                    'ip_address': user.ipaddress, 
                    'lastlogin': user.lastlogin, 
                    'merchant': user.is_merchent, 
                    'admin': user.is_admin,
                    'active': user.is_active,
                    'verified': user.is_verified,
                    'group': user.group
                } 
            

                combined_data.append({
                    'user_kyc_details': kyc_detail_obj,
                    'user': users_data
                })

            return json({'all_Kyc': combined_data}, 200)
        
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


@post('/api/test/date/')
async def test_api(self, request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # create_test_model = TestModel()
            request_body = await request.json()
            first_name = request_body['first_name']
            last_name = request_body['last_name']
            print(first_name)
            
            test_model = TestModel(
                first_name = first_name,
                last_name = last_name
            )

            session.add(test_model)
            await session.commit()
            await session.refresh(test_model)
            
    except Exception as e:
        return json({'msg': f'{str(e)}'}, 500)
    
    return json({'msg': 'Success'})