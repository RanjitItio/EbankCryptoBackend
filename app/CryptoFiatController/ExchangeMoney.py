from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.FIAT.Schema import FiatExchangeMoneySchema
from Models.models import Wallet, Currency, Users
from Models.models4 import FIATExchangeMoney
from sqlmodel import select, and_, desc, func




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

                ## Get The user 
                fiat_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                fiat_user = fiat_user_obj.scalar()

                ## If user has been suspended
                if fiat_user.is_suspended:
                    return json({'message': 'Suspended User'}, 400)
                
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
        

    ### Get all exchange transaction of a specific user
    @auth('userauth')
    @get()
    async def get_userExchangeTransactions(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                ## Select columns
                stmt = select(
                    FIATExchangeMoney.id,
                    FIATExchangeMoney.user_id,
                    FIATExchangeMoney.to_currency,
                    FIATExchangeMoney.exchange_amount,
                    FIATExchangeMoney.converted_amount,
                    FIATExchangeMoney.transaction_fee,
                    FIATExchangeMoney.status,
                    FIATExchangeMoney.created_At,

                    Currency.name.label('from_currency')
                ).join(
                    Currency, Currency.id == FIATExchangeMoney.from_currency
                ).where(
                    FIATExchangeMoney.user_id == user_id
                ).order_by(
                    desc(FIATExchangeMoney.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ## Count Total Rows
                select_rows         = select(func.count(FIATExchangeMoney.id)).where(FIATExchangeMoney.user_id == user_id)
                exec_select_rows    = await session.execute(select_rows)
                total_exchange_rows = exec_select_rows.scalar()

                total_paginated_rows = (total_exchange_rows / limit)


                ## Get all exchange requests of the user
                user_fiat_exchange_requests_obj = await session.execute(stmt)
                user_fiat_exchange_requests    = user_fiat_exchange_requests_obj.fetchall()

                if not user_fiat_exchange_requests:
                    return json({'message': 'No exchange transaction found'}, 404)
                

                ## Add all data into combined_data
                for transaction in user_fiat_exchange_requests:
                    toCurrencyObj = await session.execute(select(Currency).where(
                        Currency.id == transaction.to_currency
                    ))
                    toCurrency = toCurrencyObj.scalar()

                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'from_currency': transaction.from_currency,
                        'to_currency': toCurrency.name,
                        'exchange_amount': transaction.exchange_amount,
                        'converted_amount': transaction.converted_amount,
                        'transaction_fee': transaction.transaction_fee,
                        'status': transaction.status,
                        'created_At': transaction.created_At
                    })

                return json({
                    'success': True,
                    'user_fiat_exchange_data': combined_data,
                    'total_rows': total_paginated_rows
                }, 200)
            
        except Exception as e:
            return json({
                "error": 'Server Error',
                "message": f'{str(e)}'
                }, 500)

