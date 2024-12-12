# from blacksheep import json, Request, FromJSON, get, post
# from database.db import AsyncSession, async_engine
# from blacksheep.server.authorization import auth
# from sqlmodel import select
# from Models.models import Users,  Transection, Currency, ReceiverDetails, Wallet
# from app.docs import docs
# from decouple import config
# from httpx import AsyncClient
# from Models.Admin.AllTransaction.schema import AdminAllTransactionFilterSchema
# from datetime import datetime
# import re



# currency_converter_api = config('CURRENCY_CONVERTER_API')
# RAPID_API_KEY          = config('RAPID_API_KEY')
# RAPID_API_HOST         = config('RAPID_API_HOST')



# #Admin will be able to view the details of a Transaction
# @docs()
# @auth('userauth')
# @get('/api/v2/admin/transaction/details/{transaction_id}')
# async def each_transaction_details(self, request: Request, transaction_id: int):
#     """
#      Admin will be able to view the details of a Transaction
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             AdminID       = user_identity.claims.get('user_id') if user_identity else None

#             #Check the user is Admin or not
#             try:
#                 admin_obj = await session.execute(select(Users).where(Users.id == AdminID))
#                 admin_obj_data = admin_obj.scalar()

#                 if not admin_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 401)
                
#             except Exception as e:
#                 return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
#             try:
#                 transaction_id_obj     = await session.execute(select(Transection).where(Transection.id == transaction_id))
#                 transaction_id_details = transaction_id_obj.scalar()

#                 if not transaction_id_details:
#                     return json({'msg': 'Transaction does not exist'}, 404)
                
#             except Exception as e:
#                 return json({'msg': 'Transaction error', 'error': f'{str(e)}'}, 400)
            
#              #Get the user data
#             try:
#                 user_obj      = await session.execute(select(Users))
#                 user_obj_data = user_obj.scalars().all()

#                 if not user_obj_data:
#                     return json({'msg': 'User is not available'}, 404)
                
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            
            
#             #Get all currency data
#             try:
#                 currency_obj      = await session.execute(select(Currency))
#                 currency_obj_data = currency_obj.scalars().all()

#                 if not currency_obj_data:
#                     return json({'msg': 'Currency is not available'}, 404)
                
#             except Exception as e:
#                 return json({'msg': 'Currency not found'}, 400)
            
           
#             try:
#                 receiver_details_obj      = await session.execute(select(ReceiverDetails))
#                 receiver_details_obj_data = receiver_details_obj.scalars().all()

#                 if not receiver_details_obj_data:
#                     pass
                
#             except Exception as e:
#                 return json({'msg': 'Receiver details not found'}, 400)
            
            
#             receiver_dict         = {receiver.id: receiver for receiver in user_obj_data}
#             sender_dict           = {sender.id: sender for sender in user_obj_data}
#             currency_dict         = {currency.id: currency for currency in currency_obj_data}
#             receiver_details_dict = {receiver_details.id: receiver_details for receiver_details in receiver_details_obj_data}

            
            
#             combined_data = []

#             receiver_id   = transaction_id_details.txdrecever
#             receiver_data = receiver_dict.get(receiver_id, None)

#             sender_id   = transaction_id_details.user_id
#             sender_data = sender_dict.get(sender_id)

#             currency_id   = transaction_id_details.txdcurrency
#             currency_data = currency_dict.get(currency_id, None)


#             receiver_details_id = transaction_id_details.rec_detail
#             receiver_details_data = receiver_details_dict.get(receiver_details_id, None)

#             # print(receiver_details_data)
#             if receiver_details_data:
#                 sender_currency      = currency_data.name
#                 receiver_currency_id = receiver_details_data.currency

#                 try:
#                     receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_currency_id))
#                     receiver_currency_data = receiver_currency.scalar()
#                     sender_amount          = transaction_id_details.amount

#                     if not receiver_currency_data:
#                         return json({'msg': 'Receiver currency not found'}, 404)
                    
#                     receiver_currency_name = receiver_currency_data.name
                
#                 except Exception as e:
#                     return json({'msg': 'Currency not found'}, 400)

#                 # Call API to convert the Currency value
#                 #Call API
#                 try:
#                     url = f"{currency_converter_api}/convert?from={sender_currency}&to={receiver_currency_name}&amount={sender_amount}"
#                     headers = {
#                     'X-RapidAPI-Key': f"{RAPID_API_KEY}",
#                     'X-RapidAPI-Host': f"{RAPID_API_HOST}"
#                 }
                    
