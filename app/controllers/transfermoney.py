from blacksheep.server.controllers import post, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
import uuid
import jwt




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
                            return json({'msg': 'Token has expired'})
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'})
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]

                except Exception as e:
                   return json({'msg': 'Authentication Failed'})
                
                try:
                    recipient = await session.execute(select(Users).where(Users.email == transfer_data.recivermail))
                    recipient_obj = recipient.scalars().first()
                    
                except Exception as e:
                    return json({'msg': 'Unable to identify Recipient'})

                if not recipient_obj:
                    return json({"message": "Receipient not found"}, status=404)
                
                #User Wallet
                try:
                    user_wallet = await session.execute(select(Wallet).where(Wallet.user_id == user_id and Wallet.currency_id == transfer_data.currency))
                    user_wallet_obj = user_wallet.scalars().first()

                    if not user_wallet_obj:
                        return json({"message": "Sender Wallet not found"}, status=404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to locate user Wallet'})
                
                #Recipient Wallet
                try:
                    recipient_wallet = await session.execute(select(Wallet).where(Wallet.user_id == recipient_obj.id and Wallet.currency_id == transfer_data.currency))
                    recipient_wallet_obj = recipient_wallet.scalars().first()

                    if not recipient_wallet_obj:
                        return json({'msg': 'Recipient wallet not found'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to locate user Wallet'}, 400)
                

                if user_wallet_obj.balance >= transfer_data.transfer_amount:
                    user_wallet_obj.balance -=  transfer_data.transfer_amount
                    recipient_wallet_obj.balance += transfer_data.transfer_amount

                    unique_transaction_id = uuid.uuid4()
                    timestamp = str(int(time.time()))

                    addtransection = Transection(
                        user_id     = user_id,
                        txdid       = f"{timestamp}-{unique_transaction_id}",
                        # txdtype     = transfer_data.txdtype,
                        txdrecever  = recipient_obj.id,
                        amount      = transfer_data.transfer_amount,
                        txdfee      = transfer_data.fee,
                        totalamount = transfer_data.total_amount,
                        txdcurrency = transfer_data.currency,
                        txdmassage  = transfer_data.note,
                        # txdtype='transfer'                        
                    )
                    session.add(user_wallet_obj)
                    session.add(addtransection)
                    await session.commit()

                    return json({'msg': 'Transfer successful'},200)
                else:
                    return json({'msg': 'Insufficient balance'},400)
        except SQLAlchemyError as e:
                return json({"Error": str(e)}, 500)
            



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