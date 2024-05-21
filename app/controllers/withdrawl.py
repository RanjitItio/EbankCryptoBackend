from blacksheep.server.controllers import APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema ,WithdrawlAndDeposieSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
import uuid
from app.controllers.controllers import get, post, put, delete



class UserWithdrawlController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/withdrawl'
    
    @classmethod
    def class_name(cls):
        return "User Withdrawl Controller"
    
    @post()
    async def withdrawl(self, withdrawl_data: WithdrawlAndDeposieSchema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user from the request
                # user = await decode_token(request.headers.get("Authorization"))
                # Get the user's wallet
                wallet = await session.execute(select(Wallet).where(Wallet.user_id == withdrawl_data.user_id))
                wallet_obj = wallet.scalars().first()
                # Get the currency object
                currency = await session.execute(select(Currency).where(Currency.id == withdrawl_data.currency))
                currency_obj = currency.scalars().first()
                # Check if the user has enough balance
                if not currency_obj:
                    return json({"message": "Invalid currency"}, status=400)
                if not wallet_obj:
                    return json({"message": "Wallet not found"}, status=404)
                if wallet_obj.balance < withdrawl_data.amount:
                    return json({"message": "Insufficient balance"}, status=400)
                # Update the user's wallet balance
                wallet_obj.balance -= withdrawl_data.amount
                # Create a new transaction record
                new_transaction = Transection(
                    user_id= withdrawl_data.user_id,
                    txdid= str(uuid.uuid4()),
                    txdtype='withdrawl',
                    txdrecever= withdrawl_data.user_id,
                    amount=withdrawl_data.amount,
                    txdfee=currency_obj.fee,
                    totalamount=withdrawl_data.amount - (currency_obj.fee / withdrawl_data.amount) * 100,
                    txdcurrency=withdrawl_data.currency,
                    txdmassage=withdrawl_data.note
                )
                session.add(wallet_obj)
                
                session.add(new_transaction)
                await session.commit()
                await session.refresh(wallet_obj)
                await session.refresh(new_transaction)
                return json({"message": "Withdrawal successful", "data": {"balance": wallet_obj.balance}}, 200)
            
        except SQLAlchemyError as e:
            await session.rollback()
            return json({"message": "Error occurred during withdrawal", "error": str(e)}, 500)
        
