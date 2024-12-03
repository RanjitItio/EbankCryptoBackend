# from blacksheep import Request, post, json, pretty_json, FromJSON
# from Models.Admin.User.schemas import EachUserTransactionSchema, TransactionSearchSchema, UserTransactionFilterSchema
# from blacksheep.server.authorization import auth
# from database.db import AsyncSession, async_engine
# from sqlmodel import select, or_, and_
# from Models.models import Users, Transection, Currency
# from app.docs import docs
# from datetime import datetime






# #Get all the Transaction related to a user
# @docs(responses={200: 'List all the Transactions related to a user'})
# @auth('userauth')
# @post('/api/v2/admin/user/transactions/')
# async def get_usertransaction(self, request: Request, schema: EachUserTransactionSchema):
#     """
#       List all the transactions related to a user, Only for admin
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
            
#             user_identity   = request.identity
#             AdminID         = user_identity.claims.get("user_id") if user_identity else None
            
#             requested_user_id = schema.user_id
#             limit             = schema.limit
#             offset            = schema.offset

#             #Check the user is admin or Not
#             try:
#                 user_obj      = await session.execute(select(Users).where(Users.id == AdminID))
#                 user_obj_data = user_obj.scalar()

#                 if not user_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 400)
                
#             except Exception as e:
#                 return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
#             #Get the user
#             try:
#                 user_obj      = await session.execute(select(Users))
#                 user_obj_data = user_obj.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            
            
#             try:
#                 #Get all the currency
#                 try:
#                     currency     = await session.execute(select(Currency))
#                     currency_obj = currency.scalars().all()
#                 except Exception as e:
#                     return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                
#                 #Get all the transactions related to the user in sender
#                 try:
#                     transactions = await session.execute(
#                             select(Transection)
#                             .where(Transection.user_id == requested_user_id).order_by(Transection.id.desc()).limit(limit).offset(offset)
#                         )
#                     transactions_list = transactions.scalars().all()

#                     if not transactions_list:
#                         return json({'msg': 'No Transaction Available'}, 404)
                    
#                 except Exception as e:
#                     return pretty_json({'msg': 'Transaction error', 'error': f'{str(e)}'}, 400)
                
        
#                 currency_dict = {currency.id: currency for currency in currency_obj}
#                 user_dict     = {user.id: user for user in user_obj_data}
#                 combined_data = []

#                 for transaction in transactions_list:
#                     userid      = transaction.user_id
#                     user_data   = user_dict.get(userid)

#                     user_data = {
#                         'first_name': user_data.first_name,
#                         'last_name': user_data.lastname,
#                         'user_id': user_data.id
#                     }

#                     currency_id   = transaction.txdcurrency
#                     currency_data = currency_dict.get(currency_id)

#                     receiverid    = transaction.txdrecever
#                     receiver_data = user_dict.get(receiverid)

#                     receiver_data = {
#                         'first_name': receiver_data.first_name if receiver_data else None , 
#                         'last_name': receiver_data.lastname if receiver_data else None ,
#                         'receiver_id': receiver_data.id if receiver_data else None 
#                     }

#                     combined_data.append({
#                     'transaction': transaction,
#                     'user': user_data,
#                     'currency': currency_data,
#                     'receiver': receiver_data if receiver_data else None
#                     })
                
#             except Exception as e:
#                 return json({'msg': f'Unable to get the Transactions', 'error': f'{str(e)}'}, 400)
            
#             return json({'msg': 'User transactions data fetched successfully', 'user_transactions': combined_data}, 200)
        

#     except Exception as e:
#         return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    





# #Seacrh for Transactions
# @docs(responses={200: 'If the search value is amount and fee, then send as float value, and other values are in string..'})
# @auth('userauth')
# @post('/api/v2/admin/transaction/search/')
# async def get_searchedeusers(self, request: Request, schema: TransactionSearchSchema):
#     """
#      Search Transactions related to a user
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             searched_text = schema.searched_text

#             user_identity   = request.identity
#             AdminID          = user_identity.claims.get("user_id") if user_identity else None

#             transactions_list = []
#             users_list = []
#             combined_data = []

#             #Check the user is admin or Not
#             try:
#                 user_obj      = await session.execute(select(Users).where(Users.id == AdminID))
#                 user_obj_data = user_obj.scalar()

#                 if not user_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 400)
                
#             except Exception as e:
#                 return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
#             try:
#                 currency_obj      = await session.execute(select(Currency))
#                 currency_data     = currency_obj.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            

#             #initialize currency to none
#             currency_id = None

#             for currency in currency_data:
#                 if currency.name == schema.searched_text:
#                     currency_id = currency.id
#                     break


#             if currency_id is not None:
#                 try:
#                     searched_transaction_obj = await session.execute(select(Transection).where(
#                         and_(Transection.txdcurrency == currency_id, Transection.user_id == schema.userid)
#                     ))

#                     transactions_list = searched_transaction_obj.scalars().all()

#                 except Exception as e:
#                     return json({'msg': 'Error while searching for currency', 'error': f'{str(e)}'}, 400)


#             elif type(schema.searched_text) == str:
#                 try:
#                     transaction_query = select(Transection).where(
#                         (Transection.txdtype.ilike(searched_text))     |
#                         (Transection.txdid.ilike(searched_text))       |
#                         (Transection.txdstatus.ilike(searched_text))    
#                     )

#                     if schema.userid:
#                         transaction_query = transaction_query.where(Transection.user_id == schema.userid)

#                     searched_transaction_obj = await session.execute(transaction_query)

