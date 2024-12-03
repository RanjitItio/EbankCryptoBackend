from blacksheep import json, Request, put, get, delete, FromJSON
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, MerchantBankAccount, Currency
from Models.Merchant.schema import AdminMerchantBankApproveSchema, AdminMerchantBanksSchema
from sqlmodel import select, and_
from app.req_stream import delete_old_file
from pathlib import Path
from .environment import media_url




#Admin will be able to Approve Merchant bank accounts
@auth('userauth')
@put('/api/v3/admin/merchant/bank/update/')
async def ApproveMerchantBank(self, request: Request, schema: FromJSON[AdminMerchantBankApproveSchema]):
    """
        This API Endpoint let Admin user to update the status of Merchanr bank account.<br/><br/>

        Parameters:<br/>
            - request (Request): The request object containing the user's identity and payload data.<br/>
            - schema (FromJSON[AdminMerchantBankApproveSchema]): The schema object containing the merchant_bnk_id and status.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the success status, message, or error details.<br/>
            - On Success - 'msg': 'Updated Successfully'.<br/><br/>
        
        Error Messages:<br/>
            - 'msg': 'Admin authentication error'<br/>
            - 'msg': 'Admin authorization failed'<br/>
            - 'msg': 'Requested Account not found'<br/>
            - 'msg': 'Merchant bank account error'<br/>
            - 'msg': 'Server Error'<br/><br/>

        Raises:<br/>
            Exception: If any error occurs during the operation, JSON response with an appropriate error message is returned.<br/>
            - Error 400: 'Invalid data'<br/>
            - Error 401: 'authorization failed'<br/>
            - Error 404: 'Requested Account not found'<br/>
            - Error 500: 'Server Error'<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')

            values          = schema.value
            merchant_bnk_id = values.mrc_bnk_id
            user_id         = values.user_id
            status          = values.status

            try:
                is_admin_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_obj_data = is_admin_obj.scalar()

                if not is_admin_obj_data.is_admin:
                    return json({'msg': 'Admin authorization failed'}, 401)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
            #Get the Merchant Bank Account
            try:
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    and_(MerchantBankAccount.id == merchant_bnk_id, MerchantBankAccount.user == user_id)
                ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                if not merchant_bank_account:
                    return json({'msg': 'Requested Account not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
            
            #If the Status is Active
            if status == 'Approve':
                
                merchant_bank_account.is_active = True

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Updated Successfully'}, 200)
            #If the status is Inactive
            elif status == 'Reject':
                
                merchant_bank_account.is_active = False

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Updated Successfully'}, 200)

            #For other case
            else:
                
                merchant_bank_account.is_active = False

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Updated Successfully'}, 200)
            
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    




#Get a users specific bank account details
@auth('userauth')
@get('/api/v4/admin/merchant/bank/')
async def GetMerchantBankDetails(self, request: Request, query: int):
    """
        Admin will be able to view the details of a Merchant Bank Account.<br/><br/>

        Parameters:<br/>
            query (int): Merchant Bank Account ID.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            JSON: Returns a JSON object with the Merchant Bank Account details.<br/>
            'data': JSON object with Merchant Bank Account details.<br/>
            If any error occurs, a JSON response with error status and error message is returned.<br/><br/>

        Raises:<br/>
            Exception: If any error occurs during the database query or response generation.<br/><br/>
        
        Error Messages:<br/>
            - Error 401: 'Unauthorized Access'.<br/>
            - Error 403: 'Unauthorized Access'.<br/>
            - Error 404: 'Requested Account not found'.<br/>
            - Error 500: 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')

            if not query:
                return json({'msg': 'Unrecognized data'}, 403)
            
            merchant_bank_acc = query

            #Authenticate as Admin
            try:
                is_admin_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_obj_data = is_admin_obj.scalar()

                if not is_admin_obj_data.is_admin:
                    return json({'msg': 'Admin authorization failed'}, 401)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
             #Get the Merchant Bank Account
            try:
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                   MerchantBankAccount.id == merchant_bank_acc
                ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                if not merchant_bank_account:
                    return json({'msg': 'Requested Account not found'}, 404)

            except Exception as e:
                return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
            
            
            return json({'msg': 'Merchant bank details fetched successfully', 'data': merchant_bank_account})
            
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)



