# from blacksheep.server.controllers import APIController
# from Models.schemas import currencyExchange
# from sqlmodel import select
# from database.db import async_engine, AsyncSession
# from Models.models import  Wallet, Currency
# from blacksheep import Request, json
# from sqlalchemy.exc import SQLAlchemyError
# from app.controllers.controllers import post





# class CurrencyExchangeController(APIController):
#     @classmethod
#     def route(cls):
#         return '/api/v1/user/currency-exchange'

#     @classmethod
#     def class_name(cls):
#         return "Currency Exchange Controller"

#     @post()
#     async def exchange(self, currency_exchange: currencyExchange, request: Request):
#         try:
#             async with AsyncSession(async_engine) as session:
#                 # Get the user's wallet
#                 user_wallet = await session.execute(select(Wallet).where(Wallet.user_id == currency_exchange.user_id))
#                 user_wallet_obj = user_wallet.scalars().first() 
#                 # Get the source currency object
#                 source_currency = await session.execute(select(Currency).where(Currency.id == currency_exchange.from_currency))
#                 source_currency_obj = source_currency.scalars().first()
#                 # Get the target currency object
#                 target_currency = await session.execute(select(Currency).where(Currency.id == currency_exchange.to_currency))

#                 if not source_currency_obj:
#                     return json({"message": "Invalid currency"}, status=400)
#                 if not target_currency:
#                     return json({"message": "Invalid currency"}, status=400)
#                 if not user_wallet_obj:
#                     return json({"message": "Wallet not found"}, status=404)
#                 target_currency_obj = target_currency.scalars().first()
#                 # Check if the user has enough balance in the source currency
#                 if user_wallet_obj.balance < currency_exchange.amount:
#                     return {"error": "Insufficient balance"},400
#                 # Calculate the exchange rate and the target amount
#                 exchange_rate = 1 / 3
#                 target_amount = currency_exchange.amount * exchange_rate
#                 # Update the user's wallet balance
#                 user_wallet_obj.balance -= currency_exchange.amount
#                 return json({"success": True, "target_amount": target_amount})
#                 # Create a new transaction record for the source currency
#         except SQLAlchemyError as e:
#             return json({"error": str(e)}, 500)
#             # Create a new transaction record for the target currency
        
                    
            