from blacksheep.server.controllers import post, APIController
from Models.schemas import TransferMoneySchema , ExternalTransectionSchema ,WithdrawlAndDeposieSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , ExternalTransection
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time
import uuid
from app.auth import decode_token




class DepositController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/deposit'

    @classmethod
    def class_name(cls):
        return "Deposit Money"

    @post()
    async def create_deposit(self, transfer_money: WithdrawlAndDeposieSchema, request: Request):
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
                
                
                # Get the user's wallet
                try:
                    user_wallet = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
                    user_wallet_obj = user_wallet.scalars().first()
                except Exception as e:
                    return json({'msg': f'error {str(e)}'}, 400)
                
                try:
                    # Get the currency object
                    currency = await session.execute(select(Currency).where(Currency.id == transfer_money.currency))
                    currency_obj = currency.scalars().first()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)

                if not currency_obj:
                    return json({"message": "Invalid currency"}, status=400)
                
                if not user_wallet_obj:
                    return json({"message": "Wallet not found"}, status=404)
                
                # Update the user's wallet balance
                user_wallet_obj.balance += transfer_money.deposit_amount

                # Create a new transaction record
                new_transaction = Transection(
                    user_id      = user_data["user_id"],
                    txdid        = str(uuid.uuid4()), 
                    txdtype      = 'Deposit',
                    # txdrecever   = transfer_money.user_id,
                    amount       = transfer_money.deposit_amount,
                    txdfee       = currency_obj.fee,
                    totalamount  = transfer_money.total_amount,
                    txdcurrency  = transfer_money.currency,
                    # txdmassage   = transfer_money.note,
                    payment_mode = transfer_money.payment_mode
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