#                     async with AsyncClient() as client:
#                         response = await client.get(url, headers=headers)
#                         # print('APi Response', response)

#                         if response.status_code == 200:
#                             api_data = response.json()
#                             # print('api data', api_data)

#                         else:
#                             return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                        
#                 except Exception as e:
#                     return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

#                 converted_amount = api_data['result'] if 'result' in api_data else None

#                 if not converted_amount:
#                     return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                
#             elif transaction_id_details.txdrecever:
#                 sender_currency      = currency_data.name
#                 receiver_currency_id = transaction_id_details.rec_currency
#                 sender_amount        = transaction_id_details.amount

#                 try:
#                     receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_currency_id))
#                     receiver_currency_data = receiver_currency.scalar()

#                     if not receiver_currency_data:
#                         return json({'msg': 'Receiver currency not found'}, 404)
                    
#                     receiver_currency_name = receiver_currency_data.name
                
#                 except Exception as e:
#                     return json({'msg': 'Currency not found'}, 400)

#                 # Call API to convert the Currency value
#                 #Call API
#                 try:
#                     url = f"{currency_converter_api}/convert?from={sender_currency}&to={receiver_currency_name}&amount={sender_amount}"
#                     headers = {
#                     'X-RapidAPI-Key': f"{RAPID_API_KEY}",
#                     'X-RapidAPI-Host': f"{RAPID_API_HOST}"
#                 }
                    
#                     async with AsyncClient() as client:
#                         response = await client.get(url, headers=headers)
#                         # print('APi Response', response)

#                         if response.status_code == 200:
#                             api_data = response.json()
#                             # print('api data', api_data)

#                         else:
#                             return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                        
#                 except Exception as e:
#                     return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

#                 converted_amount = api_data['result'] if 'result' in api_data else None

#                 if not converted_amount:
#                     return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                
#             elif transaction_id_details.txdtype == 'Deposit':
#                 deposit_currency            = currency_data.name
#                 selected_wallet             = transaction_id_details.wallet_id
#                 deposit_amount              = transaction_id_details.amount

#                 try:
#                     deposit_selected_wallet      = await session.execute(select(Wallet).where(Wallet.id == selected_wallet))
#                     deposit_selected_wallet_data = deposit_selected_wallet.scalar()

#                     if not deposit_selected_wallet_data:
#                         return json({'msg': 'Selcted Wallet not found'}, 404)
                
#                 except Exception as e:
#                     return json({'msg': 'Selcted Wallet error', 'error': f'{str(e)}'}, 400)
                

#                 try:
#                     selected_wallet_currency      = await session.execute(select(Currency).where(Currency.id == deposit_selected_wallet_data.currency_id))
#                     selected_wallet_currency_data = selected_wallet_currency.scalar()

#                     if not selected_wallet_currency_data:
#                         return json({'msg': 'Selcted Wallet currency not found'}, 404)
                
#                 except Exception as e:
#                     return json({'msg': 'Selcected Wallet Currency error', 'error': f'{str(e)}'}, 400)

#                 # Call API to convert the Currency value
#                 #Call API
#                 try:
#                     url = f"{currency_converter_api}/convert?from={deposit_currency}&to={selected_wallet_currency_data.name}&amount={deposit_amount}"
#                     headers = {
#                     'X-RapidAPI-Key': f"{RAPID_API_KEY}",
#                     'X-RapidAPI-Host': f"{RAPID_API_HOST}"
#                 }
                    
#                     async with AsyncClient() as client:
#                         response = await client.get(url, headers=headers)
#                         # print('APi Response', response)

#                         if response.status_code == 200:
#                             api_data = response.json()
#                             # print('api data', api_data)

#                         else:
#                             return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                        
#                 except Exception as e:
#                     return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

#                 converted_amount = api_data['result'] if 'result' in api_data else None

#                 if not converted_amount:
#                     return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                
                

#             transaction_data = {
#                     'transaction_id': transaction_id_details.id,

#                     'sender': {
#                         'first_name': sender_data.first_name if sender_data else None,
#                         'last_name': sender_data.lastname    if sender_data else None,
#                         'id': sender_data.id                 if sender_data else None
#                          } if sender_data else None,

