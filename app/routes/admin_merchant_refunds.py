from blacksheep import get, put, post, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Currency
from Models.models2 import MerchantProdTransaction, MerchantAccountBalance
from Models.models3 import MerchantRefund
from Models.Admin.PG.schema import AdminUpdateMerchantRefundSchema, FilterMerchantRefunds
from sqlmodel import select, and_, desc, func, cast, Date, Time, or_
from datetime import datetime, timedelta
from app.dateFormat import get_date_range




# Get all the merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/refunds/')
async def Admin_Merchant_Refunds(request: Request, limit: int = 10, offset: int = 0):
    """
        Get all the merchant refund transactions.<br/>
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object.<br/>
            - limit (int): The number of rows to be returned. Default is 10.<br/>
            - offset (int): The offset of the rows to be returned. Default is 0.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the admin_merchant_refunds, success, message, and the total_count.<br/>
            - HTTP Status Code: 200 if successful, 401 if unauthorized, or 500 if an error occurs.<br/><br/>

        Error message:<br/>
            - Unauthorized Access: If the user is not authorized to access the endpoint.<br/>
            - Server Error: If an error occurs while executing the database query or response generation.<br/>
            - Bad Request: If the request data is invalid.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'error': 'Admin authentication Failed'}, 401)
            # Admin authentication ends here

            if limit < 0 or offset < 0:
                return json({"message": "limit and offset value can not be negative"}, 400)
            
            # Count total rows
            count_stmt = select(func.count(MerchantRefund.id))
            total_rows_obj = await session.execute(count_stmt)
            total_rows = total_rows_obj.scalar()

            total_rows_count = total_rows / limit

            # Get all the refund made by the merchant
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)

                ).limit(limit).offset(offset)
            
            merchant_refunds_obj = await session.execute(stmt)
            merchant_refunds = merchant_refunds_obj.fetchall()

            if not merchant_refunds:
                return json({'message': 'No refund requests available'}, 404)
            
            for refunds in merchant_refunds:
                    combined_data.append({
                        'id': refunds.id,
                        "currency": refunds.currency_name,
                        "transaction_currency": refunds.transaction_currency,
                        "merchant_id": refunds.merchant_id,
                        'merchant_name': refunds.merchant_name,
                        'merchant_email': refunds.merchant_email,
                        # 'instant_refund': refunds.instant_refund,
                        # 'instant_refund_amount': refunds.instant_refund_amount,
                        'is_completed': refunds.is_completed,
                        'transaction_id': refunds.transaction_id,
                        'amount': refunds.amount,
                        'transaction_amount': refunds.transaction_amount,
                        'createdAt': refunds.createdAt,
                        'status': refunds.status
                    })

            return json({'success': True, 'total_count': total_rows_count, 'admin_merchant_refunds': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)





# Update Merchant Refund by Admin
@auth('userauth')
@put('/api/v6/admin/merchant/update/refunds/')
async def MerchantRefundUpdate(request: Request, schema: AdminUpdateMerchantRefundSchema):
    """
        This API Endpoint let Admin update Merchant Refund transaction.
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming HTTP request.<br/>
            - schema (AdminUpdateMerchantRefundSchema): The schema for the request data.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the updated refund transaction data.<br/>
            - HTTP Status Code: 200 if the refund is updated successfully.<br/>
            - HTTP Status Code: 400 if the request data is invalid.<br/>
            - HTTP Status Code: 401 if the user is not authenticated as admin.<br/>
            - HTTP Status Code: 500 if there is a server error.<br/><br/>

        Error Messages:<br/>
            - 'message': 'Admin authentication failed'<br/>
            - 'message': 'Can not perform the same action again'<br/>
            - 'message': 'Donot have sufficient balance in account'<br/><br/>

        Raises:<br/>
            - BadRequest: If the request data is invalid or the file data is not provided.<br/>
            - SQLAlchemyError: If there is an error during database operations.<br/>
            - Exception: If any other unexpected error occurs.<br/>
            - ValueError: If the form data is invalid.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
               # Authenticate user as Admin
               user_identity = request.identity
               user_id = user_identity.claims.get('user_id')

               adminUserObj = await session.execute(select(Users).where(Users.id == user_id))
               adminUser = adminUserObj.scalar()

               if not adminUser.is_admin:
                    return json({'message': 'Admin authentication failed'}, 401)
               # Admin authentication Ends

               # Get the payload data
               merchantID    = schema.merchant_id
               refundID      = schema.refund_id
               transactionID = schema.transaction_id
               status        = schema.status

               # Get the transaction related to the Refund
               merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                        and_(MerchantProdTransaction.transaction_id == transactionID,
                                MerchantProdTransaction.merchant_id == merchantID
                                )
                ))
               merchant_transaction = merchant_transaction_obj.scalar()
               
               # Get the Merchant refund transaction
               merchantRefundTransactionObj = await session.execute(select(MerchantRefund).where(
                    and_(
                        MerchantRefund.merchant_id == merchantID,
                        MerchantRefund.id == refundID
                        )
                    ))
               merchantRefundTransaction = merchantRefundTransactionObj.scalar()

               ## If the transaction already approved
               if merchantRefundTransaction.status == 'Approved':
                    return json({'message': 'Can not perform the same action again'}, 405)
               
               
               # Update database
               merchantRefundTransaction.status = status

               if status == 'Approved':
                    # Get the Merchant account balance
                    merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                         and_(MerchantAccountBalance.merchant_id == merchantID,
                              MerchantAccountBalance.currency    == merchant_transaction.currency)
                    ))
                    merchant_account_balance = merchant_account_balance_obj.scalar()

                    if merchant_account_balance.mature_balance < merchantRefundTransaction.amount:
                        return json({'message': 'Donot have sufficient balance in account'}, 400)

                    merchantRefundTransaction.is_completed = True

                    # Update the transaction as refunded
                    merchant_transaction.is_refunded = True

                    # Deduct the merchant Account balance
                    merchant_account_balance.mature_balance -= merchantRefundTransaction.amount
                    merchant_account_balance.account_balance -= merchantRefundTransaction.amount
                    
                    session.add(merchant_transaction)
                    session.add(merchant_account_balance)
                    await session.commit()
                    await session.refresh(merchant_transaction)
                    await session.refresh(merchant_account_balance)

               session.add(merchantRefundTransaction)
               await session.commit()
               await session.refresh(merchantRefundTransaction)

               return json({'success': True, 'message': 'Updated Successfully'}, 200)
               
    except Exception as e:
         return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



