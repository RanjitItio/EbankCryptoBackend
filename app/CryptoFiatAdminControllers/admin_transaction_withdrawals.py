from app.controllers.controllers import get, put, post
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.models import Users, Currency, Wallet
from Models.models4 import FiatWithdrawalTransaction
from Models.Admin.FiatWithdrawal.schema import UpdateFiatWithdrawalsSchema, AdminFIATWithdrawalFilterSchema
from decouple import config
from app.dateFormat import get_date_range
from datetime import datetime, timedelta




currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')



## FIAT Withdrawal controller
class AdminAllWithdrawalTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "All Withdrawals"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/fiat/withdrawals/'
    

    # Get all Fiat withdrawal requests
    @auth('userauth')
    @get()
    async def get_all_user_withdrawals(self, request: Request, limit: int = 10, offset: int = 0):
        """
            Get all user fiat withdrawal requests.<br/><br/>
        
            Parameters:<br/>
            request (Request): The request object containing user identity and other information.<br/>
            limit (int, optional): The number of withdrawals to retrieve per page. Default is 10.<br/>
            offset (int, optional): The starting index for retrieving withdrawals. Default is 0.<br/><br/>
        
            Returns:<br/>
            json: A JSON response containing the success status, all fiat withdrawals, and total row count.<br/>
            If any error occurs, a JSON response with error status and error message is returned.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                combined_data = []

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                row_statement     = select(func.count(FiatWithdrawalTransaction.id))
                exe_row_statement = await session.execute(row_statement)
                withdrawal_rows   = exe_row_statement.scalar()

                total_withdrawal_rows = withdrawal_rows / limit

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

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                )

                # Get the withdrdrawlas
                withdrawals_obj      = await session.execute(stmt)
                all_fiat_withdrawals = withdrawals_obj.all()

                if not all_fiat_withdrawals:
                    return json({'message': 'No Withdrawal found'}, 404)
                
                # Store all the data inside a combined_data list
                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'user_name': withdrawals.user_name,
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
                        'all_admin_fiat_withdrawals': combined_data,
                        'total_row_count': total_withdrawal_rows
                    }, 200)


        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


    # Get FIAT Withdrawal Details
    @auth('userauth')
    @post()
    async def get__fiat_withdrawals_details(self, request: Request, id: int):
        """
            This function retrieves detailed information about a specific FIAT withdrawal transaction.<br/><br/>

            Parameters:<br/>
             - request (Request): The request object containing identity and other relevant information.<br/>
             - id (int): The unique identifier of the FIAT withdrawal transaction.<br/><br/>

            Returns:<br/>
             - JSON response containing the withdrawal details or an error message in case of failure.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                combined_data = []
                withdrawal_id = id

                # Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                # Select the withdrawal table
                stmt = select(
                    FiatWithdrawalTransaction.id,
                    FiatWithdrawalTransaction.user_id,
                    FiatWithdrawalTransaction.transaction_id,
                    FiatWithdrawalTransaction.amount,
                    FiatWithdrawalTransaction.total_amount,
                    FiatWithdrawalTransaction.transaction_fee,
                    FiatWithdrawalTransaction.withdrawal_currency,
                    FiatWithdrawalTransaction.wallet_currency,
                    FiatWithdrawalTransaction.status,
                    FiatWithdrawalTransaction.debit_currency,
                    FiatWithdrawalTransaction.is_completed,
                    FiatWithdrawalTransaction.created_At,
                    FiatWithdrawalTransaction.credit_amount,
                    FiatWithdrawalTransaction.credit_currency,

                    Currency.name.label('wallet_currency_name'),

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).where(
                    FiatWithdrawalTransaction.id == withdrawal_id
                )

                # Get the withdrdrawlas
                withdrawal_obj  = await session.execute(stmt)
                fiat_withdrawal = withdrawal_obj.first()

                # Get the wallet of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == fiat_withdrawal.wallet_currency,
                        Wallet.user_id     == fiat_withdrawal.user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User do not have any existing wallet'}, 400)
                
                # Withdrawal Currency
                wallet_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == fiat_withdrawal.wallet_currency
                ))
                wallet_currency = wallet_currency_obj.scalar()

                combined_data.append({
                    'id': fiat_withdrawal.id,
                    'user_name': fiat_withdrawal.user_name,
                    'user_email': fiat_withdrawal.user_email,
                    'wallet_currency': fiat_withdrawal.wallet_currency_name,
                    'wallet_balance': user_wallet.balance,
                    'transaction_id': fiat_withdrawal.transaction_id,
                    'withdrawal_amount': fiat_withdrawal.amount,
                    'withdrawal_currency': wallet_currency.name,
                    'withdrawal_fee': fiat_withdrawal.transaction_fee,
                    'total_amount': fiat_withdrawal.total_amount,
                    'status': fiat_withdrawal.status,
                    'created_At': fiat_withdrawal.created_At,
                    'credit_amount': fiat_withdrawal.credit_amount if fiat_withdrawal.credit_amount else None,
                    'credit_currency': fiat_withdrawal.credit_currency if fiat_withdrawal.credit_currency else None
                })

                return json({
                    'success': True,
                    'withdrawal_data': combined_data
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    # Update FIAT Withdrawal
    @auth('userauth')
    @put()
    async def update_fiat_withdrawals(self, request: Request, schema: UpdateFiatWithdrawalsSchema):
        """
            This function is responsible for updating the status of a fiat withdrawal transaction.<br/>
            It checks the admin authentication, validates the withdrawal request, deducts the amount from the user's wallet,<br/>
            and updates the transaction status.<br/><br/>

            Parameters:<br/>
            - request (Request): The request object containing the user's identity and payload data.<br/>
            - schema (UpdateFiatWithdrawalsSchema): The schema object containing the withdrawal_id and status.<br/><br/>
        
            Returns:<br/>
            - JSON response with success or error message, along with HTTP status code.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                # Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                # Get the payload data
                withdrawal_id    = schema.withdrawal_id
                status           = schema.status

                # Get the withdrawal object
                user_fiat_withdrawal_obj = await session.execute(select(FiatWithdrawalTransaction).where(
                    FiatWithdrawalTransaction.id == withdrawal_id
                ))
                user_fiat_withdrawal = user_fiat_withdrawal_obj.scalar()

                if not user_fiat_withdrawal:
                    return json({'message': 'Invalid Withdrawal Request'}, 400)
                
                ## If already approved
                if user_fiat_withdrawal.is_completed:
                    return json({'message': 'Transaction Already Approved can not perform this action'}, 400)
                

                # Get the wallet of the user
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.currency_id == user_fiat_withdrawal.wallet_currency,
                        Wallet.user_id     == user_fiat_withdrawal.user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User do not have any existing wallet'}, 400)

                ## Wallet balance validation
                if user_wallet.balance < user_fiat_withdrawal.total_amount:
                    return json({'message': 'Do not have sufficient balance in wallet'}, 400)
                
                ## Approved status
                if status == 'Approved':
                    total_withdrawal_amount = user_fiat_withdrawal.amount + user_fiat_withdrawal.transaction_fee

                    # Deduct the amount
                    user_wallet.balance -= total_withdrawal_amount

                    # user Wallet currency Name
                    wallet_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == user_wallet.currency_id
                    ))
                    wallet_currency = wallet_currency_obj.scalar()

                    user_fiat_withdrawal.debit_currency  = wallet_currency.name
                    user_fiat_withdrawal.status          = 'Approved'
                    user_fiat_withdrawal.is_completed    = True

                    session.add(user_wallet)
                    session.add(user_fiat_withdrawal)
                    await session.commit()
                    await session.refresh(user_wallet)
                    await session.refresh(user_fiat_withdrawal)

                    return json({
                        'success': True,
                        'message': 'Updated Successfully'
                    }, 200)

                else:
                    user_fiat_withdrawal.status       = status
                    user_fiat_withdrawal.is_completed = False

                    session.add(user_fiat_withdrawal)
                    await session.commit()
                    await session.refresh(user_fiat_withdrawal)

                    return json({
                        'success': True,
                        'message': 'Updated Successfully'
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)





### Filter fiat withdrawal by Admin
class AdminFilterFiatWithdrawal(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Fliter FIAT Withdrawal'
    
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/filter/fiat/withdrawal/'
    
    
    @auth('userauth')
    @post()
    async def filter_fiat_withdrawal(self, request: Request, schema: AdminFIATWithdrawalFilterSchema, limit: int = 10, offset: int = 0):
        """
            This function filters fiat withdrawal transactions based on various criteria such as date,
            email, currency, and status, and returns paginated results along with relevant information.<br/><br/>
            
            Parameters:<br/>
            - request: The HTTP request object containing the payload data.<br/>
            - schema(AdminFIATWithdrawalFilterSchema): The schema object containing the filter parameters.<br/>
            - limit: The maximum number of results to return per query. Defaults to 10.<br/>
            - offset: The number of records to skip before starting to return records. Defaults to 0.<br/><br/>
            
            Returns:<br/>
              JSON: A JSON response containing the following keys and values:<br/>
            -'success': True if the operation was successful.<br/>
            - 'all_admin_fiat_filter_withdrawals': A list of dictionaries containing details of filtered
               fiat withdrawal transactions.<br/>
            - 'paginated_count': The paginated value calculated based on the number of withdrawal
               transactions and the specified limit.<br/><br/>
            
            Raises:<br/>
            - HTTPException: If the request payload is invalid or if the admin is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                ## Get payload data
                date_time = schema.date_time
                email     = schema.email
                currency  = schema.currency
                status    = schema.status
                startDate = schema.start_date
                endDate   = schema.end_date

                conditions    = []
                combined_data = []
                paginated_value = 0

                ### Email Validation
                if email:
                    # Get the user
                    fiat_user_obj = await session.execute(select(Users).where(
                         Users.email.like(f"{email}%") 
                    ))
                    fiat_user = fiat_user_obj.scalar()

                    if not fiat_user:
                         return json({'message': 'Invalid Email'}, 400)
                
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

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )


                ## Filter datetime wise
                if date_time and date_time == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            FiatWithdrawalTransaction.created_At < (end_date + timedelta(days=1)),
                            FiatWithdrawalTransaction.created_At >= start_date
                        )
                    )

                elif date_time:
                    start_date, end_date = get_date_range(date_time)

                    conditions.append(
                        and_(
                            FiatWithdrawalTransaction.created_At <= end_date,
                            FiatWithdrawalTransaction.created_At >= start_date
                        )
                    )

                ## Filter mail wise
                if email:
                    conditions.append(
                        FiatWithdrawalTransaction.user_id == fiat_user.id
                    )
                
                ## Filter amount wise
                if currency:
                    filter_currency_obj = await session.execute(select(Currency).where(
                        Currency.name.ilike(f"{currency}%")
                    ))
                    filter_currency = filter_currency_obj.scalar()

                    conditions.append(
                        FiatWithdrawalTransaction.wallet_currency == filter_currency.id
                    )
                
                ### Filter Status wise
                if status:
                    conditions.append(
                        FiatWithdrawalTransaction.status.ilike(f"{status}%")
                    )
                

                if conditions:
                    statement = stmt.where(and_(*conditions))
                    # Get the withdrdrawlas

                    withdrawals_obj      = await session.execute(statement)
                    all_fiat_withdrawals = withdrawals_obj.all()

                    ### Count Paginated Value
                    count_withdrawal_transaction_stmt = select(func.count()).select_from(FiatWithdrawalTransaction).where(
                        *conditions
                    )
                    withdrawal_transaction_count = (await session.execute(count_withdrawal_transaction_stmt)).scalar()

                    paginated_value = withdrawal_transaction_count / limit


                    if not all_fiat_withdrawals:
                        return json({'message': 'No Withdrawal found'}, 404)
                
                else:
                    return json({'message': 'No Withdrawal found'}, 404)
                
                
                ### Withdrawal Requests
                for withdrawals in all_fiat_withdrawals:
                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'user_id': withdrawals.user_id,
                        'user_email': withdrawals.user_email,
                        'user_name': withdrawals.user_name,
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
                    'all_admin_fiat_filter_withdrawals': combined_data,
                    'paginated_count': paginated_value

                }, 200)


        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
                }, 500)
        



