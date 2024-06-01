from blacksheep import get, Request, json, pretty_json
from database.db import AsyncSession, async_engine
from app.auth import decode_token
from sqlmodel import select
from Models.models import Users, Transection, Currency
from blacksheep.server.authorization import auth
from app.docs import docs
import re



#Get all the Transfer transactions by Admin
@docs(responses={
    400: 'Only admin can view the Transactions',
    400: 'Unable to get Admin detail',
    400: 'Transaction error',
    400: 'Currency not available',
    400: 'Currency error',
    404: 'User is not available',
    400: 'User not found',
    404: 'No Transaction available to show',
    200: 'Transfer Transaction data fetched successfully',
    500: 'Server Error'
})
@auth('userauth')
@get('/api/v1/transfer/transactions')
async def get_transferTransaction(self, request: Request, limit: int = 25, offset: int = 0):
    """
      Get all transfer Transactions, Only by Admin
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            AdminID          = user_identity.claims.get("user_id") if user_identity else None

            limit  = limit
            offset = offset

            #Check the user is admin or Not
            try:
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
            #Get all transaction Data
            try:
                get_all_transaction     = await session.execute(select(Transection).where(Transection.txdtype == 'Transfer').order_by(Transection.id.desc()).limit(limit).offset(offset))
                get_all_transaction_obj = get_all_transaction.scalars().all()
            except Exception as e:
                return json({'msg': 'Transaction error', 'error': f'{str(e)}'}, 400)
            
            #Get the Currency
            try:
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                if not currency_obj:
                    return json({'msg': 'Currency not available'}, 404)
                    
            except Exception as e:
                return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
            
            #Get the user data
            try:
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                if not user_obj_data:
                    return json({'msg': 'User is not available'}, 404)
                
            except Exception as e:
                return json({'msg': 'User not found'}, 400)
            
            # Prepare dictionaries for output data
            currency_dict = {currency.id: currency for currency in currency_obj}
            user_dict     = {user.id: user for user in user_obj_data}
            receiver_dict = {receiver.id: receiver for receiver in user_obj_data}

            combined_data = []
            
            for transaction in get_all_transaction_obj:
                    currency_id             = transaction.txdcurrency
                    currency_data           = currency_dict.get(currency_id)

                    user_id   = transaction.user_id
                    user_data = user_dict.get(user_id)
                    user_data = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None

                    receiver_id   = transaction.txdrecever
                    receiver_data = receiver_dict.get(receiver_id)
                    receiver_data = {'first_name': receiver_data.first_name, 'lastname': receiver_data.lastname, 'id': receiver_data.id} if receiver_data else None

                    combined_data.append({
                        'transaction': transaction,
                        'sender_currency': currency_data,
                        'user': user_data,
                        'receiver': receiver_data
                    })

            if not get_all_transaction_obj:
                return json({'msg': "No Transaction available to show"}, 404)
            
            return json({'msg': 'Transfer Transaction data fetched successfully', 'data': combined_data}, 200)
        
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    


#Search Transfer Transaction
@auth('userauth')
@get('/api/v1/search/transfer/transactions/')
async def search_transferTransaction(self, request: Request, search: str = ''):
    """
      Get all transfer Transactions, Only by Admin
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            AdminID         = user_identity.claims.get("user_id") if user_identity else None

            searched_text   = search

            if re.fullmatch(r'\d+', searched_text):
                parsed_value = int(searched_text)
            else:
                parsed_value = searched_text
            
            # Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
            if parsed_value == '':
                await get_transferTransaction(self, request)
            
            try:
                currency_obj      = await session.execute(select(Currency))
                currency_data     = currency_obj.scalars().all()
            except Exception as e:
                return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
            try:
                all_user_obj      = await session.execute(select(Users))
                all_user_obj_data = all_user_obj.scalars().all()

                if not all_user_obj_data:
                    return json({'msg': 'No users available'})
                
            except Exception as e:
                return json({'msg': 'User not found'}, 400)
            
            #initialize currency to none
            currency_id    = None
            # user_search_id = None
            # user_search_list = []

            # if isinstance(parsed_value, str):
            #     check_word = parsed_value.split()
            #     print(check_word)

            #     if len(check_word) >= 2:
            #         first_name, last_name = check_word[0], check_word[1]

            #         for users in searched_user_obj_data:
            #             if users.first_name == first_name and users.lastname == last_name:
            #                 user_search_id  = users.id
            #                 user_search_list.append(user_search_id)
            
            # if user_search_list is not None:
            #     print('User exists')
            #     print(user_search_list)


            for currency in currency_data:
                if currency.name == parsed_value:
                    currency_id  = currency.id
                    break

            if currency_id is not None:
                try:
                    searched_transaction_obj = await session.execute(select(Transection).where(
                        Transection.txdcurrency == currency_id
                    ))

                    transactions_list = searched_transaction_obj.scalars().all()

                except Exception as e:
                    return json({'msg': 'Error while searching for currency', 'error': f'{str(e)}'}, 400)

            elif type(parsed_value) == str:
                try:
                    transaction_query = select(Transection).where(
                        (Transection.txdtype.ilike(parsed_value))     |
                        (Transection.txdid.ilike(parsed_value))       |
                        (Transection.txdstatus.ilike(parsed_value))    
                    )

                    searched_transaction_obj = await session.execute(transaction_query)

                    transactions_list = searched_transaction_obj.scalars().all()
                                                                                                                                                                                                                                                                        
                except Exception as e:
                    return json({'msg': 'Transaction Search error', 'error': f'{str(e)}'}, 400)
            

            elif isinstance(parsed_value, int):
                try:
                    transaction_query = select(Transection).where(
                        (Transection.amount == parsed_value)      |
                        (Transection.txdfee == parsed_value)        
                    )

                    searched_transaction_obj = await session.execute(transaction_query)

                    transactions_list = searched_transaction_obj.scalars().all()

                except Exception as e:
                    return json({'msg': 'Transaction amount fee Search error', 'error': f'{str(e)}'}, 400)


            #Get the Currency
            try:
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                if not currency_obj:
                    return json({'msg': 'Currency not available'}, 404)
                    
            except Exception as e:
                return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
            
                
            
            combined_data = []
            user_dict     = {user.id: user for user in all_user_obj_data}
            currency_dict = {currency.id: currency for currency in currency_obj}

            for transaction in transactions_list:
                user_id    = transaction.user_id
                user_data  = user_dict.get(user_id)
                user_data  = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None

                currency_id             = transaction.txdcurrency
                currency_data           = currency_dict.get(currency_id)

                combined_data.append({
                    'transaction': transaction,
                    'user': user_data,
                    'sender_currency': currency_data
                })

            return json({'msg': 'Transfer Transaction data fetched successfully', 'data': combined_data}, 200)
        
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)