#Get a Merchants all available bank accounts 
@auth('userauth')
@get('/api/v4/admin/all/merchant/bank/')
async def GetMerchantBanks(self, request: Request, query: int):
    """
        Get all the available bank accounts and it details of a specific merchant.<br/><br/>

        Parameters:<br/>
            - query (int): User ID of the merchant whose bank accounts to fetch.<br/>
            - request (Request): The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the bank accounts of the merchant(data) with message(msg). <br/>
            - If the merchant is not found, returns a 404 status code. <br/>
            - If an error occurs, returns a 500 status code.<br/><br/>

        Error Messages:<br/>
            - Admin authorization failed: If the user is not an admin.<br/>
            - Merchant bank account error: If there is an error while fetching the bank accounts.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database operations or processing.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')
            
            mer_bank_user_id = query

            #Authenticate as Admin
            try:
                is_admin_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_obj_data = is_admin_obj.scalar()

                if not is_admin_obj_data.is_admin:
                    return json({'msg': 'Admin authorization failed'}, 401)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
            #Get the Merchant Bank Account
            try:
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                   MerchantBankAccount.user == mer_bank_user_id
                ))
                merchant_bank_accounts = merchant_bank_account_obj.scalars().all()

                if not merchant_bank_accounts:
                    return json({'msg': 'Bank account not found'}, 404)

            except Exception as e:
                return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
            

            #Get the user with specific ID
            try:
                user_obj = await session.execute(select(Users).where(
                    Users.id == mer_bank_user_id
                ))
                user = user_obj.scalar()

                if not user:
                    return json({'msg': 'User not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
            
            combined_data = []

            for merchant_account in merchant_bank_accounts:
                try:
                    currency_obj = await session.execute(select(Currency).where(Currency.id == merchant_account.currency))
                    currency = currency_obj.scalar()
                except Exception as e:
                    return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)

                combined_data.append({
                    'user': {    
                        'user_id': user.id,
                        'user_email': user.email,
                        'user_name': user.full_name
                    },
                    'account': {
                        'acc_no': merchant_account.acc_no,
                        'id' : merchant_account.id,
                        'acc_holder_name': merchant_account.acc_hold_name,
                        'ifsc_code': merchant_account.ifsc_code,
                        'bank_name': merchant_account.bank_name,
                        'add_info': merchant_account.add_info,
                        'doc': f'{media_url}{merchant_account.doc}',
                        'acc_hold_add': merchant_account.acc_hold_add,
                        'short_code': merchant_account.short_code,
                        'bank_add': merchant_account.bank_add,
                        'currency': currency.name if currency else None,
                        'is_active': merchant_account.is_active
                    } 
                })
            
            return json({'msg': 'Merchant bank accounts fetched successfully', 'data': combined_data})
            
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    


#Admin will be able to delete the bank account
@auth('userauth')
@delete()
async def delete_merchantAccount(self, request: Request, query: int):

    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')

            merchant_bank_id = query

            #Authenticate as Admin
            try:
                is_admin_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                is_admin_obj_data = is_admin_obj.scalar()

                if not is_admin_obj_data.is_admin:
                    return json({'msg': 'Admin authorization failed'}, 401)

            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            

            #Get the Merchant Bank Account
            try:
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    MerchantBankAccount.id == merchant_bank_id
                ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                if not merchant_bank_account:
                    return json({'msg': 'Requested Account not found'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
            
            # Delete previous file of User
            if merchant_bank_account.doc:
                old_doc = Path('Static') / merchant_bank_account.doc
                delete_old_file(old_doc)

            await session.delete(merchant_bank_account)
            await session.commit()

            return json({'msg': 'Bank account deleted successfully'}, 200)

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    

