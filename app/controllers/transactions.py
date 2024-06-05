from blacksheep.server.controllers import APIController
from sqlmodel import Session, select, and_
from blacksheep import Request, json, FromJSON
from Models.models import Transection, ExternalTransection, Currency, Users, Wallet, ReceiverDetails
from database.db import async_engine, AsyncSession
from app.auth import decode_token
from blacksheep.server.responses import pretty_json
from Models.schemas import UpdateTransactionSchema
from app.controllers.controllers import get, put
from blacksheep.server.authorization import auth
from httpx import AsyncClient
import http.client
from decouple import config
from blacksheep.server.authorization import auth
from sqlalchemy import desc



currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')



class TransactionController(APIController):

    @classmethod
    def route(cls):
        return '/api/v4/transactions/'
    
    @classmethod
    def class_name(cls):
        return "Transaction"
    
    #Get all the Transactions by Admin
    @auth('userauth')
    @get()
    async def get_transaction(self, request: Request, limit: int = 25, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None
                
                limit  = limit
                offset = offset

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
                    get_all_transaction     = await session.execute(select(Transection).order_by(Transection.id.desc()).limit(limit).offset(offset))
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
                
                return json({'msg': 'Transaction data fetched successfully', 'data': combined_data}, 200)
            
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
                

                #Get the Sender currency name from currency Table
                try:
                    sender_currency_name     = await session.execute(select(Currency).where(Currency.id == transaction_data.txdcurrency))
                    sender_currency_name_obj = sender_currency_name.scalar()

                    if not sender_currency_name_obj:
                        return json({'msg': 'Did not found recipient Details'}, 404)
                                
                except Exception as e:
                    return json({'msg': 'Recipient currency error', 'error': f'{str(e)}'}, 400)
                

                #=================================
                #If Transaction status is Success
                #=================================
                if not transaction_data.is_completed:
                    if data.status == 'Success':
                        if transaction_data.txdtype == 'Deposit':

                            user_id         = transaction_data.user_id
                            currency_id     = transaction_data.txdcurrency
                            selected_wallet = transaction_data.wallet_id

                            # if not transaction_data.is_completed:
                                #Get the Sender Selected FIAT wallet according to users selected wallet
                            try:
                                sender_wallet     = await session.execute(select(Wallet).where(Wallet.id == selected_wallet))
                                sender_wallet_obj = sender_wallet.scalar()

                                if not sender_wallet:
                                    return json({"msg": "Sender donot have a selected wallet"}, status=404)
                                
                                selected_wallet_currency_name = sender_wallet_obj.currency

                            except Exception as e:
                                return json({'mag': 'Selected Wallet error','error': f'{str(e)}'}, 400)
                                
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
                                url = f"{currency_converter_api}/convert?from={currency_to_convert_name}&to={selected_wallet_currency_name}&amount={transaction_data.amount}"
                                headers = {
                                'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                                'X-RapidAPI-Host': f"{RAPID_API_HOST}"
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
                                transaction_data.txdstatus         = 'Success'
                                transaction_data.is_completed      = True
                                transaction_data.credited_amount   = converted_amount
                                transaction_data.credited_currency = currency_to_convert_name

                                session.add(transaction_data)
                                await session.commit()
                                await session.refresh(transaction_data)

                            except Exception as e:
                                return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)

                            return pretty_json({'msg': 'Deposit Transaction Updated Successfully', 'data': transaction_data, 'is_completed': True}, 200)
                            # else:
                            #     return json({'msg': 'Transaction is completed'}, 400)
                            
                        #====================================
                        #If the Transaction type is Transfer
                        #====================================
                        elif transaction_data.txdtype == 'Transfer':
                            receiver_detail        = transaction_data.rec_detail
                            recipient_id           = transaction_data.txdrecever
                            sender_id              = transaction_data.user_id
                            sender_currency        = transaction_data.txdcurrency
                            total_amount           = transaction_data.totalamount

                            recipient_payment_mode = transaction_data.rec_pay_mode

                            #Get the Sender Wallet
                            try:
                                sender_wallet_transfer     = await session.execute(select(Wallet).where(Wallet.user_id == sender_id, Wallet.currency_id == sender_currency))
                                sender_wallet_transfer_obj = sender_wallet_transfer.scalar()

                                if not sender_wallet_transfer_obj:
                                    return json({"msg": "Sender donot have a wallet"}, status=404)

                            except Exception as e:
                                return json({'mag': 'Selected Wallet error','error': f'{str(e)}'}, 400)
                           

                            if recipient_payment_mode:
                                
                                # Check Recipient payment mode is bank or Not
                                #============================================
                                if recipient_payment_mode == 'Bank':
                                    #Get the receiver details
                                    try:
                                        receiver_details      = await session.execute(select(ReceiverDetails).where(ReceiverDetails.id == receiver_detail))
                                        receiver_details_obj = receiver_details.scalar()

                                        if not receiver_details_obj:
                                            return json({'msg': 'Did not found recipient Details'}, 404)
                                        
                                    except Exception as e:
                                        return json({'msg': 'Recipient currency error', 'error': f'{str(e)}'}, 400)
                                    
                                    #Get Receiver Currency
                                    try:
                                        receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_details_obj.currency))
                                        receiver_currency_obj  = receiver_currency.scalar()

                                        if not receiver_currency_obj:
                                            return json({'msg': 'Did not found Receiver Currency'}, 404)
                                        
                                    except Exception as e:
                                        return json({'msg': 'Recipient currency error', 'error': f'{str(e)}'}, 400)
                                    
                                    if sender_wallet_transfer_obj.balance <= transaction_data.totalamount:
                                        return json({'msg': 'Sender do not have sufficient wallet balance'})

                                    if sender_wallet_transfer_obj.balance >= transaction_data.totalamount:
                                        #Convert currency using API
                                        try:
                                            url = f"{currency_converter_api}/convert?from={sender_currency_name_obj.name}&to={receiver_currency_obj.name}&amount={transaction_data.amount}"
                                            headers = {
                                            'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                                            'X-RapidAPI-Host': f"{RAPID_API_HOST}"
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
                                        
                                        #Update Receiver Received amount
                                        receiver_details_obj.amount = converted_amount
                                        session.add(receiver_details_obj)

                                        # Deduct from sender wallet
                                        try:
                                            sender_wallet_transfer_obj.balance -=  total_amount
                                            session.add(sender_wallet_transfer_obj)

                                        except Exception as e:
                                            return json({'msg': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)
                                        
                                        try:
                                            transaction_data.txdstatus         = 'Success'
                                            transaction_data.is_completed      = True
                                            transaction_data.credited_amount   = converted_amount
                                            transaction_data.credited_currency = receiver_currency_obj.name

                                            session.add(transaction_data)
                                        except Exception as e:
                                            return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)
                                        
                                        await session.commit()
                                        await session.refresh(sender_wallet_transfer_obj)
                                        await session.refresh(transaction_data)
                                        await session.refresh(receiver_details_obj)

                                        return json({'msg': 'Transfer Transaction updated successfully', 'is_completed': True}, 200)


                                #Check Recipient payment mode is Wallet or Not
                                #==============================================
                                elif recipient_payment_mode == 'Wallet':

                                    try:
                                        recipient_wallet     = await session.execute(select(Wallet).where(and_(Wallet.user_id == recipient_id, Wallet.currency_id == transaction_data.rec_currency)))
                                        recipient_wallet_obj = recipient_wallet.scalars().first()

                                        if not recipient_wallet_obj:
                                            return json({'msg': 'Recipient wallet not found'}, 404)
            
                                    except Exception as e:
                                        return json({'msg': 'Unable to locate recipient Wallet'}, 400)
                                
                                    #If Sender wallet and receiver wallet are same
                                    if sender_wallet_transfer_obj.id == recipient_wallet_obj.id:
                                        return json({'msg': 'Cannot transfer to self'}, 404)

                                    if sender_wallet_transfer_obj.balance <= transaction_data.totalamount:
                                        return json({'msg': 'Sender do not have sufficient wallet balance'})

                                    if sender_wallet_transfer_obj.balance >= transaction_data.totalamount:

                                        #Convert currency using API
                                        try:
                                            url = f"{currency_converter_api}/convert?from={sender_currency_name_obj.name}&to={recipient_wallet_obj.currency}&amount={transaction_data.amount}"
                                            headers = {
                                            'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                                            'X-RapidAPI-Host': f"{RAPID_API_HOST}"
                                        }
                                            async with AsyncClient() as client:
                                                response = await client.get(url, headers=headers)

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


                                        #Add into Receiver Wallet
                                        try:
                                            recipient_wallet_obj.balance += converted_amount
                                            session.add(recipient_wallet_obj)
                                        except Exception as e:
                                            return json({'msg': 'Unable to update recipient wallet', 'error': f'{str(e)}'}, 400)

                                        # Deduct from sender wallet
                                        try:
                                            sender_wallet_transfer_obj.balance -=  total_amount
                                            session.add(sender_wallet_transfer_obj)

                                        except Exception as e:
                                            return json({'msg': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)

                                        try:
                                            transaction_data.txdstatus         = 'Success'
                                            transaction_data.is_completed      = True
                                            transaction_data.credited_amount   = converted_amount
                                            transaction_data.credited_currency = recipient_wallet_obj.currency

                                            session.add(transaction_data)

                                        except Exception as e:
                                            return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)

                                        await session.commit()
                                        await session.refresh(recipient_wallet_obj)
                                        await session.refresh(sender_wallet_transfer_obj)
                                        await session.refresh(transaction_data)

                                        return json({'msg': 'Transfer Transaction updated successfully', 'is_completed': True}, 200)
                                    
                                    else:
                                        return json({'msg': 'Donot have sufficient balance in Wallet'}, 404)
                                
                                else:
                                    #If the Receiver Payment mode is other than Bank or wallet.
                                    # Get Receiver Details
                                    try:
                                        receiver_details      = await session.execute(select(ReceiverDetails).where(ReceiverDetails.id == receiver_detail))
                                        receiver_details_obj  = receiver_details.scalar()

                                        if not receiver_details_obj:
                                            return json({'msg': 'Did not found recipient Details'}, 404)
                                        
                                    except Exception as e:
                                        return json({'msg': 'Recipient currency error', 'error': f'{str(e)}'}, 400)
                                    
                                    #Get Receiver Currency
                                    try:
                                        receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_details_obj.currency))
                                        receiver_currency_obj  = receiver_currency.scalar()

                                        if not receiver_currency_obj:
                                            return json({'msg': 'Did not found Receiver Currency'}, 404)
                                        
                                    except Exception as e:
                                        return json({'msg': 'Recipient currency error', 'error': f'{str(e)}'}, 400)
                                    
                                    if sender_wallet_transfer_obj.balance <= transaction_data.totalamount:
                                        return json({'msg': 'Sender do not have sufficient wallet balance'})

                                    if sender_wallet_transfer_obj.balance >= transaction_data.totalamount:
                                        #Convert currency using API
                                        try:
                                            url = f"{currency_converter_api}/convert?from={sender_currency_name_obj.name}&to={receiver_currency_obj.name}&amount={transaction_data.amount}"
                                            headers = {
                                            'X-RapidAPI-Key': f"{RAPID_API_KEY}",
                                            'X-RapidAPI-Host': f"{RAPID_API_HOST}"
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
                                        
                                        #Update Receiver Received amount
                                        receiver_details_obj.amount = converted_amount
                                        session.add(receiver_details_obj)

                                        # Deduct from sender wallet
                                        try:
                                            sender_wallet_transfer_obj.balance -=  total_amount
                                            session.add(sender_wallet_transfer_obj)

                                        except Exception as e:
                                            return json({'msg': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)
                                        
                                        try:
                                            transaction_data.txdstatus         = 'Success'
                                            transaction_data.is_completed      = True
                                            transaction_data.credited_currency = receiver_currency_obj.name
                                            transaction_data.credited_amount   = converted_amount

                                            session.add(transaction_data)
                                        except Exception as e:
                                            return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)
                                        
                                        await session.commit()
                                        await session.refresh(sender_wallet_transfer_obj)
                                        await session.refresh(transaction_data)
                                        await session.refresh(receiver_details_obj)

                                        return json({'msg': 'Transfer Transaction updated successfully', 'is_completed': True}, 200)
                                    
                            else:
                                return json({'msg': 'Recipient payment mode does not exists please update New transaction'}, 404)

                        else:
                            return json({'msg': 'Working in Withdraw and Request money'})
                            
                    elif data.status == "Pending":
                        #Update the Transaction Status
                        try:
                            transaction_data.txdstatus = 'Pending'

                            session.add(transaction_data)
                            await session.commit()
                            await session.refresh(transaction_data)

                        except Exception as e:
                            return pretty_json({'msg': 'Unable to update transaction status', 'error': f'{str(e)}'}, 400)

                        return pretty_json({'msg': 'Transaction Updated Successfully', 'data': transaction_data, 'is_completed': False}, 200)

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

                        return pretty_json({'msg': 'Transaction Updated Successfully', 'data': transaction_data, 'is_completed': False}, 200)
                    
                else:
                    return json({'msg': 'Transaction is completed'}, 400)
                
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
                        transactions      = await session.execute(select(Transection).where(Transection.user_id == user_id).order_by(desc(Transection.id)))
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

                        credited_amount   = transaction.credited_amount
                        credited_currency = transaction.credited_currency

                        combined_data.append({
                            'transaction':       transaction,
                            'currency':          currency_data,
                            'user':              user_data,
                            'receiver':          receiver_data,
                            'credited_amount':   credited_amount if credited_amount else None,
                            'credited_currency': credited_currency if credited_currency else None
                        })

                except Exception as e:
                    return json({'msg': f'Unable to get the Transactions {str(e)}'}, 400)
                

                return json({'msg': 'Transaction data fetched successfully', 'all_transactions': combined_data})
                
        except Exception as e:
            return json({'error': f'{str(e)}'})
        



#Not working properly

# class IDWiseTransactionController(APIController):

#     @classmethod
#     def route(cls):
#         return '/api/v4/transaction/{transaction_id}/{currency_id}'
    
#     @classmethod
#     def class_name(cls) -> str:
#         return "Id Wise Transaction"
    
#     @get()
#     async def get_idwisetransaction(self, request: Request, transaction_id: int, currency_id: int):

#         try:
#             async with AsyncSession(async_engine) as session:
#                 transactionID = transaction_id
#                 currencyId    = currency_id

#                 try:
#                     header_value = request.get_first_header(b"Authorization")
                    
#                     if not header_value:
#                         return json({'error': 'Authentication Failed Please provide auth token'}, 400)
                    
#                     header_value_str = header_value.decode("utf-8")

#                     parts = header_value_str.split()

#                     if len(parts) == 2 and parts[0] == "Bearer":
#                         token = parts[1]
#                         user_data = decode_token(token)

#                         if user_data == 'Token has expired':
#                             return json({'msg': 'Token has expired'})
#                         elif user_data == 'Invalid token':
#                             return json({'msg': 'Invalid token'})
#                         else:
#                             user_data = user_data
                            
#                         user_id = user_data["user_id"]
#                 except Exception as e:
#                     return json({'msg': 'Authentication Failed'}, 400)
                
#                 try:
#                     #Get The transaction by ID
#                     transaction     = await session.execute(select(Transection).where(Transection.id == transactionID))
#                     transaction_obj = transaction.scalars().all()

#                     if not transaction_obj:
#                         return pretty_json({'msg': 'requested transaction not available'}, 404)
                    
#                 except Exception as e:
#                     return pretty_json({'error': 'Unable to get the transaction'}, 400)
                
#                 # Get the Currency
#                 try:
#                     get_currency = await session.execute(select(Currency).where(Currency.id == currencyId))
#                     currency_obj = get_currency.scalars()
#                     # print(currency_obj)
                    
#                 except Exception as e:
#                     return pretty_json({'msg': 'Currency error', "error": f'{str(e)}'})
                
#                 currency_dict = {currency_obj.id: currency for currency in currency_obj}

#                 for transaction in transaction_obj:
#                     currency_id   = transaction.txdcurrency
#                     currency_data = currency_dict.get(currency_id)
#                     transaction.txdcurrency = currency_data

#                 return pretty_json({'msg': 'Data fetched successfully', 'transaction': transaction_obj})

#         except Exception as e:
#             return pretty_json({'error': f'Server error {str(e)}'}, 500)
        
