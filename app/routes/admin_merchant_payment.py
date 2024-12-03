# from blacksheep import json, Request, get, post, put
# from blacksheep.server.authorization import auth
# from database.db import AsyncSession, async_engine
# from Models.models import BusinessProfile, MerchantTransactions, Currency, Users, Wallet
# from sqlmodel import select, join, and_
# from Models.Merchant.schema import AdminMerchantPaymentUpdateSchema





# UAT Transaction of Businesses which has been removed
#Admin will be able to view the Transactions of the Business
# @auth('userauth')
# @get('/api/v4/admin/merchant/payments/')
# async def admin_merchant_payments(request: Request, limit: int = 25, offset: int = 0):
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             user_id       = user_identity.claims.get('user_id') if user_identity else None
#             combined_data = []


#             if not user_id:
#                 return json({'msg': 'Authentication Failed'}, 401)
            
#             #Check the user is Admin or not
#             try:
#                 is_admin_obj = await session.execute(select(Users).where(Users.id == user_id))
#                 is_adim_obj_detail = is_admin_obj.scalar()

#                 if not is_adim_obj_detail.is_admin:
#                     return json({'msg': 'Admin authentication failed'}, 401)
                
#             except Exception as e:
#                 return json({'msg': 'Admin Identify error', 'error': f'{str(e)}'}, 400)
            

#             #Get Merchant
#             try:
#                 merchant_profiles = await session.execute(select(
#                     BusinessProfile).offset(offset).limit(limit)
#                     ) 
#                 merchant_profiles_data = merchant_profiles.scalars().all()

#             except Exception as e:
#                 return json({'msg': 'Mechant profile error', 'error': f'{str(e)}'}, 400)
            
#             #Get the transaction related to every business
#             for merchant_profile in merchant_profiles_data:
#                 stmt = (select(
#                     MerchantTransactions, 
#                     Currency
#                     ).select_from(
#                         join(MerchantTransactions, Currency, MerchantTransactions.currency == Currency.id)
#                     )).where(MerchantTransactions.merchant == merchant_profile.id)

#                 business_transactions      = await session.execute(stmt)
#                 business_transactions_data = business_transactions.all()

#                 user_obj  = await session.execute(select(Users).where(Users.id == merchant_profile.user))
#                 user_data = user_obj.scalar()

#                 if business_transactions_data:
#                     for business_transaction, currency in business_transactions_data:

#                         combined_data.append({
#                             'business_transaction': {
#                                 'id': business_transaction.id,
#                                 'date': business_transaction.created_date,
#                                 'pay_mode': business_transaction.pay_mode,
#                                 'order_id': business_transaction.order_id,
#                                 'total_amount': business_transaction.amount,
#                                 'fee': business_transaction.fee,
#                                 'amount': business_transaction.credit_amt,
#                                 'status': business_transaction.status,
#                                 'merchant': merchant_profile.bsn_name,
#                                 'currency': currency.name,
#                                 'payer': business_transaction.payer if business_transaction.payer else '-',
#                                 'user': user_data.full_name if user_data else '-',
#                                 'is_completed': business_transaction.is_completed
#                             }
#                         })

#             return json({'msg': 'Business Transactions data fetched successfully', 'data': combined_data}, 200)
        
#     except Exception as e:
#         return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    



# @auth('userauth')
# @put('/api/v4/admin/merchant/payment/update/')
# async def adminMerchantPaymentUpdate(self, request: Request, schema: AdminMerchantPaymentUpdateSchema):
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             admin_id      = user_identity.claims.get('user_id') if user_identity else None

#             if not admin_id:
#                 return json({'msg': 'Authentication Failed'}, 401)
            
#             try:
#                 is_admin_obj = await session.execute(select(Users).where(
#                     Users.id == admin_id
#                 ))
#                 is_admn_data = is_admin_obj.scalar()

#                 if not is_admn_data.is_admin:
#                     return json({'msg': 'Admin authentication failed'}, 401)
                
#             except Exception as e:
#                 return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
#             transaction_id = schema.id
#             status         = schema.status

#             #Get the Merchant transaction
#             try:
#                 merchant_transaction_obj = await session.execute(select(MerchantTransactions).where(
#                     MerchantTransactions.id == transaction_id
#                 ))
#                 merchant_transaction = merchant_transaction_obj.scalar()

#                 if not merchant_transaction:
#                     return json({'msg': 'Requested merchant not found'}, 404)
                
