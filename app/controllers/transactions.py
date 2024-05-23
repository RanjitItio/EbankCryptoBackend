from blacksheep.server.controllers import APIController
from sqlmodel import Session, select, and_
from blacksheep import Request, json, FromJSON
from Models.models import Transection, ExternalTransection, Currency, Users, Wallet
from database.db import async_engine, AsyncSession
from app.auth import decode_token
from blacksheep.server.responses import pretty_json
from Models.schemas import UpdateTransactionSchema
from app.controllers.controllers import get, put
from blacksheep.server.authorization import auth
from httpx import AsyncClient
import http.client





class TransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/transactions/'
    
    @classmethod
    def class_name(cls):
        return "Transaction"
    
    #Get all the Transactions
    @get()
    async def get_transaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:

                #Get the token from header
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
                    header_value_str = header_value.decode("utf-8")
                    parts = header_value_str.split()

                    #Decode the token
                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]

                except Exception as e:
                   return json({'msg': 'Authentication Failed'}, 400)
                

                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == user_id))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can view the Transactions'}, 400)
                    
                except Exception as e:
                    return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                
                #Get all transaction Data
                try:
                    get_all_transaction     = await session.execute(select(Transection))
                    get_all_transaction_obj = get_all_transaction.scalars().all()

                    if not get_all_transaction_obj:
                        return json({'msg': 'Transaction is not availabel'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Transaction error', 'error': f'{str(e)}'}, 400)
                
                try:
                    currency     = await session.execute(select(Currency))
                    currency_obj = currency.scalars().all()

                    if not currency_obj:
                        return json({'msg': 'Requested Currency not found'}, 404)
                    
                except Exception as e:
                    return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)

                try:
                    user_obj      = await session.execute(select(Users))
                    user_obj_data = user_obj.scalars().all()

                    if not user_obj_data:
                        return json({'msg': 'User not available'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'User not found'}, 400)
                
                currency_dict = {currency.id: currency for currency in currency_obj}
                user_dict     = {user.id: user for user in user_obj_data}
                receiver_dict = {receiver.id: receiver for receiver in user_obj_data}
                combined_data = []
                
                for transaction in get_all_transaction_obj:
                        currency_id             = transaction.txdcurrency
                        currency_data           = currency_dict.get(currency_id)
                        
                        user_id   = transaction.user_id
                        user_data = user_dict.get(user_id)

                        receiver_id = transaction.txdrecever
                        receiver_data = receiver_dict.get(receiver_id)

                        combined_data.append({
                            'transaction': transaction,
                            'currency': currency_data,
                            'user': user_data,
                            'receiver': receiver_data
                        })

                if not get_all_transaction_obj:
                    return json({'msg': "No transactions available to show"}, 404)
                
                return json({'msg': 'Transaction data fetched successfully', 'data': combined_data})
            
        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 400)
        
    

    #Update Transaction by Admin
    @auth('userauth')
    @put()
    async def update_transactio(self, request: Request, input: FromJSON[UpdateTransactionSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                data = input.value

                user_identity = request.identity
                AdminID       = user_identity.claims.get("user_id") if user_identity else None

                #Check the user is admin or Not
                try:
                    user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                    user_obj_data = user_obj.scalar()

                    if not user_obj_data.is_admin:
                        return json({'msg': 'Only admin can update the Transaction status'}, 400)
                    
                except Exception as e:
                    return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
                

                #Get the transaction by ID
                try:
                    transaction_obj = await session.execute(select(Transection).where(Transection.id == data.transaction_id))
                    transaction_data = transaction_obj.scalar()

                    if not transaction_data:
                        return pretty_json({'msg': 'Requested transaction not available'}, 404)
                
                except Exception as e:
                    return json({'msg': 'Unable to locate the transaction', 'error': f'{str(e)}'}, 400)


                #If Transaction status is Success
                if data.status == 'Success':
                    if transaction_data.txdtype == 'Deposit':
                        user_id         = transaction_data.user_id
                        currency_id     = transaction_data.txdcurrency
                        selected_wallet = transaction_data.wallet_id

                        if not transaction_data.is_completed:
                            #Get the Sender Selected FIAT wallet
                            try:
                                sender_wallet = await session.execute(select(Wallet).where(Wallet.id == selected_wallet))
                                sender_wallet_obj = sender_wallet.scalar()

                                if not sender_wallet:
                                    return json({"msg": "Sender donot have a selected wallet"}, status=404)
                                
                                selected_wallet_currency_name = sender_wallet_obj.currency

                            except Exception as e:
                                return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)
                            
                            #Get the currency name
                            try:
                                currency_to_convert     = await session.execute(select(Currency).where(Currency.id == currency_id))
                                currency_to_convert_obj = currency_to_convert.scalar()

                                if not currency_to_convert_obj:
                                    return json({"msg": "Currency Not found"}, status=404)
                                
                                currency_to_convert_name = currency_to_convert_obj.name

                            except Exception as e:
                                return json({'mag': 'Currency error','error': f'{str(e)}'}, 400)
                            
                            #Call API
                            try:
                                url = f"https://currency-conversion-and-exchange-rates.p.rapidapi.com/convert?from={currency_to_convert_name}&to={selected_wallet_currency_name}&amount={transaction_data.amount}"
                                headers = {
                                'X-RapidAPI-Key': "d68ba047cdmshdb9424e30ff6741p18a7eejsn41ca175d188d",
                                'X-RapidAPI-Host': "currency-conversion-and-exchange-rates.p.rapidapi.com"
                            }
                                
                                async with AsyncClient() as client:
                                    response = await client.get(url, headers=headers)
                                    # print('APi Response', response)

                                    if response.status_code == 200:
                                        api_data = response.json()
                                        # print('api data', api_data)

                                    else:
                                        return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                                    
                            except Exception as e:
                                return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                            converted_amount = api_data['result'] if 'result' in api_data else None

                            if not converted_amount:
                                return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)


                            #Update user wallet
                            try:
                                sender_wallet_obj.balance += converted_amount

                                session.add(sender_wallet_obj)
                                await session.commit()
                                await session.refresh(sender_wallet_obj)
                            except Exception as e:
                                return json({'msg': 'Unable to update user wallet', 'error': f'{str(e)}'}, 400)
                            
                            #Update the transaction status
                            try:
                                transaction_data.txdstatus    = 'Success'
                                transaction_data.is_completed = True

                                session.add(transaction_data)
                                await session.commit()
                                await session.refresh(transaction_data)

                            except Exception as e:
                                return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)

                            return pretty_json({'msg': 'Transaction Updated Successfully', 'data': transaction_data}, 200)
                        
                        else:
                            return json({'msg': 'Transaction is completed'}, 400)

                    #If the Transaction type is Transfer
                    elif transaction_data.txdtype == 'Transfer':
                        user_id      = transaction_data.user_id
                        currency_id  = transaction_data.txdcurrency
                        recipient_id = transaction_data.txdrecever
                        sent_amount  = transaction_data.amount
                        total_amount = transaction_data.totalamount

                        if not transaction_data.is_completed:

                            #Get User Wallet
                            try:
                                user_wallet     = await session.execute(select(Wallet).where(and_(Wallet.user_id == user_id, Wallet.currency_id == currency_id)))
                                user_wallet_obj = user_wallet.scalars().first()

                                if not user_wallet_obj:
                                    return json({"msg": "Sender Wallet not found"}, status=404)
                                
                            except Exception as e:
                                return json({'msg': 'Unable to locate user Wallet'}, 400)
                            
                            #Get recipient wallet
                            try:
                                recipient_wallet    = await session.execute(select(Wallet).where(and_(Wallet.user_id == recipient_id, Wallet.currency_id == currency_id)))
                                recipient_wallet_obj = recipient_wallet.scalars().first()

                                if not recipient_wallet_obj:
                                    return json({'msg': 'Recipient wallet not found'}, 404)
        
                            except Exception as e:
                                return json({'msg': 'Unable to locate recipient Wallet'}, 400)
                            
                            if user_id == recipient_id:
                                return json({'msg': 'Cannot transfer to self'}, 404)
                            

                            # Before Deducting from Sender wallet check does the user has sufficient wallet
                            if user_wallet_obj.balance <= transaction_data.totalamount:
                                return json({'msg': 'Sender do not have sufficient wallet balance'})
                            

                            if user_wallet_obj.balance >= transaction_data.totalamount:
                                #Deposit in Recipient Wallet
                                try:
                                    recipient_wallet_obj.balance += sent_amount
                                    
                                    session.add(recipient_wallet_obj)

                                except Exception as e:
                                    return json({'msg': 'Unable to update recipient wallet', 'error': f'{str(e)}'}, 400)
                                
                                #Deduct from sender wallet
                                try:
                                    user_wallet_obj.balance -=  total_amount

                                    session.add(user_wallet_obj)
                                except Exception as e:
                                    return json({'msg': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)
                                
                                
                                #Update the Transaction Status
                                try:
                                    transaction_data.txdstatus    = 'Success'
                                    transaction_data.is_completed = True

                                    session.add(transaction_data)

                                except Exception as e:
                                    return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)
                                
                                await session.commit()
                                await session.refresh(recipient_wallet_obj)
                                await session.refresh(user_wallet_obj)
                                await session.refresh(transaction_data)

                                return pretty_json({'msg': 'Transaction Updated Successfully', 'data': transaction_data}, 200)
                            
                        else:
                            return json({'msg': 'Transaction is completed'}, 400)
                        
                elif data.status == "Pending":
                    return pretty_json({'msg': 'Updated successfully'}, 200)
                

                #If the transaction status is cancelled
                else:
                    #Update the Transaction Status
                    try:
                        transaction_data.txdstatus = 'Cancelled'

                        session.add(transaction_data)
                        await session.commit()
                        await session.refresh(transaction_data)
                    except Exception as e:
                        return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)

                    return pretty_json({'msg': 'Transaction Updated Successfully', 'data': transaction_data}, 200)

                # return pretty_json({'msg': 'success', 'data': data})
        except Exception as e:
            return pretty_json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)

        


