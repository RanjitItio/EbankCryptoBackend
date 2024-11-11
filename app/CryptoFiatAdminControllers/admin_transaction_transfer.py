from blacksheep import Request, json, pretty_json, FromJSON
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, put, post
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from sqlalchemy.orm import aliased
from Models.models import Users, Currency, ReceiverDetails, Wallet
from Models.models4 import TransferTransaction
from Models.schemas import UpdateTransactionSchema
from Models.Admin.Transfer.schemas import AdminFilterTransferTransaction
from httpx import AsyncClient
from decouple import config
from app.dateFormat import get_date_range
from datetime import datetime, timedelta




currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')


## View all transfer transactions by Admin
class AllTransferTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'All Transafer Transactions'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/admin/transfer/transactions/'
    
    ### Get all Transfer Transactions
    @auth('userauth')
    @get()
    async def get_transfer_transaction(self, request: Request, limit: int = 15, offset: int = 0):
        """
        Get all transfer Transactions
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity   = request.identity
                AdminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                #Get all transaction Data
                get_all_transaction = await session.execute(select(TransferTransaction).order_by(
                        desc(TransferTransaction.id)
                    ).limit(
                        limit
                    ).offset(
                        offset
                    ))
                get_all_transaction_obj = get_all_transaction.scalars().all()
                
                if not get_all_transaction_obj:
                    return json({'message': 'No transaction found'}, 404)
                
                #Get the Currency
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                if not currency_obj:
                    return json({'msg': 'Currency not available'}, 404)
                
                #Get the user data
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                if not user_obj_data:
                    return json({'msg': 'User is not available'}, 404)
                
                # Count total rows in the table
                count_stmt          = select(func.count(TransferTransaction.id))
                total_trsnsfer_obj  = await session.execute(count_stmt)
                total_transfer_rows = total_trsnsfer_obj.scalar()

                total_transfer_row_count = total_transfer_rows / limit


                # Prepare dictionaries for output data
                currency_dict = {currency.id: currency for currency in currency_obj}
                user_dict     = {user.id: user for user in user_obj_data}
                receiver_dict = {receiver.id: receiver for receiver in user_obj_data}

                combined_data = []
                
                for transaction in get_all_transaction_obj:
                        currency_id             = transaction.currency
                        currency_data           = currency_dict.get(currency_id)

                        user_id   = transaction.user_id
                        user_data = user_dict.get(user_id)
                        user_data = {
                            'first_name': user_data.first_name, 
                            'lastname': user_data.lastname, 
                            'email': user_data.email,
                            'id': user_data.id
                            } if user_data else None

                        receiver_id   = transaction.receiver
                        receiver_data = receiver_dict.get(receiver_id)
                        receiver_data = {
                            'first_name': receiver_data.first_name, 
                            'lastname': receiver_data.lastname, 
                            'id': receiver_data.id
                            } if receiver_data else None

                        combined_data.append({
                            'transaction': transaction,
                            'sender_currency': currency_data,
                            'user': user_data,
                            'receiver': receiver_data
                        })
                
                return json({
                        'msg': 'Transfer Transaction data fetched successfully', 
                        'transfer_transactions': combined_data,
                        'success': True,
                        'total_row_count': total_transfer_row_count
                    }, 
                    200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        


## Transfer Transaction Detail by Admin
class TransferTransactionDetailsController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Transfer Transaction Details'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/admin/transfer/transaction/details/{transaction_id}/'
    

    @auth('userauth')
    @get()
    async def get_transfer_transactions(self, request: Request, transaction_id: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id') if user_identity else None

                # Authenticate Admin
                admin_obj = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'message': 'Only admin can view the Transactions'}, 401)
                # Admin Authentication ends
                
                # Get the Transaction
                transaction_id_obj     = await session.execute(select(TransferTransaction).where(
                    TransferTransaction.id == transaction_id
                    ))
                transaction_id_details = transaction_id_obj.scalar()

                if not transaction_id_details:
                    return json({'message': 'Transaction does not exist'}, 404)
                
                # Get all the users
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                if not user_obj_data:
                    return json({'message': 'User is not available'}, 404)
                
                # Get all available currencies
                currency_obj      = await session.execute(select(Currency))
                currency_obj_data = currency_obj.scalars().all()
                
                if not currency_obj_data:
                    return json({'message': 'Currency is not available'}, 404)
                
                # Get ReceiverDetails
                receiver_details_obj      = await session.execute(select(ReceiverDetails))
                receiver_details_obj_data = receiver_details_obj.scalars().all()

                if not receiver_details_obj_data:
                    pass
                
                # Store particular id details inside a dict
                receiver_dict         = {receiver.id: receiver for receiver in user_obj_data}
                sender_dict           = {sender.id: sender for sender in user_obj_data}
                currency_dict         = {currency.id: currency for currency in currency_obj_data}
                receiver_details_dict = {receiver_details.id: receiver_details for receiver_details in receiver_details_obj_data}

                combined_data = []

                # Get receiver id from transfer transaction
                receiver_id   = transaction_id_details.receiver
                receiver_data = receiver_dict.get(receiver_id, None)

                # Get sender ID from transfer transaction
                sender_id   = transaction_id_details.user_id
                sender_data = sender_dict.get(sender_id)

                # Get Currecny id from transfer transaction
                currency_id   = transaction_id_details.currency
                currency_data = currency_dict.get(currency_id, None)

                # Get receiver details from transfer transaction
                receiver_details_id = transaction_id_details.receiver_detail
                receiver_details_data = receiver_details_dict.get(receiver_details_id, None)

                if receiver_details_data:
                    sender_currency      = currency_data.name
                    receiver_currency_id = receiver_details_data.currency

                
                    receiver_currency = await session.execute(select(Currency).where(
                        Currency.id == receiver_currency_id
                        ))
                    receiver_currency_data = receiver_currency.scalar()

                    sender_amount          = transaction_id_details.amount

                    if not receiver_currency_data:
                        return json({'message': 'Receiver currency not found'}, 404)
                
                    receiver_currency_name = receiver_currency_data.name

                    try:
                        url = f"{currency_converter_api}/convert?from={sender_currency}&to={receiver_currency_name}&amount={sender_amount}"
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
                                return json({'message': 'Error calling external API', 'error': response.text}, 400)
                            
                    except Exception as e:
                        return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                    converted_amount = api_data['result'] if 'result' in api_data else None

                    if not converted_amount:
                        return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
            
                # If Paid to Receiver Wallet
                elif transaction_id_details.receiver:
                    sender_currency      = currency_data.name
                    receiver_currency_id = transaction_id_details.receiver_currency
                    sender_amount        = transaction_id_details.amount

                    try:
                        receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_currency_id))
                        receiver_currency_data = receiver_currency.scalar()

                        if not receiver_currency_data:
                            return json({'message': 'Receiver currency not found'}, 404)
                        
                        receiver_currency_name = receiver_currency_data.name
                    
                    except Exception as e:
                        return json({'message': 'Currency not found'}, 400)

                    # Call API to convert the Currency value
                    #Call API
                    try:
                        url = f"{currency_converter_api}/convert?from={sender_currency}&to={receiver_currency_name}&amount={sender_amount}"
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
                                return json({'message': 'Error calling external API', 'error': response.text}, 400)
                            
                    except Exception as e:
                        return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                    converted_amount = api_data['result'] if 'result' in api_data else None

                    if not converted_amount:
                        return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                    
                
                transaction_data = {
                    'transaction_id': transaction_id_details.id,

                    'transaction_id': transaction_id_details.transaction_id,
                    'send_amount': transaction_id_details.amount,

                    'transaction_fee': transaction_id_details.transaction_fee,
                    'payout_amount': transaction_id_details.payout_amount,
                
                    'receiver_curreny': currency_dict[transaction_id_details.receiver_currency].name if transaction_id_details.receiver_currency else None,
                    'receiver_amount': converted_amount if transaction_id_details.receiver else None,
                    'message': transaction_id_details.massage,
                    'transaction_status': transaction_id_details.status,
                    'sender_payment_mode': transaction_id_details.payment_mode,
                    'receiver_payment_mode': transaction_id_details.receiver_payment_mode,
                    'transaction_date': transaction_id_details.created_At,
                    'is_completed': transaction_id_details.is_completed,

                    'sender': {
                    'first_name': sender_data.first_name if sender_data else None,
                    'last_name': sender_data.lastname    if sender_data else None,
                    'id': sender_data.id                 if sender_data else None,
                    'email': sender_data.email           if sender_data else None
                    } if sender_data else None,

                    'receiver': {
                        'first_name': receiver_data.first_name if receiver_data else None,
                        'last_name': receiver_data.lastname if receiver_data else None,
                        'email': receiver_data.email if receiver_data else None,
                        'id': receiver_data.id if receiver_data else None,
                    } if receiver_data else None,

                    'sender_currency': {
                        'name': currency_data.name if currency_data else None
                    } if currency_data else None,

                    'receiver_details': {
                        'full_name': receiver_details_data.full_name,
                        'email': receiver_details_data.email,
                        'mobile_number': receiver_details_data.mobile_number,
                        'amount': receiver_details_data.amount,
                        'pay_mode': receiver_details_data.pay_via,
                        'bank_name': receiver_details_data.bank_name,
                        'acc_no': receiver_details_data.acc_number,
                        'ifsc_code': receiver_details_data.ifsc_code,
                        'additional_info': receiver_details_data.add_info,
                        'address': receiver_details_data.add_info,
                        'currency': currency_dict[receiver_details_data.currency].name if receiver_details_data else None,
                        'received_amount': converted_amount

                    } if receiver_details_data else None,
                }
            
                combined_data.append(transaction_data)

                return json({
                    'msg': 'Transaction data fetched Successfully', 
                    'transfer_transaction_data': combined_data
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


# Update Transfer Transaction By admin
class UpdateTransferTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Update Transfer Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/update/transfer/transactions/'
    

    @auth('userauth')
    @put()
    async def update_transfer_transaction(self, request: Request, input: FromJSON[UpdateTransactionSchema]):
        try:
            async with AsyncSession(async_engine) as session:
                data = input.value

                user_identity = request.identity
                AdminID       = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'message': 'Admin authorization Failed'}, 400)
                # Admin authentication ends

                # Get the transfer transaction
                transaction_obj = await session.execute(select(TransferTransaction).where(
                    TransferTransaction.id == data.transaction_id
                    ))
                transaction_data = transaction_obj.scalar()

                if not transaction_data:
                    return pretty_json({'message': 'Requested transaction not available'}, 404)
                
                # Get sender currency
                sender_currency_name = await session.execute(select(Currency).where(
                    Currency.id == transaction_data.currency
                    ))
                sender_currency_name_obj = sender_currency_name.scalar()

                if not sender_currency_name_obj:
                    return json({'message': 'Did not found recipient Details'}, 404)
                
                if transaction_data.is_completed:
                    return json({'message': "Transaction has been completed"}, 400)
                
                # For Approved status
                if data.status == 'Approved':
                    receiver_detail        = transaction_data.receiver_detail
                    recipient_id           = transaction_data.receiver
                    sender_id              = transaction_data.user_id
                    sender_currency        = transaction_data.currency
                    total_amount           = transaction_data.payout_amount

                    recipient_payment_mode = transaction_data.receiver_payment_mode

                    # Get the sender wallet
                    sender_wallet_transfer = await session.execute(select(Wallet).where(
                        Wallet.user_id == sender_id, Wallet.currency_id == sender_currency
                        ))
                    sender_wallet_transfer_obj = sender_wallet_transfer.scalar()

                    if not sender_wallet_transfer_obj:
                        return json({"message": "Sender donot have a wallet"}, 404)
                    
                    # Available balance validation
                    if sender_wallet_transfer_obj.balance <= total_amount:
                        return json({'message': 'Sender do not have sufficient wallet balance'}, 400)
                    

                    if recipient_payment_mode:

                        if recipient_payment_mode == 'Bank':
                            receiver_details      = await session.execute(select(ReceiverDetails).where(ReceiverDetails.id == receiver_detail))
                            receiver_details_obj = receiver_details.scalar()

                            if not receiver_details_obj:
                                return json({'message': 'Did not found recipient Details'}, 404)
                            
                            receiver_currency      = await session.execute(select(Currency).where(
                                Currency.id == receiver_details_obj.currency
                                ))
                            receiver_currency_obj  = receiver_currency.scalar()

                            if not receiver_currency_obj:
                                return json({'message': 'Did not found Receiver Currency'}, 404)
                            
                            if sender_wallet_transfer_obj.balance <= transaction_data.payout_amount:
                                return json({'message': 'Sender do not have sufficient wallet balance'}, 400)
                            
                            if sender_wallet_transfer_obj.balance >= transaction_data.payout_amount:
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
                                        return json({'message': 'Error calling external API', 'error': response.text}, 400)
                            
                                except Exception as e:
                                    return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                                converted_amount = api_data['result'] if 'result' in api_data else None

                                if not converted_amount:
                                    return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                                
                                #Update Receiver Received amount
                                receiver_details_obj.amount = converted_amount
                                session.add(receiver_details_obj)

                                # Deduct from sender wallet
                                try:
                                    sender_wallet_transfer_obj.balance -=  total_amount
                                    session.add(sender_wallet_transfer_obj)

                                except Exception as e:
                                    return json({'msg': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)

                                transaction_data.status            = 'Approved'
                                transaction_data.is_completed      = True
                                transaction_data.credited_amount   = converted_amount
                                transaction_data.credited_currency = receiver_currency_obj.name

                                session.add(transaction_data)
                                
                                await session.commit()
                                await session.refresh(sender_wallet_transfer_obj)
                                await session.refresh(transaction_data)
                                await session.refresh(receiver_details_obj)

                                return json({
                                    'message': 'Transfer Transaction updated successfully', 
                                    'is_completed': True}, 200
                                    )
                            
                         # Recipient payment mode is Wallet
                        #==============================================
                        elif recipient_payment_mode == 'Wallet':
                            recipient_wallet     = await session.execute(select(Wallet).where(and_(
                                Wallet.user_id == recipient_id, Wallet.currency_id == transaction_data.receiver_currency
                                )))
                            recipient_wallet_obj = recipient_wallet.scalars().first()

                            if not recipient_wallet_obj:
                                return json({'message': 'Recipient wallet not found'}, 404)
                            
                            #If Sender wallet and receiver wallet are same
                            if sender_wallet_transfer_obj.id == recipient_wallet_obj.id:
                                return json({'message': 'Cannot transfer to same account'}, 404)

                            if sender_wallet_transfer_obj.balance <= transaction_data.payout_amount:
                                return json({'message': 'Sender do not have sufficient wallet balance'}, 400)
                            
                            if sender_wallet_transfer_obj.balance >= transaction_data.payout_amount:
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
                                        return json({'message': 'Error calling external API', 'error': response.text}, 400)

                                except Exception as e:
                                    return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                                converted_amount = api_data['result'] if 'result' in api_data else None

                                if not converted_amount:
                                    return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                                
                                # Add into Receiver Wallet
                                recipient_wallet_obj.balance += converted_amount
                                session.add(recipient_wallet_obj)

                                # Deduct from sender wallet
                                sender_wallet_transfer_obj.balance -=  total_amount
                                session.add(sender_wallet_transfer_obj)  

                                transaction_data.status            = 'Approved'
                                transaction_data.is_completed      = True
                                transaction_data.credited_amount   = converted_amount
                                transaction_data.credited_currency = recipient_wallet_obj.currency

                                session.add(transaction_data)

                                await session.commit()
                                await session.refresh(recipient_wallet_obj)
                                await session.refresh(sender_wallet_transfer_obj)
                                await session.refresh(transaction_data)

                                return json({'message': 'Transfer Transaction updated successfully', 'is_completed': True}, 200)
                            
                            else:
                                return json({'message': 'Donot have sufficient balance in Wallet'}, 400)
                        
                        else:
                            # Get the receiver details
                            receiver_details      = await session.execute(select(ReceiverDetails).where(ReceiverDetails.id == receiver_detail))
                            receiver_details_obj  = receiver_details.scalar()

                            if not receiver_details_obj:
                                return json({'message': 'Did not found recipient Details'}, 404)
                            
                            # Get receiver currency
                            receiver_currency      = await session.execute(select(Currency).where(Currency.id == receiver_details_obj.currency))
                            receiver_currency_obj  = receiver_currency.scalar()

                            if not receiver_currency_obj:
                                return json({'message': 'Did not found Receiver Currency'}, 404)
                            
                            # Sender wallet Validation
                            if sender_wallet_transfer_obj.balance <= transaction_data.payout_amount:
                                return json({'message': 'Sender do not have sufficient wallet balance'}, 400)
                            
                            if sender_wallet_transfer_obj.balance >= transaction_data.payout_amount:
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
                                        return json({'message': 'Error calling external API', 'error': response.text}, 400)
                            
                                except Exception as e:
                                    return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

                                converted_amount = api_data['result'] if 'result' in api_data else None

                                if not converted_amount:
                                    return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
                                
                                #Update Receiver Received amount
                                receiver_details_obj.amount = converted_amount
                                session.add(receiver_details_obj)

                                # Deduct from sender wallet
                                try:
                                    sender_wallet_transfer_obj.balance -=  total_amount
                                    session.add(sender_wallet_transfer_obj)

                                except Exception as e:
                                    return json({'message': 'Unable to update sender wallet', 'error': f'{str(e)}'}, 400)
                                

                                # Update transaction Data
                                transaction_data.status            = 'Approved'
                                transaction_data.is_completed      = True
                                transaction_data.credited_currency = receiver_currency_obj.name
                                transaction_data.credited_amount   = converted_amount

                                session.add(transaction_data)
                                
                                await session.commit()
                                await session.refresh(sender_wallet_transfer_obj)
                                await session.refresh(transaction_data)
                                await session.refresh(receiver_details_obj)

                                return json({'message': 'Transfer Transaction updated successfully', 'is_completed': True}, 200)
                    else:
                        return json({'message': 'Recipient payment mode does not exists please update New transaction'}, 400)

                else:
                    transaction_data.status = data.status

                    session.add(transaction_data)
                    await session.commit()
                    await session.refresh(transaction_data)

                    return json({
                        'message': 'Transaction Updated Successfully', 
                        'data': transaction_data, 
                        'is_completed': False}, 
                        200)

        except Exception as e:
            return json({'error': 'Server error', 'message': f'{str(e)}'}, 500)
        



## Filter Transfer Transaction
class FilterTransferTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter Transfer Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/admin/filter/transfer/transaction/'
    

    ## Filter all transfer transaction by Admin
    @auth('userauth')
    @post()
    async def filter_transferTransaction(self, request: Request, schema: AdminFilterTransferTransaction, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id')

                # Admin Authentication
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'message': 'Admin authorization Failed'}, 400)
                # Admin authentication ends

                ## Get payload data
                dateTime  = schema.date_time
                email     = schema.email
                status    = schema.status
                currency  = schema.currency
                startDate = schema.start_date
                endDate   = schema.end_date

                conditions = []   ## apply all conditions
                combined_data = []  ## Append all data
                paginatedValue = 0


                ### Filter datetime wise
                if dateTime and dateTime == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            TransferTransaction.created_At < (end_date + timedelta(days=1)),
                            TransferTransaction.created_At >= start_date
                            )
                        )
                
                elif dateTime:
                    start_date, end_date = get_date_range(dateTime) 

                    conditions.append(
                        and_(
                            TransferTransaction.created_At <= end_date,
                            TransferTransaction.created_At >= start_date
                            )
                        )
                

                # Filter Email wise
                if email:
                    fiat_user_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{email}%")
                    ))
                    fiat_user = fiat_user_obj.scalar()

                    if fiat_user:
                        conditions.append(
                            TransferTransaction.user_id == fiat_user.id
                        )
                    else:
                        return json({'message': 'Invalid email'}, 404)
                    

                ## Filter status wise
                if status:
                    conditions.append(
                        TransferTransaction.status.ilike(f"{status}%")
                    )

                ## Filter Currency wise
                if currency:
                    filter_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{currency}%")
                    ))
                    filter_currency = filter_currency_obj.scalar()

                    conditions.append(
                        TransferTransaction.currency == filter_currency.id
                    )

                ### Select the Table
                select_transfer = select(TransferTransaction)

                if conditions:
                    #Get all transaction Data
                    query_ = select_transfer.where(and_(*conditions))

                    result           = await session.execute(query_.order_by(desc(TransferTransaction.id)).limit(limit).offset(offset))
                    all_transactions = result.scalars().all()

                    ### Count Paginated Value
                    count_transfer_transaction_stmt = select(func.count()).select_from(TransferTransaction).where(
                        *conditions
                    )
                    transfer_transaction_count = (await session.execute(count_transfer_transaction_stmt)).scalar()

                    paginated_value = transfer_transaction_count / limit

                    if not all_transactions:
                        return json({'message': 'No transaction found'}, 404)

                else:
                    return json({'message': 'No transaction found'}, 404)
                
                # Get the Currency
                all_currency_obj = await session.execute(select(Currency))
                all_currency     = all_currency_obj.scalars().all()

                if not all_currency:
                    return json({'message': 'Currency not available'}, 404)
                
                # Get the user data
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                if not user_obj_data:
                    return json({'message': 'User not available'}, 404)
                
                # Prepare dictionaries for output data
                currency_dict = {currency.id: currency for currency in all_currency}
                user_dict     = {user.id: user for user in user_obj_data}
                receiver_dict = {receiver.id: receiver for receiver in user_obj_data}

                ### Gather all data
                for transaction in all_transactions:
                    currency_id             = transaction.currency
                    currency_data           = currency_dict.get(currency_id)

                    user_id   = transaction.user_id
                    user_data = user_dict.get(user_id)
                    user_data = {
                        'first_name': user_data.first_name, 
                        'lastname': user_data.lastname, 
                        'email': user_data.email,
                        'id': user_data.id
                        } if user_data else None

                    receiver_id   = transaction.receiver
                    receiver_data = receiver_dict.get(receiver_id)
                    receiver_data = {
                        'first_name': receiver_data.first_name, 
                        'lastname': receiver_data.lastname, 
                        'id': receiver_data.id
                        } if receiver_data else None

                    combined_data.append({
                        'transaction': transaction,
                        'sender_currency': currency_data,
                        'user': user_data,
                        'receiver': receiver_data
                    })

                return json({
                    'success': True,
                    'filtered_transaction_data': combined_data,
                    'paginated_count': paginated_value

                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)



### Export Transfer Transactions
class ExportTransferTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Transfer Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/admin/export/transfer/transaction/'
    
    ## Export Transfer Transaction By Admin
    @auth('userauth')
    @get()
    async def export_transferTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id')

                # Admin Authentication
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'message': 'Admin authorization Failed'}, 400)
                # Admin authentication end

                combined_data = []
                #Get all transaction Data
                get_all_transaction = await session.execute(select(TransferTransaction).order_by(
                    desc(TransferTransaction.id)
                ))
                get_all_transaction_obj = get_all_transaction.scalars().all()

                #Get the Currency
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                #Get the user data
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                ## Receiver details
                receiver_details_obj = await session.execute(select(ReceiverDetails))
                receiver_details     = receiver_details_obj.scalars().all()

                # Prepare dictionaries for output data
                currency_dict          = {currency.id: currency for currency in currency_obj}
                receiver_currency_dict = {currency.id: currency for currency in currency_obj}
                user_dict              = {user.id: user for user in user_obj_data}
                receiver_dict          = {receiver.id: receiver for receiver in user_obj_data}
                receiver_details_dict  = {details.id: details for details in receiver_details}


                for transaction in get_all_transaction_obj:
                    ## Transaction Currency
                    currency_id             = transaction.currency
                    currency_data           = currency_dict.get(currency_id)

                    ## Receiver Currency 
                    receiver_currency_id  = transaction.receiver_currency
                    receiver_currency_data = receiver_currency_dict.get(receiver_currency_id)

                    ## Sender data
                    user_id   = transaction.user_id
                    user_data = user_dict.get(user_id)

                    ## Receiver Details
                    receiver_details_id   = transaction.receiver_detail
                    if receiver_details_id:
                        receiver_details_data = receiver_details_dict.get(receiver_details_id)
                    else:
                        receiver_details_data = None

                    receiver_id   = transaction.receiver
                    if receiver_id:
                        receiver_data = receiver_dict.get(receiver_id)
                    else:
                        receiver_data = None


                    combined_data.append({
                        'id': transaction.id,
                       'sender_name': user_data.full_name if user_data else None,
                       'sender_email': user_data.email if user_data else None,
                       'transaction_id': transaction.transaction_id,
                       'transaction_amount': transaction.amount,
                       'transaction_fee': transaction.transaction_fee,
                       'transaction_currency': currency_data.name,
                       'transaction_purpose': transaction.massage,
                       'status': transaction.status,
                       'credited_amount': transaction.credited_amount,
                       'credited_currency': transaction.credited_currency,
                       
                       ## Receiver if Receiver payment mode is wallet
                       'receiver_user_name': receiver_data.full_name if receiver_data else None,
                       'receiver_email': receiver_data.email if receiver_data else None,
                       'receiver_payment_mode': transaction.receiver_payment_mode,
                       'receiver_currency': receiver_currency_data.name,

                       ## Receiver Bank Details
                       'receiver_name': receiver_details_data.full_name if receiver_details_data else None,
                       'receiver_email': receiver_details_data.email if receiver_details_data else None,
                       'receiver_mobile_number': receiver_details_data.mobile_number if receiver_details_data else None,
                       'receiver_bank_name': receiver_details_data.bank_name if receiver_details_data else None,
                       'receiver_account_number': receiver_details_data.acc_number if  receiver_details_data else None,
                       'receiver_ifsc_code': receiver_details_data.ifsc_code if receiver_details_data else None
                    })

                return json({
                    'success': True,
                    'export_transfer_transaction_data': combined_data
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)