from app.controllers.controllers import get, post
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.PG.schema import FiatUserWithdrawalSchema, UserFilterFIATWithdrawalSchema
from Models.models4 import FiatWithdrawalTransaction
from Models.models import Wallet, Currency, Users
from datetime import datetime, timedelta
from app.dateFormat import get_date_range
import uuid



## Raise Withdrawal Request by User
class UserFiatWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Fiat Withdrawal'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/user/fiat/withdrawal/'
    
    # Raise Withdrawal Request by User
    @auth('userauth')
    @post()
    async def withdrawal_fiat_amount(self, request: Request, schema: FiatUserWithdrawalSchema):
        """
            This API Endpoint is responsible for creating withdrawal requests for users.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing the user's identity and payload data.<br/>
                - schema (FiatUserWithdrawalSchema): The schema object containing the wallet_currency, withdrawalCurrency, withdrawalAmount, fee, and converted_credit_amt.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, message, or error details.<br/>
                - HTTP Status Code: 200 if successful, 400 if invalid request data, or 500 if an error occurs.<br/><br/>

            Error Messages:<br/>
                - Error Response status code 400: "message": "Suspended User"<br/>
                - Error Response status code 400: "message": "Invalid Wallet Currency"<br/>
                - Error Response status code 400: "message": "User wallet does not exists"<br/>
                - Error Response status code 400: "message": "Do not have Sufficient balance in Wallet"<br/>
                - Error Response status code 400: "message": "Invalid withdrawal Currency"<br/>
                - Error Response status code 400: "message": "Server Error"<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get The payload data
                walletCurrency     = schema.wallet_currency
                withdrawalCurrency = schema.withdrawalCurrency
                withdrawalAmount   = float(schema.withdrawalAmount)
                withdrawalFee      = float(schema.fee)
                creditedAmount     = float(schema.converted_credit_amt)

                ## Get The user 
                fiat_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                fiat_user = fiat_user_obj.scalar()

                ## If user has been suspended
                if fiat_user.is_suspended:
                    return json({'message': 'Suspended User'}, 400)
                

                # Get wallet Currency
                wallet_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == walletCurrency
                ))
                wallet_currency_ = wallet_currency_obj.scalar()

                if not wallet_currency_:
                    return json({'message': 'Invalid Wallet Currency'}, 400)
                
                # Get the wall                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            et of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.user_id == user_id,
                        Wallet.currency_id == wallet_currency_.id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User wallet does not exists'}, 400)
                
                ## Total amount to deduct
                total_amt = withdrawalAmount + withdrawalFee

                # Account balance check
                if total_amt > user_wallet.balance:
                    return json({'message': 'Do not have Sufficient balance in Wallet'}, 400)
                

                # Get the withdrawal Currency
                withdrawal_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == withdrawalCurrency
                ))
                withdrawal_currency_ = withdrawal_currency_obj.scalar()

                if not withdrawal_currency_:
                    return json({'message': 'Invalid withdrawal Currency'}, 400)
                

                # Create a Withdrawal Request
                withdrawal_request = FiatWithdrawalTransaction(
                    user_id             = user_id,
                    transaction_id      = str(uuid.uuid4()),
                    amount              = withdrawalAmount,
                    total_amount        = total_amt,
                    transaction_fee     = withdrawalFee,
                    wallet_currency     = wallet_currency_.id,
                    withdrawal_currency = withdrawal_currency_.id,
                    status              = 'Pending',
                    debit_currency      = wallet_currency_.name,
                    credit_currency     = withdrawal_currency_.name,
                    credit_amount       = creditedAmount,
                )

                session.add(withdrawal_request)
                await session.commit()
                await session.refresh(withdrawal_request)

                return json({'success': True, 'message': 'Withdrawak Request Raised Successfully'}, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
    
    # Get all withdrawals of Merchant
    @auth('userauth')
    @get()
    async def get_all_fiat_withdrawal(self, request: Request, limit: int = 10, offset: int = 0):
        """
            This API Endpoint will return all fiat withdrawal requests of users.
            <br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing the user's identity and pagination information.<br/>
                - limit (int): The number of rows to be returned per page. Default value is 10.<br/>
                - offset (int): The starting index of the rows to be returned. Default value is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, message, and withdrawal requests data.<br/>
                - HTTP Status Code: 200 if successful, 400 if invalid request data, or 500 if an error occurs.<br/><br/>

            Error Messages:<br/>
                - Error Response status code 400: "message": "No Withdrawal found"<br/>
                - Error Response status code 500: "error": "Server Error"<br/><br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                ## Count available rows of Fiat withdrawala
                select_rows    = select(func.count(FiatWithdrawalTransaction.id)).where(FiatWithdrawalTransaction.user_id == user_id)
                exec_row_count = await session.execute(select_rows)
                available_rows = exec_row_count.scalar()

                total_row_count = available_rows / limit

                # Select the withdrawal table
                stmt = select(
                    FiatWithdrawalTransaction.id,
                    FiatWithdrawalTransaction.user_id,
                    FiatWithdrawalTransaction.transaction_id,
                    FiatWithdrawalTransaction.amount,
                    FiatWithdrawalTransaction.total_amount,
                    FiatWithdrawalTransaction.transaction_fee,
                    FiatWithdrawalTransaction.withdrawal_currency,
                    FiatWithdrawalTransaction.status,
                    FiatWithdrawalTransaction.debit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,
                    FiatWithdrawalTransaction.credit_amount,
                    FiatWithdrawalTransaction.credit_currency,

                    Currency.name.label('wallet_currency'),

                    Users.email.label('user_email')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).where(
                    FiatWithdrawalTransaction.user_id == user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                )

                # Get the withdrdrawlas
                withdrawals_obj = await session.execute(stmt)
                all_fiat_withdrawals = withdrawals_obj.all()

                if not all_fiat_withdrawals:
                    return json({'message': 'No Withdrawal found'}, 404)


                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'transaction_id': withdrawals.transaction_id,
                        'amount': withdrawals.amount,
                        'total_amount': withdrawals.total_amount,
                        'transaction_fee': withdrawals.transaction_fee,
                        'withdrawal_currency': withdrawal_currency.name,
                        'wallet_currency': withdrawals.wallet_currency,
                        'status': withdrawals.status,
                        'credit_amount': withdrawals.credit_amount,
                        'credit_currency': withdrawals.credit_currency,
                        'is_completed': withdrawals.is_completed,
                        'created_At': withdrawals.created_At
                    })

                return json({
                            'success': True,
                            'all_fiat_withdrawals': combined_data,
                            'total_row_count': total_row_count
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        




### Filter all FIAT Withdrawal
class UserFilterFiatWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter User FIAT Withdrawal Controller'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/user/filter/fiat/withdrawal/'
    

    ### Filter FIAT Withdrawal
    @auth('userauth')
    @post()
    async def filter_fiatWithdrawal(self, request: Request, schema: UserFilterFIATWithdrawalSchema, limit: int = 10, offset: int = 0):
        """
            This API Endpoint will filter Fiat withdrawals based on the specified schema.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing user identity and other information.<br/>
                - schema (UserFilterFIATWithdrawalSchema): The schema containing the filter criteria.<br/>
                - limit (int, optional): The number of withdrawals to retrieve per page. Default is 10.<br/>
                - offset (int, optional): The number of withdrawals to skip before starting to retrieve. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, a list of withdrawal data, and the total number of pages.<br/>
                - paginated_count (int): The total number of pages available for the filtered withdrawals.<br/>
                - user_filtered_fiat_withdrawal: All the filtered withdrawal data.<br/>
                - success - True if successful.<br/><br/>

            Error message:<br/>
               Error Response status code 404 - "message": "No data found"<br/>
               Error Response status code 500 - "error": "Server Error"<br/><br/>

            Raises:<br/>
                - ValueError: If the input data is not valid.<br/>
                - Exception: If there is an error while executing the SQL queries.<br/>
                - SqlAlchemyError: If there is an error while executing the SQL queries.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get payload data
                dateRange    = schema.dateRange
                fromCurrency = schema.fromCurrency
                toCurrency   = schema.toCurrency
                status       = schema.status
                startDate    = schema.start_date
                endDate      = schema.end_date

                conditions = []
                combined_data = []

                # Select the withdrawal table
                stmt = select(
                    FiatWithdrawalTransaction.id,
                    FiatWithdrawalTransaction.user_id,
                    FiatWithdrawalTransaction.transaction_id,
                    FiatWithdrawalTransaction.amount,
                    FiatWithdrawalTransaction.total_amount,
                    FiatWithdrawalTransaction.transaction_fee,
                    FiatWithdrawalTransaction.withdrawal_currency,
                    FiatWithdrawalTransaction.status,
                    FiatWithdrawalTransaction.debit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,
                    FiatWithdrawalTransaction.credit_amount,
                    FiatWithdrawalTransaction.credit_currency,

                    Currency.name.label('wallet_currency'),

                    Users.email.label('user_email')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).where(
                    FiatWithdrawalTransaction.user_id == user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )


                ### Filter Custom Date range wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            FiatWithdrawalTransaction.created_At >= start_date,
                            FiatWithdrawalTransaction.created_At < (end_date + timedelta(days=1))
                        )
                    )
                
                ### Filter Date Range wise
                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(
                            FiatWithdrawalTransaction.created_At <= end_date,
                            FiatWithdrawalTransaction.created_At >= start_date
                        )
                    )
                
                ## Filter amount wise
                if fromCurrency:
                    filter_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{fromCurrency}%")
                    ))
                    filter_currency = filter_currency_obj.scalar()

                    conditions.append(
                        FiatWithdrawalTransaction.wallet_currency == filter_currency.id
                    )

                ### Filter To Currency Wise
                if toCurrency:
                    filter_to_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{toCurrency}%")
                    ))
                    filter_to_currency = filter_to_currency_obj.scalar()

                    conditions.append(
                        FiatWithdrawalTransaction.withdrawal_currency == filter_to_currency.id
                    )
                
                ### Filter Status Wise
                if status:
                    conditions.append(
                        FiatWithdrawalTransaction.status.ilike(f"{status}%")
                    )
                

                ### If data found
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    # Get the withdrdrawlas

                    withdrawals_obj      = await session.execute(statement)
                    all_fiat_withdrawals = withdrawals_obj.fetchall()

                    if not all_fiat_withdrawals:
                        return json({'message': 'No data found'}, 404)
                
                else:
                    return json({'message': 'No data found'}, 404)
                
                ### Count total paginated value
                withdrawal_count_stmt =  select(func.count()).select_from(FiatWithdrawalTransaction).where(
                        FiatWithdrawalTransaction.user_id == user_id, *conditions
                    )
                withdrawal_count = (await session.execute(withdrawal_count_stmt)).scalar()

                paginated_value = withdrawal_count / limit


                ### Get all the data inside a List
                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'transaction_id': withdrawals.transaction_id,
                        'amount': withdrawals.amount,
                        'total_amount': withdrawals.total_amount,
                        'transaction_fee': withdrawals.transaction_fee,
                        'withdrawal_currency': withdrawal_currency.name,
                        'wallet_currency': withdrawals.wallet_currency,
                        'status': withdrawals.status,
                        'credit_amount': withdrawals.credit_amount,
                        'credit_currency': withdrawals.credit_currency,
                        'is_completed': withdrawals.is_completed,
                        'created_At': withdrawals.created_At
                    })
                
                return json({
                    'success': True,
                    'user_filtered_fiat_withdrawal': combined_data,
                    'paginated_count': paginated_value
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
    