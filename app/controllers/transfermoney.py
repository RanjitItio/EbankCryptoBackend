from blacksheep.server.controllers import post, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time



class TransferMoneyController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/transfer_money'

    @classmethod
    def class_name(cls):
        return "Transfer Money"
    
    @post()
    async def transfer_money(self, transfer_data: TransferMoneySchema, request: Request):
        print("hello")
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user making the transfer
                # user = await session.execute(select(Users).where(Users.id == transfer_data.user_id))
                # user_obj = user.scalars().first()
                # Get the recipient user
                recipient = await session.execute(select(Users).where(Users.email == transfer_data.recivermail))
                recipient_obj = recipient.scalars().first()
                user_wallet = await session.execute(select(Wallet).where(Wallet.user_id == transfer_data.user_id and Wallet.currency_id == transfer_data.currency))
                user_wallet_obj = user_wallet.scalars().first()
                print(user_wallet_obj,user_wallet_obj.balance)
                # Check if the user has enough balance
                if user_wallet_obj.balance >= transfer_data.amount:
                    # Deduct the amount from the user's balance
                    user_wallet_obj.balance -=  transfer_data.amount
                    fees = await session.execute(select(Currency).where(Currency.id == transfer_data.currency))
                    fee =  fees.scalars().first()
                    # Add the amount to the recipient's balance
                    # recipient_wallet = await session.execute(select(Wallet).where(Wallet.user_id == recipient_obj.id and Wallet.currency_id == transfer_data.from_wallet))
                    # recipient_wallet_obj = recipient_wallet.scalars().first()
                    # recipient_wallet_obj.balance += transfer_data.amount
                    addtransection = Transection(
                        user_id=transfer_data.user_id,
                        txdid=str(int(time.time())),
                        txdtype=transfer_data.txdtype,
                        txdrecever=recipient_obj.id,
                        amount=  transfer_data.amount,
                        txdfee=fee.fee,
                        totalamount=transfer_data.amount - (fee.fee/ transfer_data.amount)*100,
                        txdcurrency=transfer_data.currency,
                        txdmassage= transfer_data.note,
                        # txdtype='transfer'                        
                    )
                    print("opopo")
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