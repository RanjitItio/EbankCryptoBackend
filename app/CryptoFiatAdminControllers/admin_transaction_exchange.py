from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, desc, and_, func
from Models.models import Users, Currency, Wallet
from Models.models4 import FIATExchangeMoney
from Models.FIAT.Schema import AdminUpdateExchangeMoneySchema, AdminFilterExchangeTransaction
from app.dateFormat import get_date_range
from datetime import datetime, timedelta



# Exchange Money Controller for Admin section
class AdminFiatExchangeMoneyController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Exchange Money Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/exchange/money/'
    

    ## Get all Exchange Money Transactions
    @auth('userauth')
    @get()
    async def get_fiat_exchange_requests(self, request: Request, limit: int = 10, offset: int = 0):
        """
        Retrieves a list of fiat exchange money transactions for admin users.<br/><br/>

        Parameters:<br/>
        request (Request): The HTTP request object containing user identity and other request data.<br/>
        limit (int): The maximum number of transactions to retrieve. Default is 10.<br/>
        offset (int): The number of transactions to skip before starting to collect the result set. Default is 0.<br/><br/>

        Returns:<br/>
        json: A JSON response containing the success status, a list of exchange money data, and the total row count.<br/>
              If the user is not an admin, returns a JSON response with an error message.<br/>
              If no data is found, returns a JSON response with a 'No data found' message.<br/>
              In case of a server error, returns a JSON response with an error message.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity   = request.identity
                AdminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                combined_data = []

                # Count total available rows
                row_stmt = select(func.count(FIATExchangeMoney.id))
                exe_row_stmt = await session.execute(row_stmt)
                exchange_row_count = exe_row_stmt.scalar()

                total_exchange_rows = exchange_row_count / limit
                
                stmt = select(
                    FIATExchangeMoney.id,
                    FIATExchangeMoney.from_currency,
                    FIATExchangeMoney.to_currency,
                    FIATExchangeMoney.exchange_amount,
                    FIATExchangeMoney.converted_amount,
                    FIATExchangeMoney.transaction_fee,
                    FIATExchangeMoney.created_At,
                    FIATExchangeMoney.is_completed,
                    FIATExchangeMoney.user_id,
                    FIATExchangeMoney.status,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    Users, Users.id == FIATExchangeMoney.user_id
                ).order_by(
                    desc(FIATExchangeMoney.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                fiat_exchange_money_obj = await session.execute(stmt)
                fiat_exchange_money     = fiat_exchange_money_obj.fetchall()

                if not fiat_exchange_money:
                    return json({'message': 'No data found'}, 404)

                for transaction in fiat_exchange_money:
                    # From Currency
                    from_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.from_currency
                    ))
                    from_currency = from_currency_obj.scalar()

                    # To Currency
                    to_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.to_currency
                    ))
                    to_currency = to_currency_obj.scalar()

                    combined_data.append({
                        "id": transaction.id,
                        "to_currency": to_currency.name,
                        "converted_amount": transaction.converted_amount,
                        "is_completed": transaction.is_completed,
                        "from_currency": from_currency.name,
                        "exchange_amount": transaction.exchange_amount,
                        "user_id": transaction.user_id,
                        "transaction_fee": transaction.transaction_fee,
                        "created_At": transaction.created_At,
                        "user_name": transaction.user_name,
                        'user_email': transaction.user_email,
                        "status": transaction.status
                    })

                return json({
                    'success': True,
                    'all_exchange_money_data': combined_data,
                    'total_row_count': total_exchange_rows
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    ## update Exchange Money Transaction
    @auth('userauth')
    @put()
    async def update_exchange_money(self, request: Request, schema: AdminUpdateExchangeMoneySchema):
        """
        Updates the status of a fiat exchange money transaction and performs necessary operations on user wallets.<br/><br/>

        Parameters:<br/>
        - request (Request): The HTTP request object containing user identity and other request data.<br/>
        - schema (AdminUpdateExchangeMoneySchema): The schema object containing the updated transaction status and converted amount.<br/><br/>

        Returns:<br/>
        - json: A JSON response containing the success status and a message. In case of an error, returns a JSON response with an error message.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity   = request.identity
                AdminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                # Get payload data
                status            = schema.status
                exchange_money_id = int(schema.exchange_money_id)
                convertedAmount   = float(schema.converted_amount)

                # Get the Exchange Money request
                exchange_money_req_obj = await session.execute(select(FIATExchangeMoney).where(
                    FIATExchangeMoney.id == exchange_money_id
                ))
                exchange_money_req = exchange_money_req_obj.scalar()

                if not exchange_money_req:
                    return json({'message': 'Transaction not found'}, 404)

                if exchange_money_req.is_completed:
                    return json({'message': 'Transaction has been completed'}, 400)

                # get the user wallet
                user_from_wallet_obj =  await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == exchange_money_req.from_currency,
                        Wallet.user_id     == exchange_money_req.user_id
                    )
                ))
                user_from_wallet = user_from_wallet_obj.scalar()

                if not user_from_wallet:
                    return json({'message': 'From Wallet not found'}, 404)
                

                # get the user wallet
                user_to_wallet_obj =  await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == exchange_money_req.to_currency,
                        Wallet.user_id     == exchange_money_req.user_id
                    )
                ))
                user_to_wallet = user_to_wallet_obj.scalar()

                if not user_to_wallet:
                    return json({'message': 'Received Wallet not found'}, 404)
                
                if status == 'Approved':
                    if user_from_wallet.balance < exchange_money_req.exchange_amount:
                        return json({'message': 'Do not have sufficient balance in account'}, 400)
                    
                    # Add and deduct from wallet to respective Wallet
                    total_deduct_amount = exchange_money_req.exchange_amount + exchange_money_req.transaction_fee

                    user_from_wallet.balance -= total_deduct_amount
                    user_to_wallet.balance += convertedAmount

                    # Update transaction status
                    exchange_money_req.status       = 'Approved'
                    exchange_money_req.is_completed = True

                    session.add(exchange_money_req)
                    session.add(user_from_wallet)
                    session.add(user_to_wallet)
                    await session.commit()
                    await session.refresh(exchange_money_req)
                    await session.refresh(user_to_wallet)
                    await session.refresh(user_from_wallet)

                    return json({
                        'success': True,
                        'message': 'Updated successfully'
                        }, 200)
                else:
                    exchange_money_req.status = status
                    exchange_money_req.is_completed = False

                    session.add(exchange_money_req)
                    await session.commit()
                    await session.refresh(exchange_money_req)

                    return json({
                        'success': True,
                        'message': 'Updated successfully'
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




### Filter Exchange Money Transaction
class AdminFilterExchangeMoneyTransaction(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter Exchange Money'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/filter/exchange/money/'

    ### Filter Exchange money
    @auth('userauth')
    @post()
    async def filter_exchange_money(self, request: Request, schema: AdminFilterExchangeTransaction, limit: int = 10, offset: int = 0):
        """
            This function filters exchange transactions based on various criteria and
            returns paginated results along with relevant data.<br/><br/>
            
            Parameters:<br/>
              - request(Request): The incoming request object containing information about the HTTP request<br/>
              - schema(AdminFilterExchangeTransaction): This schema contains data related to filtering exchange transactions, such as date time, email, status, currency, start date, and end date<br/>
              - limit(int): The maximum number of results to return. Default is 10<br/>
              - offset(int): The offset for pagination. Default is 0<br/><br/>

            Returns:<br/>
                JSON: A JSON response containing the following keys:<br/>
                - success(bool): A boolean indicating whether the operation was successful <br/>
                - pagination_count(float): The total number of pages based on the provided limit <br/>
                - admin_filter_exchange_money_data(list): A list of dictionaries, each representing an exchange transaction <br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id')

                 # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                ### Get payload data
                dateTime  = schema.date_time
                email     = schema.email
                status    = schema.status
                currency  = schema.currency
                startDate = schema.start_date
                endDate   = schema.end_date

                conditions    = []
                combined_data = []
                paginated_value = 0

                ## Filter Email wise
                if email:
                    user_email_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{email}%")
                    ))
                    user_email = user_email_obj.scalar()

                    if not user_email:
                        return json({'message': 'Invalid email'}, 400)
                    
                    conditions.append(
                        FIATExchangeMoney.user_id == user_email.id
                    )

                ## Filter Date time wise
                if dateTime and dateTime == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            FIATExchangeMoney.created_At < (end_date + timedelta(days=1)),
                            FIATExchangeMoney.created_At >= start_date
                        )
                    )

                elif dateTime:
                    start_date, end_date = get_date_range(dateTime)

                    conditions.append(
                        and_(
                            FIATExchangeMoney.created_At <= end_date,
                            FIATExchangeMoney.created_At >= start_date
                        )
                    )
                
                ### Filter status wise
                if status:
                    conditions.append(
                        FIATExchangeMoney.status.ilike(f"{status}%")
                    )

                ## Filter From Currency wise
                if currency:
                    filter_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{currency}")
                    ))
                    filter_currency = filter_currency_obj.scalar()

                    conditions.append(
                        FIATExchangeMoney.from_currency == filter_currency.id
                    )
                
                stmt = select(
                    FIATExchangeMoney.id,
                    FIATExchangeMoney.from_currency,
                    FIATExchangeMoney.to_currency,
                    FIATExchangeMoney.exchange_amount,
                    FIATExchangeMoney.converted_amount,
                    FIATExchangeMoney.transaction_fee,
                    FIATExchangeMoney.created_At,
                    FIATExchangeMoney.is_completed,
                    FIATExchangeMoney.user_id,
                    FIATExchangeMoney.status,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    Users, Users.id == FIATExchangeMoney.user_id
                ).order_by(
                    desc(FIATExchangeMoney.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ## If data available
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    all_exchange_transactions_obj = await session.execute(statement)
                    all_exchange_transactions     = all_exchange_transactions_obj.fetchall()

                    ### Count paginated value
                    count_exchange_transaction_stmt = select(func.count()).select_from(FIATExchangeMoney).where(
                        *conditions
                    )
                    exchange_transaction_count = (await session.execute(count_exchange_transaction_stmt)).scalar()

                    paginated_value = exchange_transaction_count / limit


                    if not all_exchange_transactions:
                        return json({'message': 'No data found'}, 404)
                else:
                    return json({'message': 'No data found'}, 404)
                
                 
                ### Get all the data inside a List
                for transaction in all_exchange_transactions:
                    # From Currency
                    from_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.from_currency
                    ))
                    from_currency = from_currency_obj.scalar()

                    # To Currency
                    to_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.to_currency
                    ))
                    to_currency = to_currency_obj.scalar()

                    combined_data.append({
                        "id": transaction.id,
                        "to_currency": to_currency.name,
                        "converted_amount": transaction.converted_amount,
                        "is_completed": transaction.is_completed,
                        "from_currency": from_currency.name,
                        "exchange_amount": transaction.exchange_amount,
                        "user_id": transaction.user_id,
                        "transaction_fee": transaction.transaction_fee,
                        "created_At": transaction.created_At,
                        "user_name": transaction.user_name,
                        'user_email': transaction.user_email,
                        "status": transaction.status
                    })


                return json({
                    'success': True,
                    'filter_exchange_data': combined_data,
                    'paginated_count': paginated_value

                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)



### Export Exchange Transaction
class AdminExportFiatExchangeTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Fiat Exchange Money Transactions'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/export/exchange/money/'
    

    ### Filter Exchange money
    @auth('userauth')
    @get()
    async def export_exchange_money(self, request: Request):
        """
            This function retrieves and exports exchange money transactions data with admin authentication.<br/><br/>

            Parameters:<br/>
                - `request`- It is used to handle incoming HTTP requests and contains information such as headers,
                            body, and query parameters. In this function, the `request` parameter is used to extract the
                            user's identity and make decisions.<br/><br/>
            
            Returns:<br/>
              The code is returning a JSON response with the following structure:<br/>
                - If the user making the request is not an admin, it returns a message indicating that only
                  admins can view the transactions with a status code of 400.<br/>
                - If the user making the request is an admin, it retrieves and exports the exchange money.<br/>
                - If there is no data found in the database, it returns a message indicating that no data was
                  found with a status code of 404.<br/>
                - If there is an error during the database operations, it returns a message indicating
                  a server error with a status code of 500.<br/>
            
            Raises:
            - Exception: If any error occurs during the database operations or processing.<br/>
            
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                AdminID       = user_identity.claims.get('user_id')

                 # Admin Authentication
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                # Admin authentication ends

                combined_data = []

                ## Select Rows
                stmt = select(
                    FIATExchangeMoney.id,
                    FIATExchangeMoney.from_currency,
                    FIATExchangeMoney.to_currency,
                    FIATExchangeMoney.exchange_amount,
                    FIATExchangeMoney.converted_amount,
                    FIATExchangeMoney.transaction_fee,
                    FIATExchangeMoney.created_At,
                    FIATExchangeMoney.is_completed,
                    FIATExchangeMoney.user_id,
                    FIATExchangeMoney.status,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    Users, Users.id == FIATExchangeMoney.user_id
                ).order_by(
                    desc(FIATExchangeMoney.id)
                )

                ## Execute Query
                fiat_exchange_money_obj = await session.execute(stmt)
                fiat_exchange_money     = fiat_exchange_money_obj.fetchall()

                if not fiat_exchange_money:
                    return json({'message': 'No data found'}, 404)
                
                ### Gather all the data
                for transaction in fiat_exchange_money:
                    # From Currency
                    from_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.from_currency
                    ))
                    from_currency = from_currency_obj.scalar()

                    # To Currency
                    to_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == transaction.to_currency
                    ))
                    to_currency = to_currency_obj.scalar()

                    combined_data.append({
                        "user_name": transaction.user_name,
                        'user_email': transaction.user_email,
                        "from_currency": from_currency.name,
                        "to_currency": to_currency.name,
                        "converted_amount": transaction.converted_amount,
                        "exchange_amount": transaction.exchange_amount,
                        "transaction_fee": transaction.transaction_fee,
                        "created_At": transaction.created_At,
                        "status": transaction.status
                    })

                return json({
                    'success': True,
                    'export_exchange_money_data': combined_data
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)

