from blacksheep.server.controllers import APIController
from Models.schemas import RequestMoneySchemas 
from sqlmodel import select, and_
from database.db import async_engine, AsyncSession
from Models.models import Users ,Wallet ,Transection ,Currency , RequestMoney
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
from blacksheep.server.responses import pretty_json
from app.controllers.controllers import get, post, put, delete


# class RequestMoneyController(APIController):
#     @classmethod
#     def route(cls):
#         return '/api/v1/user/request-money'

#     @classmethod
#     def class_name(cls):
#         return "Request Money"

#     @post()
#     async def create_requestmoney(self, requestmoney: RequestMoneySchemas, request: Request):

#         try:
#             async with AsyncSession(async_engine) as session:

#                 # Get the user from requested token
#                 try:
#                     header_value = request.get_first_header(b"Authorization")
#                     if not header_value:
#                         return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
#                     header_value_str = header_value.decode("utf-8")

#                     parts = header_value_str.split()

#                     if len(parts) == 2 and parts[0] == "Bearer":
#                         token = parts[1]
#                         user_data = decode_token(token)

#                         if user_data == 'Token has expired':
#                             return json({'msg': 'Token has expired'}, 400)
#                         elif user_data == 'Invalid token':
#                             return json({'msg': 'Invalid token'}, 400)
#                         else:
#                             user_data = user_data
                            
#                         userID = user_data["user_id"]
                    
#                 except Exception as e:
#                    return json({'msg': 'Authentication Failed'}, 400)
                
#                 try:
#                     user = await session.execute(select(Users).where(Users.id == userID))
#                     user_obj = user.scalars().first()
#                 except Exception as e:
#                     return pretty_json({'error': 'Unable to locate user'}, 400)
                
#                 try:
#                     currency = await session.execute(select(Currency).where(Currency.name == requestmoney.currency))
#                     currency_obj = currency.scalar()
#                 except Exception as e:
#                     return json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
                
#                 if user_obj:
#                     # Get the wallet of the user making the request
#                     try:
#                         wallet = await session.execute(select(Wallet).where(and_(Wallet.user_id == user_obj.id, Wallet.currency_id == currency_obj.id)))
#                         wallet_obj = wallet.scalar()

#                         if not wallet_obj:
#                             return pretty_json({'msg': 'Requested user do not have a wallet'}, 200)
                        
#                     except Exception as e:
#                         return pretty_json({'error': 'Unable to locate requested user wallet'}, 400)

#                     if wallet_obj:
#                         # Create a new transection record
#                         # resuest_money = RequestMoney(
#                         #     user_id=user_obj.id,
#                         #     recipient_id=request_data.recipient_user_id,
#                         #     amount=request_data.amount,
#                         #     currency_id=request_data.currency,
#                         #     message=request_data.note,
                            
#                         # )
#                         # session.add(resuest_money)
#                         await session.commit()
#                         return json({"message": "Request sent successfully"}, status=200)
#                     else:
#                         return json({"message": "Wallet not found"}, status=404)
#                 else:
#                     return json({"message": "User not found"}, status=404)
#         except SQLAlchemyError as e:
#             return json({"message": "Error creating request", "error": str(e)}, status=500)
                