#                     'txdid': transaction_id_details.txdid,
#                     'send_amount': transaction_id_details.amount,
#                     # Deposit
#                     'deposit_selected_wallet_currency': selected_wallet_currency_data.name if transaction_id_details.wallet_id else None,
#                     'deposit_currency': deposit_currency if transaction_id_details.wallet_id else None,
#                     'converted_deposit_amount': converted_amount if transaction_id_details.wallet_id else None,

#                     'transaction_fee': transaction_id_details.txdfee,
#                     'total_amount': transaction_id_details.totalamount,
#                     'receiver_curreny': currency_dict[transaction_id_details.rec_currency].name if transaction_id_details.rec_currency else None,
#                     'receiver_amount': converted_amount if transaction_id_details.txdrecever else None,
#                     'message': transaction_id_details.txdmassage,
#                     'transaction_status': transaction_id_details.txdstatus,
#                     'transaction_type': transaction_id_details.txdtype,
#                     'sender_payment_mode': transaction_id_details.payment_mode,
#                     'receiver_payment_mode': transaction_id_details.rec_pay_mode,
#                     'transaction_date': transaction_id_details.txddate,
#                     'transaction_time': transaction_id_details.txdtime,
#                     'is_completed': transaction_id_details.is_completed,

#                     'receiver': {
#                         'first_name': receiver_data.first_name if receiver_data else None,
#                         'last_name': receiver_data.lastname if receiver_data else None,
#                         'email': receiver_data.email if receiver_data else None,
#                         'id': receiver_data.id if receiver_data else None,
#                     } if receiver_data else None,

#                     'sender_currency': {
#                         'name': currency_data.name if currency_data else None
#                     } if currency_data else None,

#                     'receiver_details': {
#                         'full_name': receiver_details_data.full_name,
#                         'email': receiver_details_data.email,
#                         'mobile_number': receiver_details_data.mobile_number,
#                         'amount': receiver_details_data.amount,
#                         'pay_mode': receiver_details_data.pay_via,
#                         'bank_name': receiver_details_data.bank_name,
#                         'acc_no': receiver_details_data.acc_number,
#                         'ifsc_code': receiver_details_data.ifsc_code,
#                         'additional_info': receiver_details_data.add_info,
#                         'address': receiver_details_data.add_info,
#                         'currency': currency_dict[receiver_details_data.currency].name if receiver_details_data else None,
#                         'received_amount': converted_amount

#                     } if receiver_details_data else None,

#                 }
            
#             combined_data.append(transaction_data)

#             #Final Return
#             return json({'msg': 'Transaction data fetched Successfully', 'transaction_data': combined_data}, 200)

#     except Exception as e:
#         return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    




# @auth('userauth')
# @get('/api/v4/admin/transaction/search/')
# async def search_all_transaction(self, request: Request, query: str = ''):
#     """
#      Admin will be able to Search Transaction
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             AdminID       = user_identity.claims.get('user_id') if user_identity else None

#             searched_text = query

#             if re.fullmatch(r'\d+', searched_text):
#                 parsed_value = int(searched_text)
#             else:
#                 parsed_value = searched_text

#             #Check the user is Admin or not
#             try:
#                 admin_obj = await session.execute(select(Users).where(Users.id == AdminID))
#                 admin_obj_data = admin_obj.scalar()

#                 if not admin_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 401)
                
#             except Exception as e:
#                 return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            
#             try:
#                 currency_obj      = await session.execute(select(Currency))
#                 currency_data     = currency_obj.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
#             try:
#                 all_user_obj      = await session.execute(select(Users))
#                 all_user_obj_data = all_user_obj.scalars().all()

#                 if not all_user_obj_data:
#                     return json({'msg': 'No users available'})
                
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            
#             currency_id      = None
#             user_search_id   = None
#             user_search_list = []
#             transactions_list = []

#             if isinstance(parsed_value, str):
#                 check_word = parsed_value.split()
#                 # print(check_word)

#                 if len(check_word) >= 2:
#                     # first_name, last_name = check_word[0], check_word[1]

#                     for users in all_user_obj_data:
#                         if users.full_name == parsed_value:
#                             user_search_id  = users.id
#                             user_search_list.append(user_search_id)

#                 else:
#                     try:
#                         transaction_query = select(Transection).where(
#                             (Transection.txdtype.ilike(parsed_value))     |
#                             (Transection.txdid.ilike(parsed_value))       |
#                             (Transection.txdstatus.ilike(parsed_value))    
#                         )