#                     transactions_list = searched_transaction_obj.scalars().all()
                                                                                                                                                                                                                                                                        
#                 except Exception as e:
#                     return json({'msg': 'Transaction Search error', 'error': f'{str(e)}'}, 400)
            

#             elif type(schema.searched_text) == float:
#                 try:
#                     transaction_query = select(Transection).where(
#                         (Transection.amount == searched_text)      |
#                         (Transection.txdfee == searched_text)        
#                     )

#                     if schema.userid:
#                         transaction_query = transaction_query.where(Transection.user_id == schema.userid)

#                     searched_transaction_obj = await session.execute(transaction_query)

#                     transactions_list = searched_transaction_obj.scalars().all()

#                 except Exception as e:
#                     return json({'msg': 'Transaction amount fee Search error', 'error': f'{str(e)}'}, 400)
                
                
#             try:
#                 all_user_obj  = await session.execute(select(Users))
#                 all_user_obj_data = all_user_obj.scalars().all()

#                 if not all_user_obj_data:
#                     return json({'msg': 'No users available'})
                
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            
            
#             currency_dict = {currency.id: currency for currency in currency_data}
#             user_dict     = {user.id: user for user in all_user_obj_data}
            
            
#             for transaction in transactions_list:
#                 userid      = transaction.user_id
#                 user_info   = user_dict.get(userid)
                
#                 user_info = {
#                     'first_name': user_info.first_name,
#                     'last_name': user_info.lastname,
#                     'user_id': user_info.id
#                 }

#                 currency_id   = transaction.txdcurrency
#                 currency_info = currency_dict.get(currency_id)

#                 receiverid    = transaction.txdrecever
#                 receiver_data = user_dict.get(receiverid)

#                 receiver_data = {
#                     'first_name': receiver_data.first_name if receiver_data else None , 
#                     'last_name': receiver_data.lastname if receiver_data else None ,
#                     'receiver_id': receiver_data.id if receiver_data else None 
#                 }

#                 combined_data.append({
#                 'transaction': transaction,
#                 'user': user_info,
#                 'currency': currency_info,
#                 'receiver': receiver_data if receiver_data else None
#                 })

                
#             return json({'msg': 'Transaction data fetched successfully', 'user_transaction': combined_data})

#     except Exception as e:
#         return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


# #Filter Transaction
# @docs(description='User ID Mandatory')
# @auth('userauth')
# @post('/api/v2/admin/transaction/filter/')
# async def filter_transaction(self, request: Request, schema: FromJSON[UserTransactionFilterSchema]):
#     """
#       Filter Transaction of users
#     """
#     try:
#         async with AsyncSession(async_engine) as session:
#             filter_data = schema.value
#             combined_data = []

#             user_identity   = request.identity
#             AdminID          = user_identity.claims.get("user_id") if user_identity else None

#             #Check the user is admin or Not
#             try:
#                 user_obj      = await session.execute(select(Users).where(Users.id == AdminID))
#                 user_obj_data = user_obj.scalar()

#                 if not user_obj_data.is_admin:
#                     return json({'msg': 'Only admin can view the Transactions'}, 400)
                
#             except Exception as e:
#                 return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            

#             #All the values of the Schema
#             userId        = filter_data.user_id
#             from_date_str = filter_data.from_date
#             to_date_str   = filter_data.to_date
#             currency      = filter_data.currency
#             status        = filter_data.status
#             type          = filter_data.type


#             try:
#                 query = select(Transection).where(Transection.user_id == userId)
#             except Exception as e:
#                 return json({'msg': 'Transaction fetch error', 'error': f'{str(e)}'}, 400)
            
#             if from_date_str:
#                 from_datetime = datetime.strptime(from_date_str, '%Y-%m-%d')
#                 from_date    = from_datetime.date()

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

#             if type is not None:
#                 query = query.where(Transection.txdtype == type)

#             result            = await session.execute(query)
#             transactions_list = result.scalars().all()


#             try:
#                 all_user_obj      = await session.execute(select(Users))
#                 all_user_obj_data = all_user_obj.scalars().all()

#                 if not all_user_obj_data:
#                     return json({'msg': 'No users available'})
                
#             except Exception as e:
#                 return json({'msg': 'User not found'}, 400)
            
#             try:
#                 currency_obj      = await session.execute(select(Currency))
#                 currency_data     = currency_obj.scalars().all()
#             except Exception as e:
#                 return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            

#             currency_dict = {currency.id: currency for currency in currency_data}
#             user_dict     = {user.id: user for user in all_user_obj_data}


#             for transaction in transactions_list:
#                 userid      = transaction.user_id
#                 user_info   = user_dict.get(userid)
                
#                 user_info = {
#                     'first_name': user_info.first_name,
#                     'last_name': user_info.lastname,
#                     'user_id': user_info.id
#                 }

#                 currency_id   = transaction.txdcurrency
#                 currency_info = currency_dict.get(currency_id)

#                 receiverid    = transaction.txdrecever
#                 receiver_data = user_dict.get(receiverid)

#                 receiver_data = {
#                     'first_name': receiver_data.first_name if receiver_data else None , 
#                     'last_name': receiver_data.lastname if receiver_data else None ,
#                     'receiver_id': receiver_data.id if receiver_data else None 
#                 }

#                 combined_data.append({
#                 'transaction': transaction,
#                 'user': user_info,
#                 'currency': currency_info,
#                 'receiver': receiver_data if receiver_data else None
#                 })


#             return json({'msg': 'Transaction data fetched Successfully', 'transaction': combined_data}, 200)
        
#     except Exception as e:
#         return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
    


        
