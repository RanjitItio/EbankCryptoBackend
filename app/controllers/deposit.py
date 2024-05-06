from blacksheep.server.controllers import post, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema ,WithdrawlAndDeposieSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import uuid


class DepositController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/deposit'

    @classmethod
    def class_name(cls):
        return "Deposit Controller"

    @post()
    async def deposit(self, transfer_money: WithdrawlAndDeposieSchema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Get the user's wallet

                user_wallet = await session.execute(select(Wallet).where(Wallet.user_id == transfer_money.user_id))
                
                if not user_wallet.scalars().first():
                    return json({"msg": "Wallet not available please create a wallet first"})

                user_wallet_obj = user_wallet.scalars().first()

                # Get the currency object
                currency = await session.execute(select(Currency).where(Currency.id == transfer_money.currency))
                if not currency.scalars().first():
                    return json({'msg': 'Currency not available please create one first'})
                
                currency_obj = currency.scalars().first()

                if not currency_obj:
                    return json({"message": "Invalid currency"}, status=400)
                
                if not user_wallet_obj:
                    return json({"message": "Wallet not found"}, status=404)
                # Update the user's wallet balance
                user_wallet_obj.balance += transfer_money.amount

                # Create a new transaction record
                new_transaction = Transection(
                    user_id=transfer_money.user_id,
                    txdid=str(uuid.uuid4()),  # Use UUID for transaction ID
                    txdtype='deposit',
                    txdrecever=transfer_money.user_id,
                    amount=transfer_money.amount,
                    txdfee=currency_obj.fee,
                    totalamount=transfer_money.amount - (currency_obj.fee / transfer_money.amount) * 100,
                    txdcurrency=transfer_money.currency,
                    txdmassage=transfer_money.note,
                )

                session.add(user_wallet_obj)
                session.add(new_transaction)
                await session.commit()
                await session.refresh(user_wallet_obj)
                await session.refresh(new_transaction)

                # Return success response with updated balance
                return json({"message": "Deposit successful", "data": {"balance": user_wallet_obj.balance}}, status=200)
        except SQLAlchemyError as e:
            # Return error response with error message
            return json({"message": "Error depositing funds", "error": str(e)}, status=400)