#                         searched_transaction_obj = await session.execute(transaction_query)

#                         transactions_list = searched_transaction_obj.scalars().all()
                                                                                                                                                                                                                                   
#                     except Exception as e:
#                         return json({'msg': 'Transaction Search error', 'error': f'{str(e)}'}, 400)
                    
#             for currency in currency_data:
#                 if currency.name == parsed_value:
#                     currency_id  = currency.id
#                     break

#             if currency_id is not None:
#                 try:
#                     searched_transaction_obj = await session.execute(select(Transection).where(
#                         Transection.txdcurrency == currency_id
#                     ))

#                     transactions_list = searched_transaction_obj.scalars().all()

#                 except Exception as e:
#                     return json({'msg': 'Error while searching for currency', 'error': f'{str(e)}'}, 400)
                
            
#             elif user_search_list is not None:
#                 try:
#                     # transactions_list = []

#                     for user in user_search_list:
#                         searched_transaction_obj = await session.execute(select(Transection).where(
#                             Transection.user_id == user
#                         ))

#                         transactions_list = searched_transaction_obj.scalars().all()

#                         # transactions_list.append(transactions)
#                 except Exception as e:
#                     return json({'msg': 'Error while searching for users Transaction', 'error': f'{str(e)}'}, 400)
                
            
#             elif isinstance(parsed_value, int):
#                 try:
#                     transaction_query = select(Transection).where(
#                         (Transection.amount == parsed_value)      |
#                         (Transection.txdfee == parsed_value)        
#                     )

#                     searched_transaction_obj = await session.execute(transaction_query)

#                     transactions_list = searched_transaction_obj.scalars().all()

#                 except Exception as e:
#                     return json({'msg': 'Transaction amount fee Search error', 'error': f'{str(e)}'}, 400)
                
        
#             combined_data = []
#             user_dict     = {user.id: user for user in all_user_obj_data}
#             currency_dict = {currency.id: currency for currency in currency_data}
#             receiver_dict = {receiver.id: receiver for receiver in all_user_obj_data}


#             for transaction in transactions_list:
#                 user_id    = transaction.user_id
#                 user_data  = user_dict.get(user_id)
#                 user_data  = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None

#                 currency_id   = transaction.txdcurrency
#                 currency_data = currency_dict.get(currency_id)

#                 receiver_id = transaction.txdrecever
#                 receiver_data = receiver_dict.get(receiver_id)

#                 combined_data.append({
#                     'transaction': transaction,
#                     'currency': currency_data,
#                     'user': user_data,
#                     'receiver': receiver_data
#                 })

#             return json({'msg': 'Transaction data fetched successfully', 'data': combined_data}, 200)

#     except Exception as e:
#         return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    



# @auth('userauth')
# @post('/api/v4/admin/filter/transaction/')
# async def filter_all_transaction(self, request: Request, schema: FromJSON[AdminAllTransactionFilterSchema]):
#     """
#      Admin will be able to Filter Transactions
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             user_identity = request.identity
#             AdminID       = user_identity.claims.get('user_id') if user_identity else None

#             filter_data = schema.value

#             #Check the user is Admin or not
#             try:
#                 admin_obj = await session.execute(select(Users).where(Users.id == AdminID))
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

#             # print('From date',from_date_str)
#             # print('To date',to_date_str)
#             # print('Currency',currency)
#             # print('Status',status)
#             # print('User Name',user_name)
#             # print('Payment Mode',payment_mode)

#             try:
#                 query = select(Transection)
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


#             combined_data = []
#             user_dict     = {user.id: user for user in all_user_obj_data}
#             currency_dict = {currency.id: currency for currency in all_currency_data}
#             receiver_dict = {receiver.id: receiver for receiver in all_user_obj_data}

#             for transaction in transactions_list:
#                 user_id    = transaction.user_id
#                 user_data  = user_dict.get(user_id)
#                 user_data  = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None

#                 currency_id   = transaction.txdcurrency
#                 currency_data = currency_dict.get(currency_id)

#                 receiver_id = transaction.txdrecever
#                 receiver_data = receiver_dict.get(receiver_id)

#                 combined_data.append({
#                     'transaction': transaction,
#                     'currency': currency_data,
#                     'user': user_data,
#                     'receiver': receiver_data
#                 })

#             return json({'msg': 'Transaction data fetched successfully', 'data': combined_data}, 200)

#     except Exception as e:
#         return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)






    

