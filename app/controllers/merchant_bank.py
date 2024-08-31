from blacksheep import json, Request, FromForm, FromFiles, FromJSON
from app.controllers.controllers import get, post, put, delete
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.Merchant.schema import (
    MerchantCreateBankAccountSchema, MerchantUpdateBankAccountSchema
    )
from app.req_stream import save_merchant_bank_doc, delete_old_file
from sqlmodel import select, and_
from Models.models import Users, MerchantBankAccount, Currency
from pathlib import Path
from .environment import media_url



#Creeat, Update, Delete Bank account by Merchant
class MerchantBankAccountController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return super().class_name()
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/merchant/bank/'
    
    
    #Create New bank Account by Merchant
    @auth('userauth')
    @post()
    async def create_merchantAccount(self, request: Request, schema: FromForm[MerchantCreateBankAccountSchema], file: FromFiles):

        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                value   = schema.value
                data    = file.value

                acc_holder_name = value.hldr_name
                acc_holder_add  = value.hldr_add
                acc_no          = value.acc_no
                short_code      = value.srt_code
                ifsc            = value.ifsc_code
                bank_name       = value.bnk_name
                bank_add        = value.bnk_add
                add_info        = value.add_info
                req_cur         = value.curr

                # await save_merchant_bank_doc(data, request)

                #Get the user
                try:
                    merchant_obj = await session.execute(select(Users).where(
                        Users.id == user_id
                    ))
                    merchant = merchant_obj.scalar()

                except Exception as e:
                    return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)

                if not merchant:
                    return json({'msg': 'Requested merchant not found'}, 404)
                
                if not merchant.is_merchent:
                    return json({'msg': 'Only Accessible by merchant'}, 400)
                
                try:
                    currency_obj = await session.execute(select(Currency).where(
                        Currency.name == req_cur
                    ))
                    currecy = currency_obj.scalar()
                except Exception as e:
                    return json({'msg': 'Currency Error'}, 400)
                
                if data:
                    doc_path = await save_merchant_bank_doc(data, request)

                    if doc_path == 'File size exceeds the maximum allowed size':
                        return json({'msg': 'File size exceeds the maximum allowed size'}, 403)
                    
                    elif doc_path == 'File name is missing':
                        return json({'msg': 'File name is missing'}, 403)
                    else:
                        path = doc_path
                else:
                    path = ''
                

                merchant_bank_account = MerchantBankAccount(
                    user          = merchant.id,
                    acc_hold_name = acc_holder_name,
                    acc_hold_add  = acc_holder_add,
                    acc_no        = acc_no,
                    short_code    = short_code,
                    ifsc_code     = ifsc,
                    bank_name     = bank_name,
                    bank_add      = bank_add,
                    add_info      = add_info,
                    currency      = currecy.id,
                    doc           = path,
                )

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Bank account created successfully'}, 200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        

    #Update the bank Account details by Merchant
    @auth('userauth')
    @put()
    async def update_merchantAccount(self, request: Request, schema: FromForm[MerchantUpdateBankAccountSchema], file: FromFiles):

        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                value   = schema.value
                data    = file.value

                acc_holder_name  = value.hldr_name
                acc_holder_add   = value.hldr_add
                acc_no           = value.acc_no
                short_code       = value.srt_code
                ifsc             = value.ifsc_code
                bank_name        = value.bnk_name
                bank_add         = value.bnk_add
                add_info         = value.add_info
                req_cur          = value.curr
                merchant_bank_id = value.mrc_bnk_id
                merchant_bank_id = int(merchant_bank_id)

                #Get the user
                try:
                    merchant_obj = await session.execute(select(Users).where(
                        Users.id == user_id
                    ))
                    merchant = merchant_obj.scalar()
                    
                except Exception as e:
                    return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)

                if not merchant:
                    return json({'msg': 'Requested merchant not found'}, 404)
                
                if not merchant.is_merchent:
                    return json({'msg': 'Only Accessible by merchant'}, 400)
                
                #Get the Merchant Bank Account
                try:
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        and_(MerchantBankAccount.id == merchant_bank_id, MerchantBankAccount.user == merchant.id)
                    ))
                    merchant_bank_account = merchant_bank_account_obj.scalar()

                    if not merchant_bank_account:
                        return json({'msg': 'Requested Account not found'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
                
                #Get the related Currency
                try:
                    currency_obj = await session.execute(select(Currency).where(
                        Currency.name == req_cur
                    ))
                    currecy = currency_obj.scalar()
                except Exception as e:
                    return json({'msg': 'Currency Error'}, 400)
                
                # Check request stream contain document or not
                if data:
                    doc_path = await save_merchant_bank_doc(data, request)

                    if doc_path == 'File size exceeds the maximum allowed size':
                        return json({'msg': 'File size exceeds the maximum allowed size'}, 403)

                    elif doc_path == 'File name is missing':
                        return json({'msg': 'File name is missing'}, 403)

                    else:
                        path = doc_path

                        if merchant_bank_account.doc:
                            old_doc = Path('Static') / merchant_bank_account.doc
                            delete_old_file(old_doc)
                else:
                    path = merchant_bank_account.doc
                
                merchant_bank_account.user          = merchant_bank_account.user
                merchant_bank_account.acc_hold_name = acc_holder_name
                merchant_bank_account.acc_hold_add  = acc_holder_add
                merchant_bank_account.acc_no        = acc_no
                merchant_bank_account.short_code    = short_code
                merchant_bank_account.ifsc_code     = ifsc
                merchant_bank_account.bank_name     = bank_name
                merchant_bank_account.bank_add      = bank_add
                merchant_bank_account.add_info      = add_info
                merchant_bank_account.currency      = currecy.id
                merchant_bank_account.doc           = path

                session.add(merchant_bank_account)
                await session.commit()
                await session.refresh(merchant_bank_account)

                return json({'msg': 'Bank account updated successfully'}, 200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        
    
    #Delete bank account by Merchant
    @auth('userauth')
    @delete()
    async def delete_merchantAccount(self, request: Request,  query: int):

        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # value            = schema.value
                merchant_bank_id = query

                #Get the user
                try:
                    merchant_obj = await session.execute(select(Users).where(
                        Users.id == user_id
                    ))
                    merchant = merchant_obj.scalar()
                    
                except Exception as e:
                    return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)

                if not merchant:
                    return json({'msg': 'Requested merchant not found'}, 404)
                
                # if not merchant.is_merchent:
                #     return json({'msg': 'Only Accessible by merchant'}, 400)
                
                #Get the Merchant Bank Account
                try:
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        and_(MerchantBankAccount.id == merchant_bank_id, MerchantBankAccount.user == merchant.id)
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

                #Delete Merchant Bank Account
                await session.delete(merchant_bank_account)
                await session.commit()

                return json({'msg': 'Bank account deleted successfully'}, 200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        
    
    #Get all available banks of a user by Merchant
    @auth('userauth')
    @get()
    async def GetMerchantBank(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []
                
                #Get the Merchant Bank Account
                try:
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    MerchantBankAccount.user == user_id
                    ))
                    merchant_bank_accounts = merchant_bank_account_obj.scalars().all()

                    if not merchant_bank_accounts:
                        return json({'msg': 'Account not found'}, 404)

                except Exception as e:
                    return json({'msg': 'Merchant bank account error', 'error': f'{str(e)}'}, 400)
                

                
                for merchant_bank in merchant_bank_accounts:

                    try: 
                        currency_obj = await session.execute(select(Currency).where(
                            Currency.id == merchant_bank.currency
                        ))
                        currency = currency_obj.scalar()

                    except Exception as e:
                        return json({'msg': 'Currency error', 'error': f'{str(e)}'}, 400)
  
                    combined_data.append({
                            "user":          merchant_bank.user,
                            "acc_no":        merchant_bank.acc_no,
                            "id":            merchant_bank.id,
                            "acc_hold_name": merchant_bank.acc_hold_name,
                            "ifsc_code":     merchant_bank.ifsc_code,
                            "bank_name":     merchant_bank.bank_name,
                            "add_info":      merchant_bank.add_info,
                            "doc":           f'{media_url}{merchant_bank.doc}' if merchant_bank.doc else None,
                            "acc_hold_add":  merchant_bank.acc_hold_add,
                            "short_code":    merchant_bank.short_code,
                            "bank_add":      merchant_bank.bank_add,
                            "currency": {
                                'name':      currency.name
                            },
                            "is_active":     merchant_bank.is_active
                    })
                
                return json({'msg': 'Merchant bank accounts fetched successfully', 'data': combined_data})

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)