#Get all transaction of user in User dashboard section
class SpecificUserTransaction(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/users/transactions/'
    
    @classmethod
    def class_name(cls):
        return "User wise Transaction"
    
    @auth('userauth')
    @get()
    async def get_userTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get("user_id") if user_identity else None

                try:
                    try:
                        currency     = await session.execute(select(Currency))
                        currency_obj = currency.scalars().all()
                    except Exception as e:
                        return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                    
                    try:
                        transactions      = await session.execute(select(Transection).where(Transection.user_id == user_id))
                        transactions_list = transactions.scalars().all()
                    except Exception as e:
                        return pretty_json({'msg': f'Transaction error {str(e)}'}, 400)
                    
                    try:
                        all_user_obj      = await session.execute(select(Users).where(Users.id == user_id))
                        all_user_obj_data = all_user_obj.scalars().all()
                    except Exception as e:
                        return json({'msg': 'User not found'}, 400)
                    
                    # try:
                    #     all_receiver_obj      = await session.execute(select(Users).where(Users.id == user_id))
                    #     all_receiver_obj_data = all_receiver_obj.scalars().all()
                    # except Exception as e:
                    #     return json({'msg': 'User not found'}, 400)

                    currency_dict = {currency.id: currency for currency in currency_obj}
                    user_dict     = {user.id: user         for user     in all_user_obj_data}
                    receiver_dict = {receiver.id: receiver for receiver in all_user_obj_data}
                    combined_data = []

                    for transaction in transactions_list:
                        currency_id   = transaction.txdcurrency
                        currency_data = currency_dict.get(currency_id)

                        receiverID    = transaction.txdrecever
                        receiver_data = receiver_dict.get(receiverID)
                        receiver_data = {'first_name': receiver_data.first_name, 'lastname': receiver_data.lastname, 'id': receiver_data.id} if receiver_data else None

                        userID    = transaction.user_id
                        user_data = user_dict.get(userID)
                        user_data = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None
                       
                        combined_data.append({
                            'transaction': transaction,
                            'currency': currency_data,
                            'user': user_data,
                            'receiver': receiver_data
                        })
                    
                except Exception as e:
                    return json({'msg': f'Unable to get the Transactions {str(e)}'}, 400)

                
                return json({'msg': 'Transaction data fetched successfully', 'all_transactions': combined_data})
                
        except Exception as e:
            return json({'error': f'{str(e)}'})
        



#Not working properly
class IDWiseTransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/transaction/{transaction_id}/{currency_id}'
    
    @classmethod
    def class_name(cls) -> str:
        return "Id Wise Transaction"
    
    @get()
    async def get_idwisetransaction(self, request: Request, transaction_id: int, currency_id: int):

        try:
            async with AsyncSession(async_engine) as session:
                transactionID = transaction_id
                currencyId    = currency_id

                try:
                    header_value = request.get_first_header(b"Authorization")
                    
                    if not header_value:
                        return json({'error': 'Authentication Failed Please provide auth token'}, 400)
                    
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
                    return json({'msg': 'Authentication Failed'}, 400)
                
                try:
                    #Get The transaction by ID
                    transaction     = await session.execute(select(Transection).where(Transection.id == transactionID))
                    transaction_obj = transaction.scalars().all()

                    if not transaction_obj:
                        return pretty_json({'msg': 'requested transaction not available'}, 404)
                    
                except Exception as e:
                    return pretty_json({'error': 'Unable to get the transaction'}, 400)
                
                # Get the Currency
                try:
                    get_currency = await session.execute(select(Currency).where(Currency.id == currencyId))
                    currency_obj = get_currency.scalars()
                    # print(currency_obj)
                    
                except Exception as e:
                    return pretty_json({'msg': 'Currency error', "error": f'{str(e)}'})
                
                currency_dict = {currency_obj.id: currency for currency in currency_obj}

                for transaction in transaction_obj:
                    currency_id   = transaction.txdcurrency
                    currency_data = currency_dict.get(currency_id)
                    transaction.txdcurrency = currency_data

                return pretty_json({'msg': 'Data fetched successfully', 'transaction': transaction_obj})

        except Exception as e:
            return pretty_json({'error': f'Server error {str(e)}'}, 500)
        