# Export all Merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/pg/export/refunds/')
async def ExportMerchantRefunds(request: Request):
    """
        Export all Merchant Refund Transactions made by the merchant.<br/>
        Admin authentication is required to access this endpoint.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming request object.<br/><br/>

        Returns:<br/>
            - JSON response with success status and refund data(admin_merchant_refunds_export), along with HTTP status code.<br/>
            - JSON response with error status and message if any exceptions occur.<br/>
            - If no refunds found, it returns a message: {'message': 'No refund requests available'} with status code 404.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - SQLAlchemy exception if there is any error during the database query or response generation.<br/><br/>
        
        Error message:<br/>
            - Error 401: 'Unauthorized'<br/>
            - Error 500: 'error': 'Server Error'<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'error': 'Admin authentication Failed'}, 401)
            # Admin authentication ends here

            # Get all the refunds made by the merchant
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                # MerchantRefund.instant_refund,
                # MerchantRefund.instant_refund_amount,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)

                )
            
            merchant_refunds_obj = await session.execute(stmt)
            merchant_refunds = merchant_refunds_obj.fetchall()

            if not merchant_refunds:
                return json({'message': 'No refund requests available'}, 404)
            
            for refunds in merchant_refunds:
                combined_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'merchant_name': refunds.merchant_name,
                    'merchant_email': refunds.merchant_email,
                    # 'instant_refund': refunds.instant_refund,
                    # 'instant_refund_amount': refunds.instant_refund_amount,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'admin_merchant_refunds_export': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


# Search Merchant Refund Transactions
@auth('userauth')
@get('/api/v6/admin/merchant/refund/search/')
async def SearchMerchantRefunds(request: Request, query: str):
    """
        Admin will be able to Search Merchant Refund Transactions.<br/><br/>

        Parameters:<br/>
            query (str): Search query for refund details.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON response with success status and refund data(searched_merchant_refund), along with HTTP status code.<br/>
            - JSON response with error status and message if any exceptions occur.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - SQLAlchemy exception if there is any error during the database query or response generation.<br/><br/>
        
        Error message:<br/>
            - Error 401: 'Unauthorized'<br/>
            - Error 500: 'error': 'Server Error'<br/>
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
            # Admin authentication ends

            query_date = None
            query_time = None
            query_as_float = None

            try:
                query_as_float = float(query)  # If query is a number, try to convert
            except ValueError:
                pass

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

            # Search Refund amount wise
            refund_amount_obj = await session.execute(
                select(MerchantRefund).where(
                        MerchantRefund.amount == query_as_float
                )
            )
            refund_amount = refund_amount_obj.scalars().all()

             # Search status wise
            refund_status_obj = await session.execute(
                select(MerchantRefund).where(MerchantRefund.status == query)
                )
            refund_status = refund_status_obj.scalars().all()

            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)
                )
            
            conditions = []

            if user_full_name:
                conditions.append(MerchantRefund.merchant_id.in_([user.id for user in user_full_name]))

            elif user_email:
                conditions.append(MerchantRefund.merchant_id == user_email.id)

            elif currency:
                conditions.append(MerchantRefund.currency == currency.id)

            elif refund_amount:
                conditions.append(MerchantRefund.amount.in_([wa.amount for wa in refund_amount]))

            elif refund_status:
                conditions.append(MerchantRefund.status.in_([ws.status for ws in refund_status]))

            elif query_date:
                conditions.append(cast(MerchantRefund.createdAt, Date) == query_date)

            elif query_time:
                conditions.append(cast(MerchantRefund.createdAt, Time) == query_time)

            if conditions:
                stmt = stmt.where(or_(*conditions))

            merchant_refunds_object = await session.execute(stmt)
            merchant_refunds        = merchant_refunds_object.fetchall()

            merchant_refunds_data = []

            for refunds in merchant_refunds:
                
                merchant_refunds_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'merchant_name': refunds.merchant_name,
                    'merchant_email': refunds.merchant_email,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'searched_merchant_refund': merchant_refunds_data}, 200)

    except Exception as e:
         return json({'error':'Server Error', 'message': f'{str(e)}'}, 500) 
    




