from blacksheep.server.controllers import get, post, put, delete, APIController
from sqlmodel import Session, select
from blacksheep import Request, json
from Models.models import Transection, ExternalTransection, Currency
from database.db import async_engine, AsyncSession
from app.auth import decode_token






class TransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/transactions/'
    
    @classmethod
    def class_name(cls):
        return "Transaction"
    
    @get()
    async def get_transaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    get_all_transaction     = await session.execute(select(Transection))
                    get_all_transaction_obj = get_all_transaction.scalars().all()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)
                
                if not get_all_transaction_obj:
                    return json({'msg': "No user available to show"}, 404)
                
                return json({'msg': 'Transaction data fetched successfully', 'data': get_all_transaction_obj})
            
        except Exception as e:
            return json({'error': f'{str(e)}'}, 400)
        


class SpecificUserTransaction(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/users/transactions/'
    
    @classmethod
    def class_name(cls):
        return "User wise Transaction"
    
    @get()
    async def get_userTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    header_value = request.get_first_header(b"Authorization")
                    
                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
                    header_value_str = header_value.decode("utf-8")

                    parts = header_value_str.split()

                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'})
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'})
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]
                except Exception as e:
                    return json({'msg': 'Authentication Failed'})
                
                try:
                    try:
                        currency = await session.execute(select(Currency))
                        currency_obj = currency.scalars().all()
                    except Exception as e:
                        return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                    
                    transactions = await session.execute(select(Transection).join(Currency).where(Transection.user_id == user_id))
                    transactions_list = transactions.scalars().all()

                    currency_dict = {currency.id: currency for currency in currency_obj}

                    for transaction in transactions_list:
                        currency_id   = transaction.txdcurrency
                        currency_data = currency_dict.get(currency_id)
                        transaction.txdcurrency = currency_data
                    
                except Exception as e:
                    return json({'msg': f'Unable to get the Transactions {str(e)}'}, 400)

                # try:
                #     external_transactions = await session.execute(select(ExternalTransection).where(ExternalTransection.user_id == user_id))
                #     external_transactions_list = external_transactions.scalars().all()
                # except Exception as e:
                #     return json({'msg': 'Unable to get the Transactions'}, 400)
                
                return json({'msg': 'Transaction data fetched successfully', 'all_transactions': transactions_list})
                
        except Exception as e:
            return json({'error': f'{str(e)}'})
        