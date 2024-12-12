# from blacksheep import json, post, Request, FromJSON
# from blacksheep.server.authorization import auth
# from database.db import AsyncSession, async_engine
# from sqlmodel import select
# from Models.models import Users, Transection, Currency, Wallet
# from Models.Admin.Deposit.schema import AdminDepositTransactionFilterSchema
# from datetime import datetime




# @auth('userauth')
# @post('/api/v1/admin/filter/deposit/')
# async def filter_fiat_Deposit_transaction(self, request: Request, schema: FromJSON[AdminDepositTransactionFilterSchema]):
#     """
#      Admin will be able to Filter Deposit Transactions
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             AdminID       = user_identity.claims.get('user_id') if user_identity else None

#             filter_data = schema.value

#             #Check the user is Admin or not
#             try:
#                 admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
#                 admin_obj_data = admin_obj.scalar()

#                 if not admin_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 401)
                
#             except Exception as e:
#                 return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)

#             try:
#                 all_user_obj      = await session.execute(select(Users))
#                 all_user_obj_data = all_user_obj.scalars().all()

#                 if not all_user_obj_data:
#                     return json({'msg': 'No users available'})
                
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            

#             #Get all the input values
#             from_date_str = filter_data.from_date
#             to_date_str   = filter_data.to_date
#             currency      = filter_data.currency
#             status        = filter_data.status
#             user_name     = filter_data.user_name
#             payment_mode  = filter_data.pay_mode


#             try:
#                 query = select(Transection).where(Transection.txdtype == 'Deposit')
#             except Exception as e:
#                 return json({'msg': 'Transaction fetch error', 'error': f'{str(e)}'}, 400)
            
#             if from_date_str:
#                 from_datetime = datetime.strptime(from_date_str, '%Y-%m-%d')
#                 from_date     = from_datetime.date()

#                 query = query.where(Transection.txddate >= from_date)

#             if to_date_str:
#                 to_datetime = datetime.strptime(to_date_str, '%Y-%m-%d')
#                 to_date    = to_datetime.date()

#                 query = query.where(Transection.txddate <= to_date)

#             if currency is not None:
#                 currency_obj = await session.execute(select(Currency).where(Currency.name == currency))
#                 currency_data = currency_obj.scalar()

#                 if currency_data:
#                     query = query.where(Transection.txdcurrency == currency_data.id)
            
#             if status is not None:
#                 query = query.where(Transection.txdstatus == status)

#             if user_name is not None:
#                 user_search_id   = None

#                 for user in all_user_obj_data:
#                     if user.full_name == user_name:
#                         user_search_id  = user.id

#                 query = query.where(Transection.user_id == user_search_id)

#             if payment_mode is not None:
#                 query = query.where(Transection.payment_mode == payment_mode)

            
#             result            = await session.execute(query)
#             transactions_list = result.scalars().all()

#             try:
#                 currency_obj      = await session.execute(select(Currency))
#                 all_currency_data = currency_obj.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
#             #Get the converted currency wallet
#             try:
#                 converted_currency_wallet     = await session.execute(select(Wallet))
#                 converted_currency_wallet_obj = converted_currency_wallet.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
            
#             currency_dict                  = {currency.id: currency for currency in all_currency_data}
#             user_dict                      = {user.id: user for user in all_user_obj_data}
#             converted_currency_wallet_dict = {wallet.id: wallet for wallet in converted_currency_wallet_obj}
#             combined_data = []

#             for transaction in transactions_list:

#                 currency_id             = transaction.txdcurrency
#                 currency_data           = currency_dict.get(currency_id)
                
#                 user_id   = transaction.user_id
#                 user_data = user_dict.get(user_id)

#                 converted_currency_id = transaction.wallet_id
#                 converted_currency    = converted_currency_wallet_dict.get(converted_currency_id)

#                 combined_data.append({
#                     'transaction': transaction,
#                     'currency': currency_data,
#                     'user': user_data,
#                     'converted_currency': converted_currency if converted_currency else None
#                         })
                
#             return json({'msg': 'Deposit Transaction data fetched successfully', 'data': combined_data})

#     except Exception as e:
#         return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)