### Export all Fiat Withdrawal Transactions
class AdminExportFIATWithdrawal(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Fiat Withdrawal Transactions'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/export/fiat/withdrawal/'
    

    ## Export all withdrawal data
    @auth('userauth')
    @get()
    async def export_fiat_withdrawals(self, request: Request):
        """
            This function exports fiat withdrawals data for admin users after authentication.<br/><br/>

            Parameters:<br/>
            - request (Request): The HTTP request object containing identity and other relevant information.<br/><br/>

            Returns:<br/>
            - JSON: A JSON response containing the success status and the exported fiat withdrawals data (export_admin_fiat_withdrawals).<br/><br/>

            Raises:<br/>
                - BlackSheepException: If the request is not authorized or if there is an error with the database.<br/>
                - Exception: If there is an error with the database.<br/>
                - Exception: If there is an error with the API request.<br/>
                - Exception: If there is an error with the API response.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                combined_data = []

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

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

                    Users.email.label('user_email'),
                    Users.full_name.label('user_name')
                ).join(
                    Currency, Currency.id == FiatWithdrawalTransaction.wallet_currency
                ).join(
                    Users, Users.id == FiatWithdrawalTransaction.user_id
                ).order_by(
                    desc(FiatWithdrawalTransaction.id)
                )

                # Get the withdrdrawlas
                withdrawals_obj      = await session.execute(stmt)
                all_fiat_withdrawals = withdrawals_obj.all()

                if not all_fiat_withdrawals:
                    return json({'message': 'No Withdrawal found'}, 404)
                
                # Store all the data inside a combined_data list
                for withdrawals in all_fiat_withdrawals:

                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.withdrawal_currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    combined_data.append({
                        'user_email': withdrawals.user_email,
                        'user_name': withdrawals.user_name,
                        'transaction_id': withdrawals.transaction_id,
                        'amount': withdrawals.amount,
                        'transaction_fee': withdrawals.transaction_fee,
                        'total_amount': withdrawals.total_amount,
                        'withdrawal_currency': withdrawal_currency.name,
                        'wallet_currency': withdrawals.wallet_currency,
                        'status': withdrawals.status,
                        'credit_amount': withdrawals.credit_amount,
                        'credit_currency': withdrawals.credit_currency,
                        'created_At': withdrawals.created_At
                    })

                return json({
                        'success': True,
                        'export_admin_fiat_withdrawals': combined_data
                    }, 200)
            

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
