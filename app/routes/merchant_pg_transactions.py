from blacksheep import get, post, put, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantProdTransaction, MerchantSandBoxTransaction
from sqlmodel import and_, select, cast, Date, Time, func
from Models.PG.schema import AdminMerchantProductionTransactionUpdateSchema
from datetime import datetime
from app.controllers.PG.merchantTransaction import CalculateMerchantAccountBalance



# Get all the merchant production transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/transactions/')
async def get_merchant_pg_transaction(request: Request, limit : int = 15, offset : int = 0):
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
            merchant_transactions_obj = await session.execute(select(MerchantProdTransaction).order_by(
                (MerchantProdTransaction.id).desc()
            ).limit(limit).offset(offset))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # Count total row count
            count_stmt = select(func.count(MerchantProdTransaction.id))
            total_transaction_row_obj = await session.execute(count_stmt)
            total_rows = total_transaction_row_obj.scalar()

            total_rows_count = total_rows / limit

            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL': transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                    'is_completed':          transactions.is_completd,
                    'transaction_fee': transactions.transaction_fee
                })

            return json({
                'success': True, 
                'message': 'Transaction fetched successfuly', 
                'AdminmerchantPGTransactions': combined_data,
                'total_row_count':  total_rows_count
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
    


# Get all the merchant sandbox transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/sandbox/transactions/')
async def get_merchant_pg_sandbox_transaction(request: Request, limit : int = 15, offset : int = 0):
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
                (MerchantSandBoxTransaction.id).desc()
            ).limit(limit).offset(offset))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # Count total row count
            count_stmt = select(func.count(MerchantProdTransaction.id))
            total_transaction_row_obj = await session.execute(count_stmt)
            total_rows = total_transaction_row_obj.scalar()

            total_rows_count = total_rows / limit

            # get the user id
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



