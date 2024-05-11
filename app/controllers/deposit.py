from blacksheep.server.controllers import post, APIController
from Models.schemas import ExternalTransectionSchema ,WithdrawlAndDeposieSchema, DepositMoneySchema
from sqlmodel import select, and_
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
    async def create_deposit(self, transfer_money: DepositMoneySchema, request: Request):
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
                            
                        userID = user_data["user_id"]
                        
                except Exception as e:
                   return json({'msg': 'Authentication Failed'}, 400)
                
                #Try to get the currency id
                try:
                    currency = await session.execute(select(Currency).where(Currency.name == transfer_money.currency))
                    currency_obj = currency.scalar()
                except Exception as e:
                    return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
               
                # Get the user's wallet
                try:
                    user_wallet = await session.execute(select(Wallet).where(and_(Wallet.user_id == userID, Wallet.currency_id == currency_obj.id)))
                    user_wallet_obj = user_wallet.scalars().first()
                except Exception as e:
                    return json({'mag': 'Wallet error','error': f'{str(e)}'}, 400)

                if not currency_obj:
                    return json({"msg": "Invalid currency"}, status=400)
                
                if not user_wallet_obj:
                    return json({"msg": "Wallet not found"}, status=404)
                
                # Update the user's wallet balance
                user_wallet_obj.balance += transfer_money.deposit_amount

                # Create a new transaction record
                new_transaction = Transection(
                    user_id      = userID,
                    txdid        = str(uuid.uuid4()), 
                    txdtype      = 'Deposit',
                    amount       = transfer_money.deposit_amount,
                    txdfee       = currency_obj.fee,
                    totalamount  = transfer_money.total_amount,
                    txdcurrency  = currency_obj.id,
                    txdmassage   = "Deposit",
                    payment_mode = transfer_money.payment_mode,
                    txdstatus    = "Success"
                )

                session.add(user_wallet_obj)
                session.add(new_transaction)
                await session.commit()
                await session.refresh(user_wallet_obj)
                await session.refresh(new_transaction)

                # Return success response with updated balance
                return json({"msg": "Deposit successful", "data": {"balance": user_wallet_obj.balance}}, status=200)
        except Exception as e:
            # Return error response with error message
            return json({"msg": "Error depositing funds", "error": str(e)}, status=400)
        
    