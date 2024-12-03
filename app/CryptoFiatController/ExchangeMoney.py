from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.FIAT.Schema import FiatExchangeMoneySchema, UserFilterFIATExchangesSchema
from Models.models import Wallet, Currency, Users
from Models.models4 import FIATExchangeMoney
from sqlmodel import select, and_, desc, func
from datetime import datetime, timedelta
from app.dateFormat import get_date_range




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
        """
        This function handles the creation of a new FIAT exchange money request <br/>
<br/>
        Parameters:<br/>
        - request (Request): The request object containing user identity and payload data.<br/>
        - schema (FiatExchangeMoneySchema): The schema object containing validated payload data.<br/>
<br/>
        Returns:<br/>
        - JSON response with success status, message, or error details.
        """
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
        """
            This function retrieves a user's exchange transactions, including details like currency,
            amounts, fees, and status, and returns them in paginated form along with the total number of
            rows.<br/><br/>

            Parameters:<br/>
               - request: request object.<br/>
               - limit(int): The `limit` parameter specifies the maximum number of exchange transactions to retrieve in a single request. By default, the limit is set to 10.<br/>
               - offset(int): The `offset` parameter specifies the starting point from which the data should be retrieved. By default, the offset is set to 0.<br/><br/>
            
            Returns:<br/>
            - JSON response containing the user's fiat exchange data, total paginated rows, and a success message.<br/><br/>

            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
        """
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





#### Filter FIAT Exchange 
class UserFilterFIATExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Filter FIAT Transaction Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/user/filter/fiat/exchanges/'
    
    
    #### Filter FIAT Exchange Transactions
    @auth('userauth')
    @post()
    async def filter_userExchanges(self, request: Request, schema: UserFilterFIATExchangesSchema, limit: int = 10, offset: int = 0):
        """
           This API Endpoint will filter out all the FIAT Exchange Transactions.<br/><br/>

           Parameters:<br/>
               - request (Request): The request object containing user identity and other information.<br/>
               - schema (UserFilterFIATExchangesSchema): The schema containing the filter criteria.<br/>
               - limit (int, optional): The number of transactions to retrieve per page. Default is 10.<br/>
               - offset (int, optional): The number of transactions to skip before starting to retrieve. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, a list of transaction data, and the total number of pages.<br/>
                - paginated_count (int): The total number of pages available for the filtered transactions.<br/>
                - user_filtered_fiat_exchanges: All the filtered transaction data.<br/>
                - success - True if successful.<br/><br/>

             Error message:<br/>
                - Error Response status code 404 - "message": "No data found"<br/>
                - Error Response status code 500 - "error": "Server Error"<br/><br/>

             Raises:<br/>
                - ValueError: If the input data is not valid.<br/>
                - Exception: If there is an error while executing the SQL queries.<br/>
                - SqlAlchemyError: If there is an error while executing the SQL queries.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                dateRange    = schema.dateRange
                fromCurrency = schema.from_currency
                toCurrency   = schema.to_currency
                status       = schema.status
                startDate    = schema.start_date
                endDate      = schema.end_date

                exchange_conditions = []
                combined_data       = []

                ## Filter date range wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    exchange_conditions.append(
                        and_(
                            FIATExchangeMoney.created_At >= start_date,
                            FIATExchangeMoney.created_At < (end_date + timedelta(days=1))
                        )
                    )

                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    exchange_conditions.append(
                        and_(
                            FIATExchangeMoney.created_At >= start_date,
                            FIATExchangeMoney.created_At <= end_date
                        )
                    )

                ### Filter From Currency wise
                if fromCurrency:
                    from_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{fromCurrency}%")
                    ))
                    from_currency = from_currency_obj.scalar()

                    if not from_currency:
                        return json({'message': 'Invalid From Currency'}, 404)
                    
                    exchange_conditions.append(
                        FIATExchangeMoney.from_currency == from_currency.id
                    )

                ### Filter To Currency wise
                if toCurrency:
                    to_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{toCurrency}%")
                    ))
                    to_currency = to_currency_obj.scalar()

                    if not to_currency:
                        return json({'message': 'Invalid To Currency'}, 404)
                    
                    exchange_conditions.append(
                        FIATExchangeMoney.to_currency == to_currency.id
                    )

                ### Filter Status Wise
                if status:
                    exchange_conditions.append(
                        FIATExchangeMoney.status == status
                    )

                ## Select columns
                exchange_stmt = select(
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

                ### IF data found
                if exchange_conditions:
                    exchange_transaction = exchange_stmt.where(and_(*exchange_conditions))

                    user_fiat_exchange_requests_obj = await session.execute(exchange_transaction)
                    user_fiat_exchange_requests     = user_fiat_exchange_requests_obj.fetchall()

                if not user_fiat_exchange_requests:
                    return json({'message': 'No data found'}, 404)
                

                ### Count Paginated Value
                exchange_count_stmt = select(func.count()).select_from(FIATExchangeMoney).where(
                    FIATExchangeMoney.user_id == user_id
                )
                if exchange_conditions:
                    exchange_count_stmt = exchange_count_stmt.where(and_(*exchange_conditions))

                # Execute the count query and get the count value
                exchange_count_result = await session.execute(exchange_count_stmt)
                exchange_count = exchange_count_result.scalar() or 0
                paginated_value = exchange_count / limit


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
                    'user_filter_fiat_exchange_data': combined_data,
                    'paginated_count': paginated_value

                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)