@auth('userauth')
@post('/api/v6/admin/filter/merchant/refunds/')
async def filter_merchant_refunds(request: Request, schema: FilterMerchantRefunds, limit: int = 10, offset: int = 0):
    """
        Get all the merchant refund transactions.<br/>
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object containing the payload data.<br/>
            - schema (FilterMerchantRefunds): The schema object containing the validated data.<br/>
            - limit (optional): Limit the number of records returned (default: 10).<br/>
            - offset (optional): Offset the number of records to skip (default: 0).<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the list of merchant refund transactions.<br/>
            - 'paginated_count': The total number of rows in the result set.<br/>
            - 'admin_merchant_filter_refunds': A list of dictionaries, each containing details of a refund transaction.<br/>
            - 'error': If any error occurs during the database operations.<br/>
            - Error 401: If the user is not authorized to access this endpoint.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authorized to access this endpoint.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
            - 'message': 'Invalid Currency' If provided currency does not exists.<br/>
            - 'message': 'No transaction found' If no transaction found.<br/><br/>

        Raises:<br/>
            - HTTPException: If the user is not authorized or if the provided currency does not exist.<br/>
            - HTTPStatus: 401 Unauthorized if the user is not an admin.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/>
            - HTTPStatus: 400 Bad Request if the provided currency does not exist.<br/>
            - HTTPStatus: 404 Bad Request if no transaction found.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id')

            # Authenticate admin
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization failed'}, 401)
            # Admin authentication ends

            # Get the payload data
            date_time       = schema.date
            merchant_mail   = schema.email
            refund_currency = schema.currency
            refund_amount   = schema.amount
            startDate       = schema.start_date
            endDate         = schema.end_date

            conditions = []
            combined_data = []
            paginated_value = 0

            # Select data
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email'),

                ).join(
                    Currency, Currency.id == MerchantRefund.currency
                ).join(
                    MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                ).join(
                     Users, Users.id == MerchantRefund.merchant_id
                ).order_by(
                    desc(MerchantRefund.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )


            # Filter time wise
            if date_time and date_time == 'CustomRange':
                start_date = datetime.strptime(startDate, "%Y-%m-%d")
                end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                conditions.append(
                    and_(
                        MerchantRefund.createdAt >= start_date,
                        MerchantRefund.createdAt < (end_date + timedelta(days=1))
                    ))
                
            elif date_time:
                # Convert according to date time format
                start_date, end_date = get_date_range(date_time)

                conditions.append(
                    and_(
                        MerchantRefund.createdAt >= start_date,
                        MerchantRefund.createdAt <= end_date
                    ))
             

            # Filter Merchant email wise
            if merchant_mail:
                merchant_email_obj = await session.execute(select(Users).where(
                    Users.email.like(f"{merchant_mail}%")
                ))
                merchant_email = merchant_email_obj.scalar()

                if not merchant_email:
                    return json({'message': 'Invalid email address'}, 400)
                
                conditions.append(
                    MerchantRefund.merchant_id == merchant_email.id
                )


            # Filter currency wise
            if refund_currency:
                refund_currency = schema.currency.upper()

                currency_obj = await session.execute(select(Currency).where(
                    Currency.name.like(f"{refund_currency}%")
                ))
                currency = currency_obj.scalar()

                if not currency:
                    return json({'message': 'Invalid Currency'}, 400)
                
                conditions.append(MerchantRefund.currency == currency.id)

            # Filter amount wise
            if refund_amount:
                refund_amount = float(schema.amount)
                conditions.append(
                    MerchantRefund.amount == refund_amount
                )
            
            ### IF filtered data present
            if conditions:
                statement = stmt.where(and_(*conditions))

                merchant_refunds_obj = await session.execute(statement)
                merchant_refunds     = merchant_refunds_obj.fetchall()

                ### Count paginated value
                count_refund_stmt = select(func.count()).select_from(MerchantRefund).where(
                        *conditions
                )
                refund_count = (await session.execute(count_refund_stmt)).scalar()

                paginated_value = refund_count / limit

                if not merchant_refunds:
                    return json({'message': 'No transaction found'}, 404)
            else:
                return json({'message': 'No transaction found'}, 404)
            

            # Combine all the data inside a list
            for refunds in merchant_refunds:
                combined_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'merchant_name': refunds.merchant_name,
                    'merchant_email': refunds.merchant_email,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({
                'success': True, 
                'admin_merchant_filter_refunds': combined_data,
                'paginated_count': paginated_value

                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

