from blacksheep.server.controllers import post, get, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema
from sqlmodel import select, and_
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import  decode_token
import time
import uuid
from blacksheep.server.responses import pretty_json




class TransferMoneyController(APIController):
    
    @classmethod
    def route(cls):
        return '/api/v1/user/transfer_money'

    @classmethod
    def class_name(cls):
        return "Transfer Money"
    
    @post()
    async def create_transfer_money(self, transfer_data: TransferMoneySchema, request: Request):
        
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
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]

                except Exception as e:
                   return json({'msg': 'Authentication Failed'}, 400)
                
                try:
                    recipient = await session.execute(select(Users).where(Users.email == transfer_data.recivermail))
                    recipient_obj = recipient.scalars().first()
                    
                except Exception as e:
                    return json({'msg': 'Unable to identify Recipient'}, 400)

                if not recipient_obj:
                    return json({"msg": "Receipient not found please provide a valid email address"}, status=404)
                
                #Try to get the currency id
                try:
                    currency = await session.execute(select(Currency).where(Currency.name == transfer_data.currency))
                    currency_obj = currency.scalar()
                except Exception as e:
                    return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
                #User Wallet
                try:
                    user_wallet = await session.execute(select(Wallet).where(and_(Wallet.user_id == user_id, Wallet.currency_id == currency_obj.id)))
                    user_wallet_obj = user_wallet.scalars().first()

                    if not user_wallet_obj:
                        return json({"msg": "Sender Wallet not found"}, status=404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to locate user Wallet'}, 400)
            
                
                #Recipient Wallet
                try:
                    recipient_wallet = await session.execute(select(Wallet).where(Wallet.user_id == recipient_obj.id and Wallet.currency_id == currency_obj.id))
                    recipient_wallet_obj = recipient_wallet.scalars().first()

                    if not recipient_wallet_obj:
                        return json({'msg': 'Recipient wallet not found'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to locate recipient Wallet'}, 400)
                
                if user_id == recipient_obj.id:
                    return json({'msg': 'Cannot transfer to self'}, 404)
                
                if user_wallet_obj.balance >= transfer_data.transfer_amount:
                    # user_wallet_obj.balance -=  transfer_data.transfer_amount
                    # recipient_wallet_obj.balance += transfer_data.transfer_amount

                    unique_transaction_id = uuid.uuid4()
                    timestamp = str(int(time.time()))

                    addtransection = Transection(
                        user_id     = user_id,
                        txdid       = f"{timestamp}-{unique_transaction_id}",
                        txdrecever  = recipient_obj.id,
                        amount      = transfer_data.transfer_amount,
                        txdfee      = transfer_data.fee,
                        totalamount = transfer_data.total_amount,
                        txdcurrency = currency_obj.id,
                        txdmassage  = transfer_data.note,
                        txdstatus   = 'Pending',
                        txdtype     = 'Transfer'
                    )
                    session.add(user_wallet_obj)
                    session.add(addtransection)
                    await session.commit()

                    return json({'msg': 'Transfer successfull'},200)
                else:
                    return json({'msg': 'Insufficient Funds'},400)
                
        except SQLAlchemyError as e:
                return json({"Error": str(e)}, 500)
            



class AllTransferController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/transfer/transactions'
    
    @classmethod
    def class_name(cls) -> str:
        return 'All Transfer Transaction'
    

    @get()
    async def get_transferTransaction(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    #Get the token from requeseted header
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
                    get_all_transaction     = await session.execute(select(Transection).where(Transection.txdtype == 'Transfer'))
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
                            'currency': currency_data,
                            'user': user_data,
                            'receiver': receiver_data
                        })

                if not get_all_transaction_obj:
                    return json({'msg': "No Transaction available to show"}, 404)
                
                return json({'msg': 'Deposit Transaction data fetched successfully', 'data': combined_data})
            
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)



class ExternalMoneyTransferController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/external_transfer_money'

    @classmethod
    def class_name(cls):
        return "Transfer Money"
    
    @post()
    async def transfer_money(self, transfer_data: ExternalTransectionSchema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user making the transfer
                # user = await session.execute(select(Users).where(Users.id == transfer_data.user_id))
                # user_obj = user.scalars().first()
                # Get the recipient user
                # recipient = await session.execute(select(Users).where(Users.email == transfer_data.reciver))
                # recipient_obj = recipient.scalars().first()
                user_wallet = await session.execute(select(Wallet).where(Wallet.user_id ==transfer_data.user_id and Wallet.currency_id == transfer_data.txdcurrency))
                user_wallet_obj = user_wallet.scalars().first()
                # Check if the user has enough balance
                if user_wallet_obj.balance >= transfer_data.amount:
                    # Deduct the amount from the user's balance
                    user_wallet_obj.balance -=  transfer_data.amount
                    print(user_wallet_obj.balance)
                    # Add the amount to the recipient's balance
                    e_txn = ExternalTransection(
                        user_id=transfer_data.user_id,
                        txdid=str(int(time.time())),
                        txdtype=transfer_data.txdtype,
                        txdrecever=transfer_data.recipientfullname,
                        amount=transfer_data.amount,
                        txdfee=transfer_data.txdfee,
                        totalamount=transfer_data.amount - transfer_data.txdfee,
                        txdcurrency=transfer_data.txdcurrency,
                        recipientfullname=transfer_data.recipientfullname,
                        recipientemail=transfer_data.recipientemail,
                        recipientmobile=transfer_data.recipientmobile,
                        recipientbanktransfer=transfer_data.recipientbanktransfer,
                        recipientbankname=transfer_data.recipientbankname,
                        recipientbankaccountno=transfer_data.recipientbankaccountno,
                        recipientbankswiftcode=transfer_data.recipientbankifsc,
                        recipientaddress=transfer_data.recipientaddress,
                        recipientcurrency =transfer_data.recipientcurrency,
                        )
                    session.add(user_wallet_obj)
                    session.add(e_txn)
                    # session.add(recipient_wallet_obj)
                    await session.commit()
                    return json({'msg': 'External Transfer successful But bank API is not here'},200)
                else:
                    return json({'msg': 'Insufficient balance'},400)
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)