# Update Merchant Production Transaction by Admn
@auth('userauth')
@put('/api/admin/merchant/pg/transaction/update/')
async def update_merchantPGTransaction(request: Request, schema: AdminMerchantProductionTransactionUpdateSchema):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            # Authenticate User
            admin_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin = admin_obj.scalar()

            is_admin = admin.is_admin

            if not is_admin:
                return json({'error': 'Unauthorized access'}, 403)
            
            TransactionID = schema.transaction_id
            merchantID    = schema.merchant_id

            # Get The Merchant Transaction
            try:
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.transaction_id == TransactionID, 
                        MerchantProdTransaction.merchant_id    == merchantID
                        )
                ))
                merchant_transaction = merchant_transaction_obj.scalar()

            except Exception as e:
                return json({'error': 'Merchant Transaction error', 'message': f'{str(e)}'}, 400)
            
            # If no transaction found with given details
            if not merchant_transaction:
                return json({'error': 'Transaction not found'}, 404)
            
            # If the transaction already updated
            if merchant_transaction.is_completd:
                return json({'message': 'Transaction already updated'}, 405)


            # Update the transaction with details
            merchant_transaction.amount               = schema.amount
            merchant_transaction.currency             = schema.currency
            merchant_transaction.merchantCallBackURL  = schema.webhook_url
            merchant_transaction.merchantRedirectURl  = schema.redirect_url
            merchant_transaction.merchantMobileNumber = schema.mobile_number
            merchant_transaction.merchantPaymentType  = schema.payment_type
            merchant_transaction.status               = schema.status
            merchant_transaction.transaction_fee      = schema.transaction_fee

            if schema.status == 'PAYMENT_SUCCESS':
                merchant_transaction.is_completd = True

                await CalculateMerchantAccountBalance(
                    merchant_transaction.amount, 
                    merchant_transaction.currency, 
                    merchant_transaction.transaction_fee, 
                    merchant_transaction.merchant_id
                    )

            session.add(merchant_transaction)
            await session.commit()  
            await session.refresh(merchant_transaction)

            return json({'success': True, 'message': 'Updated Successfully'}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Export all Merchant Production Transactions
@auth('userauth')
@get('/api/v2/admin/merchant/pg/export/transactions/')
async def export_merchant_pg_production_transaction(request: Request):
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
            merchant_transactions_obj = await session.execute(select(MerchantProdTransaction).order_by(
                (MerchantProdTransaction.id).desc()
            ))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL': transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                })

            return json({'success': True, 'message': 'Transaction fetched successfuly', 'ExportmerchantPGTransaction': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)





# Export all Merchant Sandbox Transactions
@auth('userauth')
@get('/api/v2/admin/merchant/pg/sandbox/export/transactions/')
async def export_merchant_pg_sandbox_transactions(request: Request):
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
                return json({'error': 'Unauthorized Access'}, 401)
            
            # Get all the Sandbox transactions
            merchant_transactions_obj = await session.execute(select(MerchantSandBoxTransaction).order_by(
                (MerchantSandBoxTransaction.id).desc()
            ))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                # Store all data inside combined_data
                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL': transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                })

            return json({'success': True, 'message': 'Transaction fetched successfuly', 'ExportmerchantPGSBTransaction': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
    


# Search Merchant Production transaction Transaction by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/prod/search/transactions/')
async def search_merchant_pg_production_transactions(request: Request, query: str):
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
            merchant_order_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.merchantOrderId == search_query
            ))
            merchant_order = merchant_order_obj.scalars().all()

            # Search transaction transaction id wise
            merchant_transactionID_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.transaction_id == search_query
            ))
            merchant_transactionID = merchant_transactionID_obj.scalars().all()

            # Search transaction in MOP wise
            merchant_mop_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.payment_mode == search_query
            ))
            merchant_mop = merchant_mop_obj.scalars().all()

            # Search Transaction Amount wise
            merchant_amount_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.amount == query_as_float
            ))
            merchant_amount = merchant_amount_obj.scalars().all()

            # Search Transaction currency wise
            merchant_currency_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.currency == search_query
            ))
            merchant_currency = merchant_currency_obj.scalars().all()

            # Search transaction status wise
            merchant_status_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.status == search_query
            ))
            merchant_status = merchant_status_obj.scalars().all()

            # Search Transaction by Date
            merchant_date_obj = await session.execute(select(MerchantProdTransaction).where(
                cast(MerchantProdTransaction.createdAt, Date) == query_date
                    ))
            merchant_date = merchant_date_obj.scalars().all()

            # Search Transaction by Time
            merchant_time_obj = await session.execute(select(MerchantProdTransaction).where(
                    cast(MerchantProdTransaction.createdAt, Time) == query_time   
                ))
            merchant_time = merchant_time_obj.scalars().all()


            if merchant_order:
                merchant_prod_transactions_obj = merchant_order
            elif merchant_transactionID:
                merchant_prod_transactions_obj = merchant_transactionID
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
                    'gatewayRes': transaction.gateway_res,
                    'payment_mode': transaction.payment_mode,
                    'transaction_id': transaction.transaction_id,
                    'currency': transaction.currency,
                    'status': transaction.status,
                    'amount': transaction.amount,
                    'createdAt': transaction.createdAt,
                    'merchantOrderId': transaction.merchantOrderId,
                    'merchantRedirectURl': transaction.merchantRedirectURl,
                    'merchantRedirectMode': transaction.merchantRedirectMode,
                    'merchantCallBackURL': transaction.merchantCallBackURL,
                    'merchantMobileNumber': transaction.merchantMobileNumber,
                    'merchantPaymentType': transaction.merchantPaymentType,
                    'is_completd': transaction.is_completd,
                    'pipe_id': transaction.pipe_id,
                    'transaction_fee': transaction.transaction_fee,
                })

            return json({'success': True, 'admin_merchant_searched_prod_transactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


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


            if merchant_order:
                merchant_prod_transactions_obj = merchant_order
            elif merchant_transactionID:
                merchant_prod_transactions_obj = merchant_transactionID
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
                    'merchantRedirectMode': transaction.merchantRedirectMode,
                })

            return json({'success': True, 'admin_merchant_searched_sb_transactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



## Every merchant transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/distinct/transactions/')
async def merchant_pg_transaction(request: Request, query: int):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate admin
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

            merchant_id    = query
            combined_data  = []

            # Execute statement
            stmt = select(
                MerchantProdTransaction.id,
                MerchantProdTransaction.gateway_res,
                MerchantProdTransaction.payment_mode,
                MerchantProdTransaction.transaction_id,
                MerchantProdTransaction.currency,
                MerchantProdTransaction.status,
                MerchantProdTransaction.amount,
                MerchantProdTransaction.createdAt,
                MerchantProdTransaction.merchantOrderId,
                MerchantProdTransaction.merchantRedirectURl,
                MerchantProdTransaction.merchantCallBackURL,
                MerchantProdTransaction.merchantMobileNumber,
                MerchantProdTransaction.merchantPaymentType,
                MerchantProdTransaction.is_completd,
                MerchantProdTransaction.transaction_fee,

                Users.id.label('merchant_id'),
                Users.full_name.label('merchant_name'),
                Users.email.label('merchant_email')
            ).join(
                Users, Users.id == MerchantProdTransaction.merchant_id
            ).where(
                MerchantProdTransaction.merchant_id == merchant_id
            )


            # Get all the transaction related to the merchant
            merchant_transactions_obj = await session.execute(stmt)
            merchant_transactions_ = merchant_transactions_obj.all()

            for transaction in merchant_transactions_:

                combined_data.append({
                    'id': transaction.id,
                    'merchant': {
                        'merchant_id': transaction.merchant_id,
                        'merchant_name': transaction.merchant_name,
                        'merchant_email': transaction.merchant_email
                    },
                    'gatewayRes': transaction.gateway_res,
                    'payment_mode': transaction.payment_mode,
                    'transaction_id': transaction.transaction_id,
                    'currency': transaction.currency,
                    'status':   transaction.status,
                    'amount':   transaction.amount,
                    'createdAt': transaction.createdAt,
                    'merchantOrderId': transaction.merchantOrderId,
                    'merchantRedirectURl': transaction.merchantRedirectURl,
                    'merchantCallBackURL': transaction.merchantCallBackURL,
                    'merchantMobileNumber': transaction.merchantMobileNumber,
                    'merchantPaymentType':  transaction.merchantPaymentType,
                    'is_completed':  transaction.is_completd,
                    'transaction_fee': transaction.transaction_fee
                })

            return json({'success': True, 'distinct_merchant_transaction': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)