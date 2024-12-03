from blacksheep import Request, json, get, put, post
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantWithdrawals
from Models.models import MerchantBankAccount, Users, Currency
from Models.models2 import MerchantAccountBalance
from Models.Admin.PG.schema import AdminWithdrawalUpdateSchema
from sqlmodel import select, and_, or_, cast, Date, Time, func, desc
from datetime import datetime, timedelta
from Models.Admin.PG.schema import FilterMerchantWithdrawalsSchema
from app.dateFormat import get_date_range



# Get all merchant withdrawals
@auth('userauth')
@get('/api/v4/admin/merchant/pg/withdrawals/')
async def AdminMerchantWithdrawalRequests(request: Request, limit: int = 10, offset: int = 0):
    """
        This API Endpoint will retrieve all the merchant withdrawal requests.
        <br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object.<br/>
            - limit (int): The number of rows to be returned. Default is 10.<br/>
            - offset (int): The offset of the rows to be returned. Default is 0.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the AdminMerchantWithdrawalRequests, success, and the total_row_count.<br/>
            - HTTP Status Code: 200 if successful, 401 if unauthorized, or 500 if an error occurs. <br/><br/>

        Error message:<br/>
            - Unauthorized Access: If the user is not authorized to access the endpoint.<br/>
            - Server Error: If an error occurs while executing the database query.<br/><br/>
        
        Raises:<br/>
           - Exception: If any other unexpected error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            if not is_admin_user:
                return json({'error': 'Admin authentication failed'}, 401)
            # Admin authentication Ends

            # Get all the merchant withdrawals
            stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_completed,

                          MerchantBankAccount.bank_name,

                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          ).order_by(
                               desc(MerchantWithdrawals.id)
                         ).limit(
                              limit
                         ).offset(
                              offset
                         )
          
            merchant_withdrawals_object = await session.execute(stmt)
            merchant_withdrawals        = merchant_withdrawals_object.all()

            if not merchant_withdrawals:
                 return json({'error': 'No withdrawal request found'}, 404)
            
            # Count total rows in the table
            count_stmt = select(func.count(MerchantWithdrawals.id))
            total_withdrawals_obj = await session.execute(count_stmt)
            total_withdrawal_rows = total_withdrawals_obj.scalar()

            total_withdrawal_row_count = total_withdrawal_rows / limit

            for withdrawals in merchant_withdrawals:
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

               # Get merchant account balance
               merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(MerchantAccountBalance.merchant_id == withdrawals.merchant_id,
                         MerchantAccountBalance.currency    == merchant_withdrawal_currency.name
                         )
               ))
               merchant_account_balance_ = merchant_account_balance_obj.scalar()

               combined_data.append({
                    'id': withdrawals.id,
                    'merchant_id': withdrawals.merchant_id,
                    'merchant_name': withdrawals.full_name,
                    'merchant_email': withdrawals.email,
                    'bank_account': withdrawals.bank_name,
                    'bankCurrency': merchant_bank_currency.name,
                    'withdrawalAmount': withdrawals.amount,
                    'withdrawalCurrency': merchant_withdrawal_currency.name,
                    'createdAt': withdrawals.createdAt,
                    'status':   withdrawals.status,
                    'is_completed': withdrawals.is_completed,
                    'account_balance': merchant_account_balance_.mature_balance if merchant_account_balance_ else None,
                    'account_currency': merchant_account_balance_.currency if merchant_account_balance_ else None
               })

            return json({
                    'success': True, 
                    'AdminMerchantWithdrawalRequests': combined_data,
                    'total_row_count': total_withdrawal_row_count
                    }, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Update Merchant withdrawals by Admin
@auth('userauth')
@put('/api/v4/admin/merchant/withdrawal/update/')
async def MerchantWithdrawalTransactionUpdate(request: Request, schema: AdminWithdrawalUpdateSchema):
     """
          This endpoint allows an admin to update the status of a specific withdrawal request. <br/>
          The admin must be authenticated and have the necessary permissions.<br/><br/>

          Parameters:<br/>
               - request (Request): The HTTP request object.<br/>
               - schema (AdminWithdrawalUpdateSchema): The schema for validating the request payload.<br/><br/>

          Returns:<br/>
               - JSON: A JSON response containing the updated status, success, and the withdrawal request details.<br/>
               - HTTP Status Code: 200 if successful, 401 if unauthorized, 400 if invalid payload, or 500 if an error occurs. <br/><br/>

          Error message:<br/>
               - Unauthorized Access: If the user is not authorized to access the endpoint.<br/>
               - 'message': 'No Withdrawal request found with given information'<br/>
               - 'message': 'Already updated, Can not perform this action'<br/>
               - 'message': 'Insufficient balance to withdrawal'<br/>
               - 'Server Error': If an error occurs while executing the database query.<br/><br/>

          Raises:<br/>
               - Exception: If any other unexpected error occurs during the database query or response generation.<br/>
               - Error 401: 'error': 'Unauthorized Access'.<br/>
               - Error 400: 'error': 'Invalid payload'.<br/>
               - Error 500: 'error': 'Server Error'.<br/>
     """
     try:
          async with AsyncSession(async_engine) as session:
               # Admin Authentication
               user_identity = request.identity
               user_id       = user_identity.claims.get('user_id') if user_identity else None

               admin_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
               ))
               admin_user = admin_user_obj.scalar()

               if not admin_user.is_admin:
                    return json({'error': 'Admin authentication failed'}, 401)
               # Admin authentication ends here

               # Payload data
               status        = schema.status
               withdrawal_id = schema.withdrawal_id

               # Get the merchant withdrawal transaction
               merchant_withdrawals_obj = await session.execute(select(MerchantWithdrawals).where(
                    MerchantWithdrawals.id == withdrawal_id
               ))
               merchant_withdrawals = merchant_withdrawals_obj.scalar()

               if not merchant_withdrawals:
                    return json({'message': 'No Withdrawal request found with given information'}, 404)
               
               # Approved Withdrawals
               if merchant_withdrawals.is_completed == True:
                    return json({'message': 'Already updated, Can not perform this action'}, 400)
               
          
               # Get the currency
               currency_obj = await session.execute(select(Currency).where(
                    Currency.id == merchant_withdrawals.currency
               ))
               currency = currency_obj.scalar()

               # Get merchant account balance
               merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(MerchantAccountBalance.merchant_id == merchant_withdrawals.merchant_id,
                         MerchantAccountBalance.currency    == currency.name
                    )
               ))
               merchant_account_balance = merchant_account_balance_obj.scalar()

               account_balance_amount = merchant_account_balance.mature_balance
               
               
               # Update withdrawal status
               if status == 'Approved':
                    # If available balance is less than withdrawal balance
                    if account_balance_amount < merchant_withdrawals.amount:
                         return json({'message': 'Insufficient balance to withdrawal'}, 400)
                    
                    merchant_withdrawals.status       = status
                    merchant_withdrawals.is_completed = True
                    merchant_account_balance.mature_balance -= merchant_withdrawals.amount
                    merchant_account_balance.account_balance -= merchant_withdrawals.amount

               else:
                    merchant_withdrawals.status       = status
                    merchant_withdrawals.is_completed = False

               session.add(merchant_withdrawals)
               session.add(merchant_account_balance)
               await session.commit()
               await session.refresh(merchant_withdrawals)
               await session.refresh(merchant_account_balance)

               return json({'success': True, 'message': 'Updated Successfully'}, 200)

     except Exception as e:
          return json({'error':'Server Error', 'message': f'{str(e)}'}, 500)
     


# Search Withdrawal transactions by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/withdrawal/search/')
async def MerchantWithdrawalTransactionSearch(request: Request, query: str):
     """
        This API Endpoint let Admin search all merchant withdrawal transactions.<br/><br/>

        Parameters:<br/>
            query (str): Search query for transaction details.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            JSON: Returns a list of transaction details that match the search query.<br/>
            'merchant_withdrawal_search': List of transaction details<br/>
            'success': successful transaction status.<br/><br/>

        Raises:<br/>
            Exception: If any error occurs during the database query or response generation.<br/>
            Error 401: 'error': 'Unauthorized Access'.<br/>
            Error 500: 'error': 'Server Error'.<br/><br/>

        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
     """
     try:
          async with AsyncSession(async_engine) as session:
               # Admin Authentication
               user_identity = request.identity
               user_id       = user_identity.claims.get('user_id') if user_identity else None

               admin_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
               ))
               admin_user = admin_user_obj.scalar()

               if not admin_user.is_admin:
                    return json({'error': 'Admin authentication failed'}, 401)
               # Admin authentication ends here

               query_date = None
               query_time = None

               try:
                    query_as_float = float(query)  # If query is a number, try to convert
               except ValueError:
                    query_as_float = None

               try:
                    query_date = datetime.strptime(query, "%Y-%m-%d").date()
               except ValueError:
                    pass

               try:
                    query_time = datetime.strptime(query, "%H:%M:%S.%f").time()
               except ValueError:
                    pass

               # Search user full name
               user_full_name_obj = await session.execute(
                    select(Users).where(Users.full_name == query)
               )
               user_full_name = user_full_name_obj.scalars().all()

               # Search User Email
               user_email_obj = await session.execute(
                    select(Users).where(Users.email == query)
                    )
               user_email = user_email_obj.scalar()

               # Search Currency wise
               currency_obj = await session.execute(
                    select(Currency).where(Currency.name == query)
               )
               currency = currency_obj.scalar()

               # Search amount wise
               withdrawal_amount_obj = await session.execute(
                    select(MerchantWithdrawals).where(
                         MerchantWithdrawals.amount == query_as_float
                    ) if query_as_float is not None else select(MerchantWithdrawals).where(
                         MerchantWithdrawals.amount == 0.00
                    )
               )
               withdrawal_amount = withdrawal_amount_obj.scalars().all()

               # Search status wise
               withdrawal_status_obj = await session.execute(
                    select(MerchantWithdrawals).where(MerchantWithdrawals.status == query)
                    )
               withdrawal_status = withdrawal_status_obj.scalars().all()


               stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_completed,
                          MerchantBankAccount.bank_name,
                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          )
               
               conditions = []

               if user_full_name:
                    conditions.append(MerchantWithdrawals.merchant_id.in_([user.id for user in user_full_name]))

               elif user_email:
                    conditions.append(MerchantWithdrawals.merchant_id == user_email.id)

               elif currency:
                    conditions.append(MerchantWithdrawals.currency == currency.id)

               elif withdrawal_amount:
                    conditions.append(MerchantWithdrawals.amount.in_([wa.amount for wa in withdrawal_amount]))

               elif withdrawal_status:
                    conditions.append(MerchantWithdrawals.status.in_([ws.status for ws in withdrawal_status]))

               if query_date:
                    conditions.append(cast(MerchantWithdrawals.createdAt, Date) == query_date)

               if query_time:
                    conditions.append(cast(MerchantWithdrawals.createdAt, Time) == query_time)

               if conditions:
                    stmt = stmt.where(or_(*conditions))


               merchant_withdrawals_object = await session.execute(stmt)
               merchant_withdrawals = merchant_withdrawals_object.fetchall()

               merchant_withdrawals_data = []

               for mw in merchant_withdrawals:
                    # Currency Name
                    withdrawal_currency_obj = await session.execute(select(Currency).where(
                         Currency.id == mw.currency
                    ))
                    withdrawal_currency = withdrawal_currency_obj.scalar()

                    bank_currency_obj = await session.execute(select(Currency).where(
                         Currency.id == mw.bank_currency
                    ))
                    bank_currency = bank_currency_obj.scalar()

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == mw.merchant_id,
                              MerchantAccountBalance.currency    == withdrawal_currency.name
                              )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()


                    merchant_withdrawals_data.append({
                         "id": mw.id,
                         "merchant_id": mw.merchant_id,
                         'merchant_name': mw.full_name,
                         'merchant_email': mw.email,
                         "createdAt": mw.createdAt.isoformat() if mw.createdAt else None,
                         "withdrawalAmount": mw.amount,
                         "withdrawalCurrency": withdrawal_currency.name,
                         "status": mw.status,
                         "is_completed": mw.is_completed,
                         "bank_account": mw.bank_name,
                         "bankCurrency": bank_currency.name,
                         "full_name": mw.full_name,
                         "email": mw.email,
                         'account_balance': merchant_account_balance_.amount,
                         'account_currency': merchant_account_balance_.currency
                    })
                    

               return json({'success': True, 'merchant_withdrawal_search': merchant_withdrawals_data}, 200)

     except Exception as e:
          return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Export all merchant withdrawals by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/pg/export/withdrawals/')
async def AdminMerchantExportWithdrawalRequests(request: Request):
    """
        This API Endpoint exports all the merchant withdrawal transactions for admin users after authentication.<br/><br/>

        Parameters:<br/>
        - request (Request): The HTTP request object containing identity and other relevant information.<br/><br/>

        Returns:<br/>
        - JSON: A JSON response containing the success status and the exported withdrawals data.<br/>
        - JSON: A JSON response containing error status and error message if any.<br/><br/>

        Raises:<br/>
        - SqlAlchemyError: If there was an error while executing sql query.<br/>
        - BadRequest: If there was an error in input data.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            if not is_admin_user:
                return json({'error': 'Admin authentication failed'}, 401)
            # Admin authentication Ends

            # Get all the merchant withdrawals
            stmt = select(MerchantWithdrawals.id, 
                          MerchantWithdrawals.merchant_id,
                          MerchantWithdrawals.amount,
                          MerchantWithdrawals.createdAt,
                          MerchantWithdrawals.currency,
                          MerchantWithdrawals.bank_currency,
                          MerchantWithdrawals.status,
                          MerchantWithdrawals.is_completed,
                          MerchantBankAccount.bank_name,
                          Users.full_name,
                          Users.email,
                          ).join(
                               Users, Users.id == MerchantWithdrawals.merchant_id
                          ).join(
                               MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                          )
            merchant_withdrawals_object = await session.execute(stmt)
            merchant_withdrawals        = merchant_withdrawals_object.all()


            if not merchant_withdrawals:
                 return json({'error': 'No withdrawal request found'}, 404)
            

            for withdrawals in merchant_withdrawals:
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

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == withdrawals.merchant_id,
                              MerchantAccountBalance.currency    == merchant_withdrawal_currency.name
                              )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': withdrawals.full_name,
                        'merchant_email': withdrawals.email,
                        'bank_account': withdrawals.bank_name,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_completed': withdrawals.is_completed,
                        'account_balance': merchant_account_balance_.amount,
                        'account_currency': merchant_account_balance_.currency
                    })

            return json({'success': True, 'AdminMerchantExportWithdrawalRequests': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    





## Filter Merchant Withdrawals by Admin
@auth('userauth')
@post('/api/v4/admin/filter/merchant/withdrawals/')
async def filter_merchant_withdrawals(request: Request, schema: FilterMerchantWithdrawalsSchema, limit: int = 10, offset: int = 0):
     """
        Filter Merchant Withdrawals by Admin.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming HTTP request<br/>
            - schema (FilterMerchantWithdrawalsSchema): The schema for filtering withdrawals<br/>
            - limit (int): The number of records to return (default: 10)<br/>
            - offset (int): The offset to start from (default: 0)<br/><br/>
        
        Returns:<br/>
            JSON: A JSON response containing the following keys:<br/>
            - success (bool): A boolean indicating the success of the operation<br/>
            - AdminMerchantWithdrawalRequests (list): A list of dictionaries containing withdrawal details<br/>
            - paginated_count (int): The total number of withdrawals matching the filter criteria<br/>
            - error (str): An error message if any<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation<br/>
            - Error 401: 'error': 'Unauthorized Access'<br/>
            - Error 400: 'error': 'Invalid request parameters'<br/>
            - Error 500: 'error': 'Server Error'<br/><br/>
        
        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'<br/>
            - Error 400: 'error': 'Invalid request parameters'<br/>
            - Error 500: 'error': 'Server Error'<br/><br/>
        
        Note: The filter criteria include date, merchant email, withdrawal amount, withdrawal status, start date, and end date.<br/>
     """
     try:
          async with AsyncSession(async_engine) as session:
               user_identity = request.identity
               user_id       = user_identity.claims.get('user_id')

               # Admin authentication
               admin_user_obj = await session.execute(select(Users).where(
                    Users.id == user_id
               ))
               admin_user = admin_user_obj.scalar()

               if not admin_user.is_admin:
                    return json({'message': 'Admin authorization failed'}, 401)
               # Admin authentication ends

               combined_data = []

               ## Get The payload data
               date_time            = schema.date
               merchant_email       = schema.email
               withdrawal_amount    = schema.amount
               withdrawal_status    = schema.status
               startDate            = schema.start_date
               endDate              = schema.end_date

               conditions = []
               paginated_value = 0
                    

               # Get all the merchant withdrawals
               stmt = select(
                    MerchantWithdrawals.id, 
                    MerchantWithdrawals.merchant_id,
                    MerchantWithdrawals.amount,
                    MerchantWithdrawals.createdAt,
                    MerchantWithdrawals.currency,
                    MerchantWithdrawals.bank_currency,
                    MerchantWithdrawals.status,
                    MerchantWithdrawals.is_completed,

                    MerchantBankAccount.bank_name,

                    Users.full_name,
                    Users.email
                    ).join(
                         Users, Users.id == MerchantWithdrawals.merchant_id
                    ).join(
                         MerchantBankAccount, MerchantBankAccount.id == MerchantWithdrawals.bank_id
                    ).order_by(
                         desc(MerchantWithdrawals.id)
                    ).limit(
                         limit
                    ).offset(
                         offset
                    )
               
               # Filter merchant email wise
               if merchant_email:
                    # Get the user
                    merchant_user_obj = await session.execute(select(Users).where(
                         Users.email.like(f"{merchant_email}%") 
                    ))
                    merchant_user = merchant_user_obj.scalar()

                    if not merchant_user:
                         return json({'message': 'Invalid Email'}, 400)

               # Date time wise filter
               if date_time and date_time == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                         and_(
                             MerchantWithdrawals.createdAt >= start_date,
                             MerchantWithdrawals.createdAt  < (end_date + timedelta(days=1))
                         )
                    )

               elif date_time:
                    start_date, end_date = get_date_range(date_time)

                    conditions.append(
                         and_(
                             MerchantWithdrawals.createdAt >= start_date,
                             MerchantWithdrawals.createdAt <= end_date 
                         )
                    )

               ### Email wise filter
               if merchant_email:
                    conditions.append(
                         MerchantWithdrawals.merchant_id == merchant_user.id
                    )
               
               ### Withdrawal amount wise filter
               if withdrawal_amount:
                    withdrawal_amount = float(schema.amount)

                    conditions.append(
                         MerchantWithdrawals.amount == withdrawal_amount
                    )
               
               #### Withdrawal status wise filter
               if withdrawal_status:
                    conditions.append(
                         MerchantWithdrawals.status.ilike(f"{withdrawal_status}%")
                    )
               
               ### If fitltered data found
               if conditions:
                    statement = stmt.where(and_(*conditions))
                    
                    merchant_withdrawals_object = await session.execute(statement)
                    merchant_withdrawals        = merchant_withdrawals_object.fetchall()

                    ### Count paginated value
                    count_withdrawal_stmt = select(func.count()).select_from(MerchantWithdrawals).where(
                         *conditions
                    )
                    withdrawal_count = (await session.execute(count_withdrawal_stmt)).scalar()

                    paginated_value = withdrawal_count / limit
     
                    if not merchant_withdrawals:
                         return json({'message': 'No transaction found'}, 404)
               else:
                    return json({'message': 'No data found'}, 404)


               # Gather all the Data inside combined data
               for withdrawals in merchant_withdrawals:
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

                    # Get merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(
                              MerchantAccountBalance.merchant_id == withdrawals.merchant_id,
                              MerchantAccountBalance.currency    == merchant_withdrawal_currency.name
                         )
                    ))
                    merchant_account_balance_ = merchant_account_balance_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': withdrawals.full_name,
                        'merchant_email': withdrawals.email,
                        'bank_account': withdrawals.bank_name,
                        'bankCurrency': merchant_bank_currency.name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_completed': withdrawals.is_completed,
                        'account_balance': merchant_account_balance_.mature_balance if merchant_account_balance_ else None,
                        'account_currency': merchant_account_balance_.currency if merchant_account_balance_ else None
                    })

               return json({
                         'success': True, 
                         'AdminMerchantWithdrawalRequests': combined_data,
                         'paginated_count': paginated_value
                    }, 200)

     except Exception as e:
          return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)


