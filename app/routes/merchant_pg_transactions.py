from blacksheep import get, post, put, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import (MerchantProdTransaction, MerchantSandBoxTransaction, 
                            MerchantAccountBalance, MerchantPIPE, PIPE)
from sqlmodel import and_, select, cast, Date, Time, func, desc
from Models.PG.schema import AdminMerchantProductionTransactionUpdateSchema
from datetime import datetime, timedelta
from app.controllers.PG.merchantTransaction import CalculateMerchantAccountBalance
from app.dateFormat import get_date_range
from Models.Admin.PG.schema import AllTransactionFilterSchema
import re




# Get all the merchant production transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/transactions/')
async def get_merchant_pg_transaction(request: Request, limit : int = 10, offset : int = 0):
    """
        Get all the merchant production transaction and transfer the Immature balance to Mature balance if settlement period completed.<br/><br/>
        
        Parameters:<br/>
        - request (Request): Request object<br/>
        - limit (int): The number of rows to be returned. Default is 15.<br/>
        - offset (int): The offset of the rows to be returned. Default is 0.<br/><br/>
        
        Returns:<br/>
        - JSON: A JSON response containing the list of PG Production transactions of merchant.<br/>
        - total_row_count (int): The total number of rows available.<br/><br/>
        - AdminmerchantPGTransactions(list): A list of transactions.
        - success(bool): Whether transaction was successful.<br/>
        - message (string): The transaction message.<br/><br/>
        
        Raises:<br/>
        - Exception: If any error occurs during the database query or response generation.<br/>
        - Error 401: 'error': 'Unauthorized Access'.<br/>
        - Error 500: 'error': 'Server Error'.<br/><br/>
        
        Error Messages:<br/>
        - Error 401: 'error': 'Unauthorized Access'.<br/>
        - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id') if user_identity else None

            currenct_datetime =  datetime.now()

            combined_data = []

            # Admin Authentication
            admin_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin = admin_object.scalar()

            is_admin_user = admin.is_admin

            if not is_admin_user:
                return json({'error': 'Unauthorized Access'}, 403)
            # Admin authentication ends

            # Get all the transactions related to the merchant
            merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.status == 'PAYMENT_SUCCESS'
            ))
            merchant_prod_transaction = merchant_prod_transaction_obj.scalars().all()

            # Check the which transactions related to merchant has been matured
            if merchant_prod_transaction:
                for transaction in merchant_prod_transaction:
                    if transaction.pg_settlement_date:
                        if transaction.pg_settlement_date < currenct_datetime and transaction.balance_status == 'Immature':
                            # Get the account balance of the merchant
                            merchant_account_balance_Obj = await session.execute(select(MerchantAccountBalance).where(
                            and_(
                                MerchantAccountBalance.merchant_id == transaction.merchant_id,
                                MerchantAccountBalance.currency    == transaction.currency
                                )
                            ))
                            merchant_account_balance = merchant_account_balance_Obj.scalar()

                            charged_fee       = (transaction.amount / 100) * transaction.transaction_fee
                            merchant__balance = transaction.amount - charged_fee
                            
                            if merchant_account_balance:
                                # Update the mature and immature balance
                                if merchant_account_balance.immature_balance > 0:
                                    merchant_account_balance.immature_balance -= merchant__balance
                                    merchant_account_balance.mature_balance   += merchant__balance

                                transaction.balance_status = 'Mature'

                                session.add(merchant_account_balance)
                                session.add(transaction)
                                await session.commit()
                                await session.refresh(merchant_account_balance)
                                await session.refresh(transaction)
            
            # Get all the Production transactions
            merchant_transactions_obj = await session.execute(select(MerchantProdTransaction).order_by(
                desc(MerchantProdTransaction.id)
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
                    'transaction_fee': transactions.transaction_fee,
                    'business_name': transactions.business_name
                })

            return json({
                'success': True, 
                'message': 'Transaction fetched successfuly', 
                'AdminmerchantPGTransactions': combined_data,
                'total_row_count':  total_rows_count
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)





# Update Merchant Production Transaction by Admn
@auth('userauth')
@put('/api/admin/merchant/pg/transaction/update/')
async def update_merchantPGTransaction(request: Request, schema: AdminMerchantProductionTransactionUpdateSchema):
    """
        This API Endpoint let Admin update Merchant Production transaction.<br/>
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            schema (AdminMerchantProductionTransactionUpdateSchema): Schema object with data for updating transaction.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the success message(Updated Successfully) and status 200.<br/><br/>

        Raises:<br/>
            - Unauthorized: If user is not authenticated as admin.<br/>
            - BadRequest: If the payload data is invalid.<br/>
            - HTTPException: If the request payload is invalid or if the user is not authenticated as admin.<br/>
            - HTTPStatus: 401 Unauthorized if the user is not authenticated as admin.<br/>
            - HTTPStatus: 400 Bad Request if the payload data is invalid.<br/>
            - HTTPStatus: 500 Internal Server Error if there is an error in the server's processing.<br/>
            - HTTPStatus: 404 Not Found if transaction not found.<br/><br/>

        Error messages:<br/>
            - 401: Unauthorized.<br/>
            - 400: Bad Request.<br/>
            - 404: Not Found.<br/>
            - 500: Internal Server Error.<br/>
            - 'error': 'Transaction not found' <br/>
            - 'message': 'Provide transaction Fee'<br/>
            - 'message': 'Can not add amount into frozen balance'<br/>
            - 'message': 'Amount has been credited to Mature fund'<br/>
            - 'message': 'Insufficient Immature Balance'<br/>
            - 'message': 'Amount has been credited to Mature fund'<br/>
            - 'message': 'Insufficient Immature Balance'<br/>
            - 'message': 'Can not perform this action'<br/>
            - 'message': 'Insufficient Frozen balance'<br/>
            - 'message': 'Already added balance to Fronzen fund'<br/>
            - 'message': 'Can not hold failed transaction'<br/>
            - 'message': 'Can not hold pending transaction'<br/>
    """
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
            # Admin authentication ends here

            TransactionID = schema.transaction_id
            merchantID    = schema.merchant_id

            ## Get The Merchant Transaction
            try:
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.transaction_id == TransactionID, 
                        MerchantProdTransaction.merchant_id     == merchantID
                    )
                ))
                merchant_transaction = merchant_transaction_obj.scalar()

            except Exception as e:
                return json({'error': 'Merchant Transaction error', 'message': f'{str(e)}'}, 400)
            
            
            ## If no transaction found with given details
            if not merchant_transaction:
                return json({'error': 'Transaction not found'}, 404)
            
            transactionFee = schema.transaction_fee if isinstance(schema.transaction_fee, int) else merchant_transaction.transaction_fee
            
            if not transactionFee:
                return json({'message': 'Provide transaction Fee'}, 400)
            
            # calculate Fee Ammount
            transaction_fee_amount = ((schema.amount / 100) * transactionFee)

            current_datetime = datetime.now()

            # Get Merchant account balance
            merchant_account_balance_Obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == merchant_transaction.merchant_id,
                    MerchantAccountBalance.currency    == merchant_transaction.currency
                    )))
            merchant_account_balance = merchant_account_balance_Obj.scalar()

            ###############################
            #### For Initiated Trasaction
            ###############################
            if merchant_transaction.status == 'PAYMENT_INITIATED':
                # Holding the payment
                if schema.status == 'PAYMENT_HOLD':
                    return json({'message': 'Can not add amount into frozen balance'}, 400)
                
                else:
                    return json({'message': 'Can not perform this action'}, 400)

            
            ####################################
            ## For Already Success transaction ##
            #####################################
            elif merchant_transaction.status == 'PAYMENT_SUCCESS':

                # Reapproving the transaction
                if schema.status == 'PAYMENT_SUCCESS':
                    return json({'message': 'Transaction already updated'}, 400)

                
                # Holding the payment
                elif schema.status == 'PAYMENT_HOLD':
                    # Transfer payment to frozen balance
                    if merchant_transaction.pg_settlement_date:
                        if current_datetime > merchant_transaction.pg_settlement_date:
                            return json({'message': 'Amount has been credited to Mature fund'}, 400)
                    
                    merchant_transaction.balance_status = 'Frozen'

                    # Calculate the amount to be credited into merchant account
                    # Transfer the amount into forzen balance
                    charged_fee    = transaction_fee_amount
                    total__balance = merchant_transaction.amount - charged_fee

                    if merchant_account_balance:
                        if merchant_account_balance.immature_balance < total__balance:
                            return json({'message': 'Insufficient Immature Balance'}, 400)
                        
                        merchant_account_balance.immature_balance -= total__balance
                        merchant_account_balance.frozen_balance   += total__balance

                        session.add(merchant_account_balance)
                        session.add(merchant_transaction)

                # If the payment staus is Failed
                elif schema.status == 'PAYMENT_FAILED':

                    # Failing the transaction after amount added into Mature fund
                    if merchant_transaction.pg_settlement_date:
                        if current_datetime > merchant_transaction.pg_settlement_date:
                            return json({'message': 'Amount has been credited to Mature fund'}, 400)
                    
                    merchant_transaction.balance_status = 'Failed'

                    # Calculate the amount to be credited into merchant account
                    # Transfer the amount into forzen balance
                    charged_fee    = transaction_fee_amount
                    total__balance = merchant_transaction.amount - charged_fee

                    if merchant_account_balance:
                        if merchant_account_balance.immature_balance < total__balance:
                            return json({'message': 'Insufficient Immature Balance'}, 400)

                        merchant_account_balance.immature_balance -= total__balance

                        session.add(merchant_account_balance)
                        session.add(merchant_transaction)


                elif schema.status == 'PAYMENT_PENDING':
                    # Pending the transaction after amount added into Mature fund
                    if merchant_transaction.pg_settlement_date:
                        if current_datetime > merchant_transaction.pg_settlement_date:
                            return json({'message': 'Amount has been credited to Mature fund'}, 400)
                        
                    return json({'message': 'Can not perform this action'}, 400)
                
                else:
                    return json({'message': 'Can not perform this action'}, 400)


                # elif schema.status == 'PAYMENT_INITIATED':

                #     if merchant_transaction.pg_settlement_date:
                #         if current_datetime > merchant_transaction.pg_settlement_date:
                #             return json({'message': 'Amount has been credited to Mature fund'}, 400)
                    
                #     return json({"message": "Can not perform this action"}, 400)
            

            ###################################
            ## Already ON HOLD Transactions ##
            ###################################
            elif merchant_transaction.status == 'PAYMENT_HOLD':

                # For Success transaction status
                if schema.status == 'PAYMENT_SUCCESS':

                    if not merchant_transaction.pg_settlement_period:
                        merchant_assigned_pipe_obj = await session.execute(select(PIPE).where(
                                PIPE.id == merchant_transaction.pipe_id
                        ))
                        merchant_assigned_pipe = merchant_assigned_pipe_obj.scalar()

                        pipe_settlement_time = merchant_assigned_pipe.settlement_period

                        if pipe_settlement_time:
                            pipe_settlement_period = merchant_assigned_pipe.settlement_period
                            numeric_period         = re.findall(r'\d+', pipe_settlement_period)

                        else:
                            pipe_settlement_period = '1 Days'
                            numeric_period         = re.findall(r'\d+', pipe_settlement_period)

                    else:
                        pipe_settlement_period  = merchant_transaction.pg_settlement_period
                        numeric_period          = re.findall(r'\d+', pipe_settlement_period)

                    if numeric_period:
                        settlement_period_value = int(numeric_period[0])
                    else:
                        settlement_period_value = 0


                    # Calculate settlement date
                    transaction_settlement_date = current_datetime + timedelta(days=settlement_period_value)

                    merchant_transaction.balance_status     = 'Immature'
                    merchant_transaction.pg_settlement_date = transaction_settlement_date

                    # Calculate the amount to be credited into merchant account
                    # Transfer the amount into forzen balance
                    charged_fee    = transaction_fee_amount
                    total__balance = merchant_transaction.amount - charged_fee

                    if merchant_account_balance:

                        if merchant_account_balance.frozen_balance < total__balance:
                            return json({'message': 'Insufficient Frozen balance'}, 400)
                        
                        merchant_account_balance.frozen_balance   -= total__balance
                        merchant_account_balance.immature_balance += total__balance

                        session.add(merchant_account_balance)
                        session.add(merchant_transaction)

                # Holding the payment
                elif schema.status == 'PAYMENT_HOLD':
                    return json({'message': 'Already added balance to Fronzen fund'}, 400)


                # If the payment staus is Failed
                elif schema.status == 'PAYMENT_FAILED':

                    charged_fee    = transaction_fee_amount
                    total__balance = merchant_transaction.amount - charged_fee

                    if merchant_account_balance:
                        if merchant_account_balance.frozen_balance < total__balance:
                            return json({'message': 'Insufficient Frozen balance'}, 400)
                        
                        merchant_account_balance.frozen_balance -= total__balance

                        session.add(merchant_account_balance)
                        session.add(merchant_transaction)

                else:
                    return json({'message': 'Can not perform this action'}, 400)
                

            ###############################
            ## Already FAILED Transactions
            ###############################
            elif merchant_transaction.status == 'PAYMENT_FAILED':

                # Reapproving the transaction
                if schema.status == 'PAYMENT_SUCCESS':
                    merchant_transaction.is_completd = True

                    await CalculateMerchantAccountBalance(
                        merchant_transaction.amount, 
                        merchant_transaction.currency, 
                        merchant_transaction.transaction_fee, 
                        merchant_transaction.merchant_id
                    )
                    session.add(merchant_transaction)

                else:
                    return json({'message': 'Can not perform this action'}, 400)

            
            ################################
            ## Already Pending Transactions
            ################################
            elif merchant_transaction.status == 'PAYMENT_PENDING':

                if schema.status == 'PAYMENT_HOLD':
                    return json({'message': 'Can not hold pending transaction'}, 400)
                
                else:
                    return json({'message': 'Can not perform this action'}, 400)
                


            # Update the transaction with details
            merchant_transaction.amount               = schema.amount
            merchant_transaction.currency             = schema.currency
            merchant_transaction.merchantCallBackURL  = schema.webhook_url
            merchant_transaction.merchantRedirectURl  = schema.redirect_url
            merchant_transaction.merchantMobileNumber = schema.mobile_number
            merchant_transaction.merchantPaymentType  = schema.payment_type
            merchant_transaction.status               = schema.status
            merchant_transaction.transaction_fee      = transactionFee
            merchant_transaction.fee_amount           = transaction_fee_amount
            

            session.add(merchant_transaction)
            await session.commit()  
            await session.refresh(merchant_transaction)

            # To avoid greenlet spawn error
            if merchant_account_balance:
                await session.refresh(merchant_account_balance)


            return json({
                'success': True, 
                'message': 'Updated Successfully'
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Export all Merchant Production Transactions
@auth('userauth')
@get('/api/v2/admin/merchant/pg/export/transactions/')
async def export_merchant_pg_production_transaction(request: Request):
    """
        Export all Merchant Production PG Production Transactions by Admin.<br/><br/>

        Parameters:<br/>
            request (Request): The incoming HTTP request.<br/><br/>

        Returns:<br/>
            JSON: A JSON response containing the list of Merchant Production PG Production Transactions.<br/>
            `success`(boolean): The transaction succuess status.<br/>
            `message`(string): The transaction message.<br/>
            `ExportmerchantPGTransaction`(list): The list of Merchant Production PG Production Transactions.<br/><br/>

        Raises:<br/>
            Exception: If any error occurs during the database query or response generation.<br/><br/>

        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
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
    """
        This API endpoint is used to export all the Merchant Sandbox transactions by an admin.<br/><br/>

        Parameters:<br/>
            - request: HTTP Request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the exported Merchant Sandbox transactions, success status code.<br/><br/>

        Error message:<br/>
            - JSON: A JSON response indicating the success or failure of the operation.<br/>
            - On success: {'success': True,'message': 'Transaction fetched successfuly', 'ExportmerchantPGSBTransaction': Exported data}.<br/>
            - On failure: {'message': 'Error message'} with appropriate HTTP status code.<br/><br/>
        
        Raises:<br/>
        - Exception: If any error occurs during the database query or response generation.<br/>
    """
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
    """
        This API Endpoint let admin Search merchant pg transactions.<br/><br/>

        Parameters:<br/>
            - request (Request): Request object<br/>
            - query (str): Search query<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the following keys:<br/>
            - success (bool): A boolean indicating the success of the operation.<br/>
            - admin_merchant_searched_prod_transactions (list): A list of dictionaries, each representing a transaction.<br/>
            - message (str): An error message in case of any exceptions.<br/><br/>

        Error Messages:<br/>
            - Error 401: Unauthorized Access<br/>
            - Error 500: Server Error<br/>
            - Error 404: No Transaction Found<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 401: Unauthorized Access<br/>
            - Error 500: Server Error<br/>
            - Error 404: No Transaction Found<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id') if user_identity else None

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

            # Search transaction Business Name wise
            merchant_business_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.business_name == search_query
            ))
            merchant_business = merchant_business_obj.scalars().all()

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

            
            # Execute Conditions
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
            
            # Get the user id
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
                    'business_name': transaction.business_name
                })

            return json({'success': True, 'admin_merchant_searched_prod_transactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



## Every merchant transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/distinct/transactions/')
async def merchant_pg_transaction(request: Request, query: int, limit: int = 15, offset: int = 0):
    """
        Admin will be able to View PG Transaction transactions details of any specific merchant.<br/><br/>

        Parameters:<br/>
            request (Request): Request object<br/>
            query (int): Merchant ID<br/>
            limit (int, optional): Number of transactions per page. Defaults to 15.<br/>
            offset (int, optional): Offset for pagination. Defaults to 0.<br/><br/>

        Returns:<br/>
            JSON: A JSON response containing the success status, all PG transaction details, and total row count.<br/>
            If any error occurs, a JSON response with error status and error message is returned.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
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

            # Count merchant transactions
            count_stmt = select(func.count(MerchantProdTransaction.id)).where(MerchantProdTransaction.merchant_id == merchant_id)
            exec_count = await session.execute(count_stmt)
            total_transactions_count = exec_count.scalar()

            total_merchant_transaction_count = total_transactions_count / limit


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
            ).order_by(
                desc(MerchantProdTransaction.id)
            ).limit(limit).offset(offset)


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

            return json({
                'success': True, 
                'distinct_merchant_transaction': combined_data,
                'total_row_count': total_merchant_transaction_count
                }, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    





# Filter All production transaction
@auth('userauth')
@post('/api/v2/admin/filter/merchant/transaction/')
async def filter_merchant_pg_production_transaction(request: Request, schema: AllTransactionFilterSchema, limit: int = 10, offset: int = 0):
    """
        Filter all production transaction based on the provided filters.<br/>
        The filters are: date, transaction_id, transaction_amount, business_name, start_date, and end_date.
        Returns paginated results.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object containing the payload data.<br/>
            - schema (AllTransactionFilterSchema): The schema object containing the filter parameters.<br/>
            - limit (int): The maximum number of results to return. Default is 10.<br/>
            - offset (int): The offset for pagination. Default is 0.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the following keys and values:<br/>
            -'success': True if the operation was successful.<br/>
            - 'AdminmerchantPGTransactions': A list of dictionaries containing details of filtered production transactions.<br/>
            - 'paginated_count': The total number of pages based on the provided limit.<br/><br/>
            
        Raises:<br/>
            - HTTPException: If the request payload is invalid or if the user is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/><br/>
        
        Error message:<br/>
            - 401: Unauthorized.<br/>
            - 500: Internal Server Error.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            # Authenticate Admin
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization failed'}, 401)
            # Admin authentication ends

            combined_data = []

            ### Get The payload data
            date_time          = schema.date
            transactionID      = schema.transaction_id
            transaction_amount = schema.transaction_amount
            business_name      = schema.business_name
            startDate          = schema.start_date
            endDate            = schema.end_date

            conditions = []
            transaction_count = 0
            paginated_value = 0


            stmt = select(
                MerchantProdTransaction
            ).order_by(
                desc(MerchantProdTransaction.id)
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
                        MerchantProdTransaction.createdAt >= start_date,
                        MerchantProdTransaction.createdAt < (end_date + timedelta(days=1))
                    )
                )

            elif date_time:
                start_date, end_date = get_date_range(date_time)

                conditions.append(
                    and_(
                        MerchantProdTransaction.createdAt >= start_date,
                        MerchantProdTransaction.createdAt <= end_date
                    )
                )
            
            ## Filter according to transaction ID
            if transactionID:
                conditions.append(
                    MerchantProdTransaction.transaction_id.like(f"{transactionID}%")
                )

            ## Filter according to transaction Amount
            if transaction_amount:
                transaction_amount = float(schema.transaction_amount)
                conditions.append(
                    MerchantProdTransaction.amount == transaction_amount
                )
            
            ## Filter according to business Name
            if business_name:
                conditions.append(
                    MerchantProdTransaction.business_name.like(f"{business_name}%") 
                )

            if conditions:
                statement = stmt.where(and_(*conditions))

                merchant_transactions_obj = await session.execute(statement)
                merchant_transactions     = merchant_transactions_obj.scalars().all()

                ### Count paginated value
                count_transaction_stmt = select(func.count()).select_from(MerchantProdTransaction).where(
                    *conditions
                )
                transaction_count = (await session.execute(count_transaction_stmt)).scalar()

                paginated_value = transaction_count / limit

                if not merchant_transactions:
                    return json({'message': 'No transaction found'}, 404)
                
            else:
                return json({'message': 'No data found'}, 404)
            
            # Get all the users
            user_obj   = await session.execute(select(Users))
            users      = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            # Loop through the transaction
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
                    'transaction_fee': transactions.transaction_fee,
                    'business_name': transactions.business_name
                })

            return json({
                'success': True, 
                'message': 'Transaction fetched successfuly', 
                'AdminmerchantPGTransactions': combined_data,
                'paginated_count': paginated_value
                
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    
