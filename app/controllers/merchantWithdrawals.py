from blacksheep import Request, json, get as GET
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post
from database.db import AsyncSession, async_engine
from Models.models import MerchantBankAccount, Currency, Users
from Models.models3 import MerchantWithdrawals
from Models.models2 import MerchantAccountBalance
from Models.PG.schema import CreateMerchantWithdrawlSchma, FilterWithdrawalTransactionSchema
from sqlmodel import select, and_, desc, func
from datetime import timedelta, datetime
import calendar




# Merchant Withdrawals
class MerchantWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Withdrawal'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/withdrawal/'
    

    # Create new Withdrawal Request
    @auth('userauth')
    @post()
    async def create_merchantWithdrawal(self, request: Request, schema: CreateMerchantWithdrawlSchma):
        """
           This API Endpoint will create a new Withdrawal request for merchant.<br/><br/>

           Parameters:<br/><br/>
             - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
             - schema(CreateMerchantWithdrawlSchma): The schema object containing the bank_id, bank_currency_id, account_currency, withdrawal_amount.<br/><br/>

            Returns:<br/>
             - 'success': True, 'message': 'Withdrawal request raised successfully'<br/><br/>

            Raises:<br/>
              - HTTPException: If any validation error occurs.<br/>
              - HTTPStatus: 400 Bad Request if the payload data is invalid.<br/>
              - HTTPException 401: If the user is not authenticated.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Payload data
                merchantBank         = schema.bank_id  # To be deposited bank
                merchantBankCurrency = schema.bank_currency_id # To be deposited Currency
                accountCurrency      = schema.account_currency # From Account Balance currency
                withdrawalAmount     = schema.withdrawal_amount  # Withdrawal amount

                # Check the merchant bank account is exist and active or not
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    and_(
                          MerchantBankAccount.id         == merchantBank,
                          MerchantBankAccount.is_active == True,
                          MerchantBankAccount.currency  == merchantBankCurrency
                         )
                    ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                if not merchant_bank_account:
                    return json({'error': 'Bank account not active'}, 400)
                
                # Get The merchant
                merchant_user_obj = await session.execute(select(Users).where(
                    Users.id == merchant_bank_account.user
                ))
                merchant_user = merchant_user_obj.scalar()

                
                # If withdrawal amount is 0 or less than 10
                # if withdrawalAmount == 0 or withdrawalAmount < 10:
                #     return json({'error': 'Amount should be greater than 10'}, 400)
                
                # Get the merchant Account Balance
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(
                        MerchantAccountBalance.currency == accountCurrency,
                        MerchantAccountBalance.merchant_id == int(user_id)
                        )
                ))
                merchant_account_balance_ = merchant_account_balance_obj.scalar()

                if not merchant_account_balance_:
                    return json({'error': 'Do not have any active account in the currency'}, 400)
                
                # Withdrawal balance is lesser than Account balance or not
                merchant_account_balance = merchant_account_balance_.mature_balance
                
                if withdrawalAmount > merchant_account_balance:
                    return json({'error': 'Donot have sufficient balance in Account'}, 400)
                
                if withdrawalAmount < merchant_user.minimum_withdrawal_amount:
                    return json({'message': 'Withdrawal amount must be greater than minimum withdrawal amount'}, 400)
                
                # Currency
                account_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == accountCurrency
                ))
                account_currency = account_currency_obj.scalar()


                # Create a Withdrawal Request
                merchant_withdrawal_request = MerchantWithdrawals(
                    merchant_id      = user_id,
                    bank_id          = merchant_bank_account.id,
                    amount           = withdrawalAmount,
                    bank_currency    = merchantBankCurrency,
                    currency         = account_currency.id,
                    is_completed     = False
                )

                session.add(merchant_withdrawal_request)
                await session.commit()
                await session.refresh(merchant_withdrawal_request)

                return json({'success': True, 'message': 'Withdrawal request raised successfully'}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
 
    # Get all the withdrawals
    @auth('userauth')
    @get()
    async def get_merchantWithdrawals(self, request: Request, limit: int = 10, offset: int = 0):
        """
            This API Endpoint retrieve all the withdrawals raised by the merchant.<br/><br/>
            
            Parameters:<br/>
            request (Request): The request object containing user identity and other information.<br/>
            limit (int, optional): The number of withdrawals to retrieve per page. Default is 10.<br/>
            offset (int, optional): The number of withdrawals to skip before starting to retrieve. Default is 0.<br/><br/>
            
            Returns:<br/>
                JSON: A JSON response containing the success status, a list of withdrawal data(merchantWithdrawalRequests).<br/>
                total_row_count (int): The total number of withdrawals available for the merchant.<br/><br/>    
            
            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 404: 'error': 'error': 'No withdrawal request found' <br/>
            - Error 500: 'error': 'Server Error'.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate User
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id') if user_identity else None

                combined_data = []

                # Get all the Withdrawal request raise by the merchant
                merchantWithdrawalRequests = await session.execute(select(MerchantWithdrawals).where(
                    MerchantWithdrawals.merchant_id == user_id
                ).order_by(desc(MerchantWithdrawals.id)))
                merchantWithdrawal = merchantWithdrawalRequests.scalars().all()

                if not merchantWithdrawal:
                    return json({'error': 'No withdrawal request found'}, 404)
                
                # Count total Rows
                count_stmt            = select(func.count(MerchantWithdrawals.id)).where(MerchantWithdrawals.merchant_id == user_id)
                total_withdrawals_obj = await session.execute(count_stmt)
                total_withdrawal_rows = total_withdrawals_obj.scalar()

                total_withdrawal_rows_count = total_withdrawal_rows / limit


                for withdrawals in merchantWithdrawal:
                    # Get the bank account linked to the merchant
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.id == withdrawals.bank_id
                    ))
                    merchant_bank_account = merchant_bank_account_obj.scalar()

                    # Get the withdrawal currency and Bank Currecy
                    merchant_withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.currency
                    ))
                    merchant_withdrawal_currency = merchant_withdrawal_currency_obj.scalar()

                    # Get the merchant Bank Currency
                    merchant_bank_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.bank_currency
                    ))
                    merchant_bank_currency = merchant_bank_currency_obj.scalar()

                    # Get user Details
                    merchant_user_obj = await session.execute(select(Users).where(
                        Users.id == withdrawals.merchant_id
                    ))
                    merchant_user = merchant_user_obj.scalar()


                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': merchant_user.full_name,
                        'merchant_email': merchant_user.email,
                        'bank_account': merchant_bank_account.bank_name,
                        'bank_account_number': merchant_bank_account.acc_no,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_completed': withdrawals.is_completed
                    })

                return json({'success': True,'total_row_count': total_withdrawal_rows_count, 'merchantWithdrawalRequests': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



# Merchant Pending Withdrawals
class MerchantPendingWithdrawalController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Pending Withdrawals'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/pg/pending/withdrawal/'
    
    # Create new Withdrawal Request
    @auth('userauth')
    @get()
    async def get_merchantPendingWithdrawals(self, request: Request):
        """
            This API Endpoint retrieves pending withdrawal requests made by a merchant and returns the
            relevant data in JSON format.<br/><br/>
            
            Parameters:<br/>
                - request(Request): The HTTP Request object.<br/>
                - schema(CreateMerchantWithdrawlSchma): The schema object representing the input data expected in the request body.<br/><br/>

            Returns:<br/>
                - JSON response with success status and message, along with HTTP status code.<br/>
                - JSON response with error status and message, along with HTTP status code if any exceptions occur.<br/>
                - If there are no withdrawal requests found, it returns a message: {'message': 'No withdrawal
                    request found'} with status code 404.<br/>
                - If there are pending withdrawal requests for the merchant, it returns a success message along
                with the details of the pending withdrawals in the 'merchantPendingWithdrawals' key. The
                structure of the response.<br/><br/>

            Raises:<br/>
                - ValueError: If the request data is invalid.<br/>
                - Exception: If any other error occurs during the database query or response generation.<br/>
                - Exception: If any error occurs during the database query or response generation.<br/>
                - Error 404: 'message': 'No withdrawal request found'.<br/>
                - Error 500: 'error': 'Server Error'.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                combined_data = []

                # Get all the pending Withdrawal request raise by the merchant
                stmt = select(MerchantWithdrawals.id,
                              MerchantWithdrawals.bank_currency,
                              MerchantWithdrawals.merchant_id,
                              MerchantWithdrawals.amount,
                              MerchantWithdrawals.status,
                              MerchantWithdrawals.is_completed,
                              MerchantWithdrawals.createdAt,

                              MerchantBankAccount.bank_name,
                              Currency.name
                              ).join(
                                  MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                              ).join(
                                  Currency, Currency.id == MerchantWithdrawals.currency
                              )
                merchantWithdrawalRequests = await session.execute(stmt.where(
                    and_(
                        MerchantWithdrawals.merchant_id == user_id,
                         MerchantWithdrawals.status == 'Pending'
                         )
                ).order_by(desc(MerchantWithdrawals.id)))

                merchantWithdrawal = merchantWithdrawalRequests.all()

                if not merchantWithdrawal:
                    return json({'message': 'No withdrawal request found'}, 404)
                
                for withdrawals in merchantWithdrawal:

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': withdrawals.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_completed': withdrawals.is_completed
                    })

                return json({'success': True, 'merchantPendingWithdrawals': combined_data}, 200)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



# Export all the merchant withdrawal transactions
@auth('userauth')
@GET('/api/v3/merchant/export/withdrawals/')
async def ExportWithDrawals(request: Request):
    """
        This API endpoint exports all the merchant withdrawal transactions by an authenticated user.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object containing identity and other relevant information.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the success status and the exported withdrawals data.<br/>
            - JSON: A JSON response containing error status and error message if any.<br/><br/>

        Raises:<br/>
            - SqlAlchemyError: If there was an error while executing sql query.<br/>
            - BadRequest: If there was an error in input data.<br/>
            - Exception: If there is an error while executing the SQL queries.<br/>
            - Error 500: 'error': 'Server Error' if any error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access' if the user is not authenticated.<br/>
            - Error 400: 'error': 'Bad Request' if there was an error in input data.<br/><br/>

        Error Message:<br/>
            - 'error': 'No withdrawal request found' if no withdrawal request found by the merchant.<br/>
            - 'error': 'Server Error' if any error occurs during the database query or response generation.<br/>
            -  Error 500: 'error': 'Server Error' if any error occurs during the database query or response generation.<br/>
            -  Error 401: 'error': 'Unauthorized Access' if the user is not authenticated.<br/>
            -  Error 400: 'error': 'Bad Request' if there was an error in input data.<br/>
    """
    
    user_identity = request.identity
    user_id       = user_identity.claims.get('user_id')

    try:
        async with AsyncSession(async_engine) as session:

            # Get all the Withdrawal request raise by the merchant
            merchantWithdrawalRequests = await session.execute(select(MerchantWithdrawals).where(
                MerchantWithdrawals.merchant_id == user_id
            ).order_by(desc(MerchantWithdrawals.id)))
            merchantWithdrawal = merchantWithdrawalRequests.scalars().all()

            if not merchantWithdrawal:
                return json({'error': 'No withdrawal request found'}, 404)
            
            combined_data = []


            for withdrawals in merchantWithdrawal:
                # Get the bank account linked to the merchant
                merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                    MerchantBankAccount.id == withdrawals.bank_id
                ))
                merchant_bank_account = merchant_bank_account_obj.scalar()

                # Get the withdrawal currency and Bank Currecy
                merchant_withdrawal_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == withdrawals.currency
                ))
                merchant_withdrawal_currency = merchant_withdrawal_currency_obj.scalar()

                # Get the merchant Bank Currency
                merchant_bank_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == withdrawals.bank_currency
                ))
                merchant_bank_currency = merchant_bank_currency_obj.scalar()

                # Get user Details
                merchant_user_obj = await session.execute(select(Users).where(
                    Users.id == withdrawals.merchant_id
                ))
                merchant_user = merchant_user_obj.scalar()


                combined_data.append({
                    'merchant_name': merchant_user.full_name,
                    'merchant_email': merchant_user.email,
                    'bank_account': merchant_bank_account.bank_name,
                    'bank_account_number': merchant_bank_account.acc_no,
                    'bankCurrency': merchant_bank_currency.name,
                    'withdrawalAmount': withdrawals.amount,
                    'withdrawalCurrency': merchant_withdrawal_currency.name,
                    'time': withdrawals.createdAt,
                    'status':   withdrawals.status,
                })

            return json({'success': True,'ExportmerchantWithdrawalRequests': combined_data}, 200)
                        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


# Filter Merchant Withdrawals
class FilterMerchantWithdrawalsController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter Merchant Withdrawals'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/filter/merchant/pg/withdrawals/'
    

    # Convert text to datetime format
    @staticmethod
    def get_date_range(currenct_time_date: str):
        now = datetime.now()

        if currenct_time_date == 'Today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif currenct_time_date == 'Yesterday':
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
        elif currenct_time_date == 'ThisWeek':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif currenct_time_date == 'ThisMonth':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif currenct_time_date == 'PreviousMonth':
            first_day_last_month = (now.replace(day=1) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = first_day_last_month.replace(day=1)
            end_date = first_day_last_month.replace(day=calendar.monthrange(first_day_last_month.year, first_day_last_month.month)[1], hour=23, minute=59, second=59)
        else:
            raise ValueError(f"Unsupported date range: {currenct_time_date}")
        
        return start_date, end_date
    

    @auth('userauth')
    @post()
    async def filter_merchant_withdrawals(self, request: Request, schema: FilterWithdrawalTransactionSchema, limit: int = 10, offset: int = 0):
        """
            This function filters merchant withdrawals based on various criteria and returns paginated
            results along with relevant details.<br/>
            Note: The input dates should be in 'YYYY-MM-DD' format.<br/><br/>

            Parameters:<br/>
                - request (Request): The HTTP request object containing the payload data.<br/>
                - schema (FilterWithdrawalTransactionSchema): The schema object containing the validated
                  payload data.<br/>
                - limit (int): The maximum number of withdrawal transactions to retrieve in a single request.<br/>
                - offset (int): The offset for pagination. It determines the starting point from where the
                  results should be returned. Defaults to 0.<br/><br/>

            Returns:<br/>
                - JSON response: A JSON object containing the following keys:<br/>
                - 'paginated_count': The paginated value calculated based on the number of withdrawal
                   transactions and the limit<br/>
                - for successful responses retruns 'success': True and 'merchantWithdrawalRequests': A list of dictionaries containing details of merchant
                   withdrawal transactions.<br/>
                - 'error': A string containing an error message if the request fails.<br/><br/>

            Raises:<br/>
                - Exception: If any error occurs during the database query or response generation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                # Get the payload Data
                date_time           = schema.date
                bankName            = schema.bank_name
                withdrawal_currency = schema.withdrawal_currency
                withdrawal_amount   = schema.withdrawal_amount
                startDate           = schema.start_date
                endDate             = schema.end_date

                conditions  = []
                paginated_value = 0

                # Select the table
                stmt = select(
                    MerchantWithdrawals
                ).where(
                    MerchantWithdrawals.merchant_id == user_id
                ).order_by(
                    desc(MerchantWithdrawals.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                # Filter date wise
                if date_time and date_time == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            MerchantWithdrawals.createdAt >= start_date,
                            MerchantWithdrawals.createdAt < (end_date + timedelta(days=1))
                        ))

                elif date_time:
                    start_date, end_date = self.get_date_range(date_time)

                    conditions.append(
                        and_(
                            MerchantWithdrawals.createdAt   >= start_date,
                            MerchantWithdrawals.createdAt   <= end_date,
                        )
                    )

                
                # Filter bank name wise
                if bankName:
                    bankName = schema.bank_name.capitalize()

                    # Get The merchant bank Account
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        and_(
                                MerchantBankAccount.bank_name.like(f"{bankName}%")
                            )
                    ))
                    merchant_bank_account  = merchant_bank_account_obj.scalar()

                    if not merchant_bank_account:
                        return json({'message': 'Invalid Bank Name'}, 400)
                    
                    conditions.append(
                        and_(
                            MerchantWithdrawals.bank_id     == merchant_bank_account.id
                        )
                    )

                # Filter Withdrawal currency wise
                if withdrawal_currency:

                    # Get the currency ID
                    currency_obj = await session.execute(select(Currency).where(
                        Currency.name.like(f"{withdrawal_currency}%")
                    ))
                    currency = currency_obj.scalar()

                    if not currency:
                        return json({'message': 'Invalid Currency'}, 400)

                    conditions.append(
                        and_(
                            MerchantWithdrawals.currency == currency.id
                            )
                        )
                
                # Filter Withdrawal amount wise
                if withdrawal_amount:
                    withdrawal_amount = float(schema.withdrawal_amount)

                    conditions.append(
                        and_(
                            MerchantWithdrawals.amount == withdrawal_amount
                            )
                        )
                
                # If data is available
                if conditions:
                    statement = stmt.where(and_(*conditions))

                    merchant_withdrawal_transaction_obj = await session.execute(statement)
                    merchant_withdrawal_transaction     = merchant_withdrawal_transaction_obj.scalars().all()

                     ### Count paginated value
                    count_withdrawal_stmt = select(func.count()).select_from(MerchantWithdrawals).where(
                            *conditions
                    )
                    withdrawal_count = (await session.execute(count_withdrawal_stmt)).scalar()

                    paginated_value = withdrawal_count / limit

                    if not merchant_withdrawal_transaction:
                        return json({'error': 'No withdrawal request found'}, 404)
                    
                else:
                    return json({'error': 'No withdrawal request found'}, 400)
                
                # Store all the data inside a list
                for withdrawals in merchant_withdrawal_transaction:
                    # Get the bank account linked to the merchant
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.id == withdrawals.bank_id
                    ))
                    merchant_bank_account = merchant_bank_account_obj.scalar()

                    # Get the withdrawal currency and Bank Currecy
                    merchant_withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.currency
                    ))
                    merchant_withdrawal_currency = merchant_withdrawal_currency_obj.scalar()

                    # Get the merchant Bank Currency
                    merchant_bank_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.bank_currency
                    ))
                    merchant_bank_currency = merchant_bank_currency_obj.scalar()

                    # Get user Details
                    merchant_user_obj = await session.execute(select(Users).where(
                        Users.id == withdrawals.merchant_id
                    ))
                    merchant_user = merchant_user_obj.scalar()


                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': merchant_user.full_name,
                        'merchant_email': merchant_user.email,
                        'bank_account': merchant_bank_account.bank_name,
                        'bank_account_number': merchant_bank_account.acc_no,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_completed': withdrawals.is_completed
                    })

                return json({
                    'success': True,
                    'merchantWithdrawalRequests': combined_data,
                    'paginated_count': paginated_value
                    
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)