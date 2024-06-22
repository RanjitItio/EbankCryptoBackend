from blacksheep import json, Request, put, get, delete, FromJSON
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, MerchantBankAccount
from Models.Merchant.schema import AdminMerchantBankApproveSchema, AdminMerchantBanksSchema
from sqlmodel import select, and_
from app.req_stream import delete_old_file
from pathlib import Path




@auth('userauth')
@put('/api/v3/admin/merchant/bank/update/')
async def ApproveMerchantBank(self, request: Request, schema: FromJSON[AdminMerchantBankApproveSchema]):
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
            if status == 'Active':
                
                merchant_bank_account.is_active = True

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Updated Successfully'}, 200)
            #If the status is Inactive
            elif status == 'Inactive':
                
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
                    return json({'msg': 'Requested Account not found'}, 404)

            except Exception as e:
                return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
            
            
            return json({'msg': 'Merchant bank accounts fetched successfully', 'data': merchant_bank_accounts})
            
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    


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
    

