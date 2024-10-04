from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.FIAT.Schema import FiatExchangeMoneySchema
from Models.models import Wallet, Currency
from Models.models4 import FIATExchangeMoney
from sqlmodel import select, and_




# Exchange Money Controller for user
class ExchangeMoneyController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'FIAT Exchange Money Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/fiat/exchange/money/'
    

    @auth('userauth')
    @post()
    async def create_exchange_money_request(self, request: Request, schema: FiatExchangeMoneySchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get the payload data
                fromCurrency    = schema.from_currency
                toCurrency      = schema.to_currency
                exchangeAmount  = float(schema.exchange_amount)
                convertedAmount = schema.convert_amount
                transaction_fee = schema.fee

                # Get from Currency
                from_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == fromCurrency
                ))
                from_currency = from_currency_obj.scalar()

                # Get the From Wallet of the user
                from_wallet_obj  = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.user_id == user_id,
                        Wallet.currency_id == from_currency.id
                    )
                ))
                from_wallet = from_wallet_obj.scalar()

                if not from_wallet:
                    return json({'message': 'Do not have from wallet'}, 400)

                # Balance validation
                if from_wallet.balance < exchangeAmount:
                    return json({'message': 'Do not have sufficient balance in From wallet'}, 400)

                # Get to Currnecy
                to_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == toCurrency
                ))
                to_currency = to_currency_obj.scalar()

                # Create Exchange request
                exchange_request = FIATExchangeMoney(
                    user_id          = user_id,
                    from_currency    = from_currency.id,
                    to_currency      = to_currency.id,
                    exchange_amount  = float(exchangeAmount),
                    converted_amount = float(convertedAmount),
                    transaction_fee  = float(transaction_fee)
                )

                session.add(exchange_request)
                await session.commit()
                await session.refresh(exchange_request)

                return json({
                    'success': True,
                    'message': 'Exchnage money created successfully'
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)