#             except Exception as e:
#                 return json({'msg': 'Merchant transaction fetch error', 'error': f'{str(e)}'}, 400)
            
#             #Get the transaction currency
#             currency_obj = await session.execute(select(Currency).where(
#                 Currency.id == merchant_transaction.currency
#                 ))
#             currency = currency_obj.scalar()
            
#             #Get the merchant profile to get the user
#             try:
#                 merchant_profile_obj = await session.execute(select(BusinessProfile).where(
#                     BusinessProfile.id == merchant_transaction.merchant
#                 ))
#                 merchant_profile = merchant_profile_obj.scalar()
#             except Exception as e:
#                 return json({'msg': 'Merchant profile error', 'error': f'{str(e)}'}, 400)
            
#             #Get The user to get wallet
#             user_obj = await session.execute(select(Users).where(
#                 Users.id == merchant_profile.user
#             ))
#             user = user_obj.scalar()

#             #Get the wallet of the Business owner
#             user_wallet_obj = await session.execute(select(Wallet).where(
#                 and_(Wallet.user_id == user.id, Wallet.currency_id == currency.id)
#             ))
#             user_wallet = user_wallet_obj.scalar()

#             if status == 'Success':
#                 if merchant_transaction.pay_mode == 'Paymoney':
#                     try:
#                         payer = merchant_transaction.payer

#                         if payer == '':
#                             return json({'msg': 'Unidentified user'}, 404)
#                         elif payer == '-':
#                             return json({'msg': 'Unidentified user'}, 404)
#                         elif not payer:
#                             return json({'msg': 'Unidentified user'}, 404)
                        
#                         if payer:
#                             payer_obj = await session.execute(select(Users).where(
#                                 Users.full_name == merchant_transaction.payer
#                             ))
#                             payer = payer_obj.scalars().first()

#                             payer_wallet_obj = await session.execute(select(Wallet).where(
#                                 and_(Wallet.user_id == payer.id, Wallet.currency_id == currency.id)
#                             ))
#                             payer_wallet = payer_wallet_obj.scalar()
                        
#                     except Exception as e:
#                         return json({'msg':'Payer error', 'error': f'{str(e)}'}, 400)
                    
#                     amount             = merchant_transaction.credit_amt
#                     transaction_amount = merchant_transaction.amount

#                     user_wallet_balance  = user_wallet.balance
#                     payer_wallet_balance = payer_wallet.balance

#                     if payer_wallet_balance < transaction_amount:
#                         return json({'msg': 'Payer donot have sufficient wallet balance'}, 403)

#                     user_wallet_balance  += amount
#                     payer_wallet_balance -= transaction_amount

#                     user_wallet.balance  = user_wallet_balance
#                     payer_wallet.balance = payer_wallet_balance

#                     merchant_transaction.status       = 'Success'
#                     merchant_transaction.is_completed = True

#                     session.add(user_wallet)
#                     session.add(payer_wallet)
#                     session.add(merchant_transaction)

#                     await session.commit()

#                     await session.refresh(user_wallet)
#                     await session.refresh(payer_wallet)
#                     await session.refresh(merchant_transaction)

#                     return json({'msg': 'Transaction updated successfully'}, 200)

#                 else:
#                     amount = merchant_transaction.credit_amt

#                     user_wallet_balance = user_wallet.balance

#                     user_wallet_balance  += amount

#                     user_wallet.balance = user_wallet_balance

#                     merchant_transaction.status       = 'Success'
#                     merchant_transaction.is_completed = True

#                     session.add(user_wallet)
#                     session.add(merchant_transaction)

#                     await session.commit()

#                     await session.refresh(user_wallet)
#                     await session.refresh(merchant_transaction)

#                     return json({'msg': 'Transaction updated successfully'}, 200)

#             elif status == 'Pending':
#                 merchant_transaction.status       = 'Pending'
#                 merchant_transaction.is_completed = False

#                 session.add(merchant_transaction)
#                 await session.commit()
#                 await session.refresh(merchant_transaction)

#                 return json({'msg': 'Transaction updated successfully'}, 200)
            
#             else:
#                 merchant_transaction.status       = 'Cancelled'
#                 merchant_transaction.is_completed = False

#                 session.add(merchant_transaction)
#                 await session.commit()
#                 await session.refresh(merchant_transaction)

#                 return json({'msg': 'Transaction updated successfully'}, 200)
            
#     except Exception as e:
#         return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    
