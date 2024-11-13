from blacksheep import get, json, Request, post
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantSandBoxTransaction
from sqlmodel import select, func, desc, cast, Date, Time, and_
from datetime import datetime, timedelta
from Models.Admin.PG.schema import AllSandboxTransactionFilterSchema
from app.dateFormat import get_date_range





# Get all the merchant sandbox transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/sandbox/transactions/')
async def get_merchant_pg_sandbox_transaction(request: Request, limit : int = 10, offset : int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Admin Authentication
            admin_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin = admin_object.scalar()

            is_admin_user = admin.is_admin

            if not is_admin_user:
                return json({'error': 'Unauthorized Access'}, 403)
            
            # Get all the Production transactions
            merchant_transactions_obj = await session.execute(select(MerchantSandBoxTransaction).order_by(
                desc(MerchantSandBoxTransaction.id)
            ).limit(limit).offset(offset))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # Count total row count
            count_stmt = select(func.count(MerchantSandBoxTransaction.id))
            total_transaction_row_obj = await session.execute(count_stmt)
            total_rows = total_transaction_row_obj.scalar()

            total_rows_count = total_rows / limit

            # get the users
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            # User data dictionary
            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                # All the transaction inside the combined_data
                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    # 'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL':  transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                    'business_name':       transactions.business_name,
                    'is_completed':         transactions.is_completd
                })

            return json({
                'success': True, 
                'message': 'Transaction fetched successfuly', 
                'AdminmerchantPGSandboxTransactions': combined_data,
                'total_row_count':  total_rows_count
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
    



# Search Merchant Sandbox transaction Transaction by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/sb/search/transactions/')
async def search_merchant_pg_sandbox_transactions(request: Request, query: str):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id') if user_identity else None

            # Admin Authentication
            admin_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin = admin_object.scalar()

            is_admin_user = admin.is_admin

            if not is_admin_user:
                return json({'error': 'Unauthorized Access'}, 401)
            # Admin authentication ends here

            search_query = query
            combined_data = []
            query_date = None
            query_time = None
            
            # Convert to date format
            try:
                query_date = datetime.strptime(search_query, "%d %B %Y").date()
            except ValueError:
                pass

            # Convert to time format
            try:
                query_time = datetime.strptime(search_query, "%H:%M:%S.%f").time()
            except ValueError:
                pass

            # Conver to float format
            try:
                query_as_float = float(query)  # If query is a number, try to convert
            except ValueError:
                query_as_float = None

            # Search transaction order wise
            merchant_order_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.merchantOrderId == search_query
            ))
            merchant_order = merchant_order_obj.scalars().all()

            # Search transaction transaction id wise
            merchant_transactionID_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.transaction_id == search_query
            ))
            merchant_transactionID = merchant_transactionID_obj.scalars().all()


            # Search transaction business name wise
            merchant_business_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.business_name == search_query
            ))
            merchant_business = merchant_business_obj.scalars().all()


            # Search transaction in MOP wise
            merchant_mop_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.payment_mode == search_query
            ))
            merchant_mop = merchant_mop_obj.scalars().all()


            # Search Transaction Amount wise
            merchant_amount_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.amount == query_as_float
            ))
            merchant_amount = merchant_amount_obj.scalars().all()


            # Search Transaction currency wise
            merchant_currency_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.currency == search_query
            ))
            merchant_currency = merchant_currency_obj.scalars().all()


            # Search transaction status wise
            merchant_status_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                MerchantSandBoxTransaction.status == search_query
            ))
            merchant_status = merchant_status_obj.scalars().all()


            # Search Transaction by Date
            merchant_date_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                cast(MerchantSandBoxTransaction.createdAt, Date) == query_date
                    ))
            merchant_date = merchant_date_obj.scalars().all()


            # Search Transaction by Time
            merchant_time_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    cast(MerchantSandBoxTransaction.createdAt, Time) == query_time   
                ))
            merchant_time = merchant_time_obj.scalars().all()


            # Apply conditions
            if merchant_order:
                merchant_prod_transactions_obj = merchant_order

            elif merchant_transactionID:
                merchant_prod_transactions_obj = merchant_transactionID

            elif merchant_business:
                merchant_prod_transactions_obj = merchant_business

            elif merchant_mop:
                merchant_prod_transactions_obj = merchant_mop

            elif merchant_amount:
                merchant_prod_transactions_obj = merchant_amount

            elif merchant_currency:
                merchant_prod_transactions_obj = merchant_currency

            elif merchant_status:
                merchant_prod_transactions_obj = merchant_status

            elif merchant_date:
                merchant_prod_transactions_obj = merchant_date

            elif merchant_time:
                merchant_prod_transactions_obj = merchant_time

            else:
                merchant_prod_transactions_obj = []
            
            if not merchant_prod_transactions_obj:
                return json({'message': 'No transaction found'}, 404)
                
            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            for transaction in merchant_prod_transactions_obj:
                user_id = users_dict.get(transaction.merchant_id)

                combined_data.append({
                    'id': transaction.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    'payment_mode': transaction.payment_mode,
                    'transaction_id': transaction.transaction_id,
                    'currency': transaction.currency,
                    'status': transaction.status,
                    'amount': transaction.amount,
                    'createdAt': transaction.createdAt,
                    'merchantOrderId': transaction.merchantOrderId,
                    'merchantRedirectURl': transaction.merchantRedirectURl,
                    'merchantCallBackURL': transaction.merchantCallBackURL,
                    'merchantMobileNumber': transaction.merchantMobileNumber,
                    'merchantPaymentType': transaction.merchantPaymentType,
                    'is_completd': transaction.is_completd,
                    'business_name': transaction.business_name,
                    'merchantRedirectMode': transaction.merchantRedirectMode,
                })

            return json({'success': True, 'admin_merchant_searched_sb_transactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    

# Filter Merchant Sandbox Transactions
@auth('userauth')
@post('/api/v2/admin/merchant/filter/sandbox/transaction/')
async def filter_merchant_sandbox_transaction(request: Request, schema: AllSandboxTransactionFilterSchema, limit: int = 10, offset: int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            combined_data = []

            # Admin authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authentication failed'}, 401)
            # Admin authentication ends

            # Get the payload data
            date_time          = schema.date
            transactionID      = schema.transaction_id
            transaction_amount = schema.transaction_amount
            business_name      = schema.business_name
            startDate          = schema.start_date
            endDate            = schema.end_date
            

            conditions = []
            paginated_value = 0

            
            ### Select the table and column
            stmt = select(
                MerchantSandBoxTransaction
            ).order_by(
                desc(MerchantSandBoxTransaction.id)
            ).limit(
                limit
            ).offset(
                offset
            )

            ## Filter according to the Input date time
            if date_time and date_time == 'CustomRange':
                start_date = datetime.strptime(startDate, "%Y-%m-%d")
                end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                conditions.append(
                    and_(
                        MerchantSandBoxTransaction.createdAt >= start_date,
                        MerchantSandBoxTransaction.createdAt < (end_date + timedelta(days=1))
                    )
                )

            elif date_time:
                # Convert according to date time format
                start_date, end_date = get_date_range(date_time)

                conditions.append(
                    and_(
                        MerchantSandBoxTransaction.createdAt >= start_date,
                        MerchantSandBoxTransaction.createdAt <= end_date
                    )
                )

            ## Filter according to transaction ID
            if transactionID:

                conditions.append(
                    MerchantSandBoxTransaction.transaction_id == transactionID
                )
            
            ## Filter according to transaction Amount
            if transaction_amount:
                transaction_amount = float(schema.transaction_amount)
                conditions.append(
                    MerchantSandBoxTransaction.amount == transaction_amount
                )

            ## Filter according to business Name
            if business_name:
                conditions.append(
                    MerchantSandBoxTransaction.business_name == business_name
                )
            
            ### IF data found
            if conditions:
                statement = stmt.where(and_(*conditions))

                merchant_transactions_obj = await session.execute(statement)
                merchant_transactions     = merchant_transactions_obj.scalars().all()

                ### Count paginated value
                count_transaction_stmt = select(func.count()).select_from(MerchantSandBoxTransaction).where(
                    *conditions
                )
                transaction_count = (await session.execute(count_transaction_stmt)).scalar()

                paginated_value = transaction_count / limit

                if not merchant_transactions:
                    return json({'message': 'No transaction found'}, 404)
            else:
                return json({'message': 'No data found'}, 404)
            
            # get the users
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            # User data dictionary
            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                # All the transaction inside the combined_data
                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    # 'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL':  transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                    'business_name':       transactions.business_name,
                    'is_completed':         transactions.is_completd
                })

            return json({
                'success': True, 
                'message': 'Transaction fetched successfuly', 
                'AdminmerchantPGSandboxTransactions': combined_data,
                'paginated_count': paginated_value
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)