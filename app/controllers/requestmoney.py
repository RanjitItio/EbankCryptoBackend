from blacksheep.server.controllers import post, APIController
from Models.schemas import RequestMoneySchemas 
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , RequestMoney
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time


class RequestMoneyController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/request_money'

    @classmethod
    def class_name(cls):
        return "Request Money"

    @post()
    async def request_money(self, request_data: RequestMoneySchemas, request: Request):
        try:
            
            async with AsyncSession(async_engine) as session:
                # Get the user making the request
                user = await session.execute(select(Users).where(Users.id == request_data.user_id))
                user_obj = user.scalars().first()
                
                if user_obj:
                    # Get the wallet of the user making the request
                    wallet = await session.execute(select(Wallet).where(Wallet.user_id == user_obj.id))
                    wallet_obj = wallet.scalars().first()
                    if wallet_obj:
                        # Create a new transection record
                        resuest_money = RequestMoney(
                            user_id=user_obj.id,
                            recipient_id=request_data.recipient_user_id,
                            amount=request_data.amount,
                            currency_id=request_data.currency,
                            message=request_data.note,
                            
                        )
                        session.add(resuest_money)
                        await session.commit()
                        return json({"message": "Request sent successfully"}, status=200)
                    else:
                        return json({"message": "Wallet not found"}, status=404)
                else:
                    return json({"message": "User not found"}, status=404)
        except SQLAlchemyError as e:
            return json({"message": "Error creating request", "error": str(e)}, status=500)
                