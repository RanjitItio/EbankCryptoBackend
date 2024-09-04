from blacksheep.server.controllers import APIController
from blacksheep import Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from app.controllers.controllers import get
from Models.models2 import MerchantProdTransaction, MerchantSandBoxTransaction
from sqlmodel import select, and_, desc, cast, Time, Date, func, extract
from datetime import datetime, timedelta




# All transactions made by merchant in production
class MerchantProductionTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Production Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/prod/transactions/'
    
   
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request, limit: int = 10, offset: int = 0):
        # Authenticcate users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                combined_data = []

                # fetch all the transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.merchant_id == user_id
                ).order_by(MerchantProdTransaction.id.desc()).limit(limit).offset(offset)
            )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)
                
                # Count total rows
                count_stmt     = select(func.count(MerchantProdTransaction.id)).where(
                    MerchantProdTransaction.merchant_id == user_id
                    )
                total_rows_obj = await session.execute(count_stmt)
                total_rows     = total_rows_obj.scalar()

                total_rows_count = total_rows / limit


                for transaction in merchant_transactions:

                    combined_data.append({
                        "id": transaction.id,
                        "merchant_id": transaction.merchant_id,
                        "currency": transaction.currency,
                        "merchantMobileNumber": transaction.merchantMobileNumber,
                        "payment_mode": transaction.payment_mode,
                        "status": transaction.status,
                        "merchantPaymentType": transaction.merchantPaymentType,
                        "amount":transaction.amount,
                        "is_completd": transaction.is_completd,
                        "createdAt": transaction.createdAt,
                        "is_refunded": transaction.is_refunded,
                        "merchantOrderId": transaction.merchantOrderId,
                        "pipe_id": transaction.pipe_id,
                        "merchantRedirectURl": transaction.merchantRedirectURl,
                        "gateway_res": transaction.gateway_res,
                        "transaction_fee": transaction.transaction_fee,
                        "merchantRedirectMode": transaction.merchantRedirectMode,
                        "transaction_id": transaction.transaction_id,
                        "merchantCallBackURL": transaction.merchantCallBackURL
                    })

                return json({'msg': 'Success','total_rows': total_rows_count ,'merchant_prod_trasactions': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        


# All transactions made by merchant in production without limit
class MerchantAllProductionTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant All Production Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/month/prod/transactions/'
    

    @auth('userauth')
    @get()
    async def get_all_transactions(self, request: Request, month: str = False, currency: str = False):
        # Authenticate users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        # Month wise data
        if month:
            req_month      = datetime.strptime(month, '%B').month
            year           = datetime.now().year
            start_of_month = datetime(year, req_month, 1)
            end_of_month   = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)
        else:
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            end_of_month   = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

        try:
            async with AsyncSession(async_engine) as session:

                # Currency wise data
                if currency:
                    # Fetch transactions Currency wise
                    merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                        and_(MerchantProdTransaction.merchant_id == user_id,
                            MerchantProdTransaction.createdAt >= start_of_month,
                            MerchantProdTransaction.createdAt <= end_of_month,
                            MerchantProdTransaction.is_completd == True,
                            MerchantProdTransaction.currency    == currency
                            )))
                    merchant_transactions = merchant_transactions_object.scalars().all()
                else:
                    # Fetch transactions
                    merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                        and_(MerchantProdTransaction.merchant_id == user_id,
                            MerchantProdTransaction.createdAt >= start_of_month,
                            MerchantProdTransaction.createdAt <= end_of_month,
                            MerchantProdTransaction.is_completd == True
                            )
                        ))
                    merchant_transactions = merchant_transactions_object.scalars().all()
                
                return json({'msg': 'Success', 'merchant_all_prod_trasactions': merchant_transactions}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        



# All transactions made by merchant in Sandbox mode
class MerchantSandboxTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Sandbox Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/sandbox/transactions/'
    
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request, limit: int = 10, offset: int = 0):
        # Authenticate Users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # Fetch transactions
                merchant_transactions_object = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchant_id == user_id
                ).order_by(MerchantSandBoxTransaction.id.desc()).limit(limit).offset(offset)
            )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)
                
                # Count total rows
                count_stmt = select(func.count(MerchantSandBoxTransaction.id)).where(MerchantSandBoxTransaction.merchant_id == user_id)
                total_rows_obj = await session.execute(count_stmt)
                total_rows = total_rows_obj.scalar()

                total_rows_count = total_rows / limit

                return json({'msg': 'Success','total_rows': total_rows_count ,'merchant_sandbox_trasactions': merchant_transactions}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        


# Get Account balance of the Merchant
class MerchantAccountBalance(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Account Balace'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/account/balance/'
    
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request):
        # Authenticate Users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # fetch all the transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.merchant_id == user_id,
                         MerchantProdTransaction.is_completd == True,
                         )
                    )
                )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)

                # Calculate all the amount currency wise
                usd_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'USD')
                euro_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'EUR')
                inr_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'INR')

                return json({
                        'success': True, 
                        'usd_balance': usd_balance if usd_balance else 0,
                        'euro_balance': euro_balance if euro_balance else None,
                        'inr_balance': inr_balance if inr_balance else None,
                        }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


class ExportMerchantTransactions(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/merchant/export/transactions/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Export Merchant Transactions'
    

    @auth('userauth')
    @get()
    async def ExportMerchantTransactions(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate users
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Fetch Transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.merchant_id == user_id
                    )
                )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)
                
                return json({'success': True, 'export_merchant_all_prod_trasactions': merchant_transactions}, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Search merchant transaction
class SearchMerchantProductionTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Search Merchant Transactions'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/merchant/search/prod/transactions/'
    

    @auth('userauth')
    @get()
    async def SearchMerchantProdTransactions(self, request: Request, query: str):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id')

                search_query = query
                combined_data = []
                query_date = None
                query_time = None
                query_status = None

                if search_query == 'PAYMENT SUCCESS':
                    query_status = 'PAYMENT_SUCCESS'
                elif search_query == 'PAYMENT INITIATED':
                    query_status = 'PAYMENT_INITIATED'
                elif search_query == 'PAYMENT FAILED':
                    query_status = 'PAYMENT_FAILED'


                try:
                    query_date = datetime.strptime(search_query, "%d %B %Y").date()
                except ValueError:
                    pass

                try:
                    query_time = datetime.strptime(search_query, "%H:%M:%S.%f").time()
                except ValueError:
                    pass

                try:
                    query_as_float = float(query)  # If query is a number, try to convert
                except ValueError:
                    query_as_float = None
                
                # For Month Search
                try:
                    query_month = datetime.strptime(search_query, "%B").month
                except ValueError:
                    query_month = None

                if query_month:
                    merchant_month_obj = await session.execute(select(MerchantProdTransaction).where(
                        and_(extract('month', MerchantProdTransaction.createdAt) == query_month,
                            MerchantProdTransaction.merchant_id == user_id)
                    ))
                    merchant_month = merchant_month_obj.scalars().all()


                # Search transaction order wise
                merchant_order_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.merchantOrderId == search_query,
                         MerchantProdTransaction.merchant_id == user_id
                         )
                ))
                merchant_order = merchant_order_obj.scalars().all()

                # Search transaction transaction id wise
                merchant_transactionID_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.transaction_id == search_query,
                     MerchantProdTransaction.merchant_id == user_id
                     )
                ))
                merchant_transactionID = merchant_transactionID_obj.scalars().all()

                # Search transaction in MOP wise
                merchant_mop_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.payment_mode == search_query,
                     MerchantProdTransaction.merchant_id == user_id
                     )
                ))
                merchant_mop = merchant_mop_obj.scalars().all()

                # Search Transaction Amount wise
                merchant_amount_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.amount == query_as_float,
                         MerchantProdTransaction.merchant_id == user_id
                         )
                ))
                merchant_amount = merchant_amount_obj.scalars().all()

                # Search Transaction currency wise
                merchant_currency_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.currency == search_query,
                         MerchantProdTransaction.merchant_id == user_id
                         )
                ))
                merchant_currency = merchant_currency_obj.scalars().all()

                # Search transaction status wise
                merchant_status_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.status == query_status,
                         MerchantProdTransaction.merchant_id == user_id
                         )
                    ))
                merchant_status = merchant_status_obj.scalars().all()

                # Search Transaction by Date
                merchant_date_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(cast(MerchantProdTransaction.createdAt, Date) == query_date,
                            MerchantProdTransaction.merchant_id == user_id
                        )))
                merchant_date = merchant_date_obj.scalars().all()

                # Search Transaction by Time
                merchant_time_obj = await session.execute(select(MerchantProdTransaction).where(
                        and_(cast(MerchantProdTransaction.createdAt, Time) == query_time,
                            MerchantProdTransaction.merchant_id == user_id
                            )
                    ))
                merchant_time = merchant_time_obj.scalars().all()

                # Execute conditions
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
                elif merchant_month:
                    merchant_prod_transactions_obj = merchant_month
                else:
                    merchant_prod_transactions_obj = []

                # if not merchant_prod_transactions_obj:
                #     return json({'message': 'No transaction found'}, 404)
                

                for transaction in merchant_prod_transactions_obj:
                    combined_data.append({
                        'id': transaction.id,
                        'gateway_res': transaction.gateway_res,
                        'currency': transaction.currency,
                        'amount': transaction.amount,
                        'merchantOrderId': transaction.merchantOrderId,
                        'merchantRedirectMode': transaction.merchantRedirectMode,
                        'merchantMobileNumber': transaction.merchantMobileNumber,
                        'is_completd': transaction.is_completd,
                        'merchant_id': transaction.merchant_id,
                        'pipe_id': transaction.pipe_id,
                        'transaction_fee': transaction.transaction_fee,
                        'payment_mode': transaction.payment_mode,
                        'transaction_id': transaction.transaction_id,
                        'status': transaction.status,
                        'createdAt': transaction.createdAt,
                        'merchantRedirectURl': transaction.merchantRedirectURl,
                        'merchantCallBackURL': transaction.merchantCallBackURL,
                        'merchantPaymentType': transaction.merchantPaymentType
                    })

                return json({'success': True, 'merchant_searched_transactions': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

# Search Merchant Sandbox Transactions
class SearchMerchantSandboxTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Search Merchant Sandbox Transactions'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/merchant/search/sb/transactions/'
    
    @auth('userauth')
    @get()
    async def SearchMerchantSandBoxTransactions(self, request: Request, query: str):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id')

                search_query = query
                combined_data = []
                query_date = None
                query_time = None

                try:
                    query_date = datetime.strptime(search_query, "%d %B %Y").date()
                except ValueError:
                    pass

                try:
                    query_time = datetime.strptime(search_query, "%H:%M:%S.%f").time()
                except ValueError:
                    pass

                try:
                    query_as_float = float(query)  # If query is a number, try to convert
                except ValueError:
                    query_as_float = None

                # Search transaction order wise
                merchant_order_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.merchantOrderId == search_query,
                         MerchantSandBoxTransaction.merchant_id == user_id
                         )
                ))
                merchant_order = merchant_order_obj.scalars().all()

                # Search transaction transaction id wise
                merchant_transactionID_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.transaction_id == search_query,
                     MerchantSandBoxTransaction.merchant_id == user_id
                     )
                ))
                merchant_transactionID = merchant_transactionID_obj.scalars().all()

                # Search transaction in MOP wise
                merchant_mop_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.payment_mode == search_query,
                     MerchantSandBoxTransaction.merchant_id == user_id
                     )
                ))
                merchant_mop = merchant_mop_obj.scalars().all()

                # Search Transaction Amount wise
                merchant_amount_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.amount == query_as_float,
                         MerchantSandBoxTransaction.merchant_id == user_id
                         )
                ))
                merchant_amount = merchant_amount_obj.scalars().all()

                # Search Transaction currency wise
                merchant_currency_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.currency == search_query,
                         MerchantSandBoxTransaction.merchant_id == user_id
                         )
                ))
                merchant_currency = merchant_currency_obj.scalars().all()

                # Search transaction status wise
                merchant_status_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.status == search_query,
                         MerchantSandBoxTransaction.merchant_id == user_id
                         )
                ))
                merchant_status = merchant_status_obj.scalars().all()

                # Search Transaction by Date
                merchant_date_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(cast(MerchantSandBoxTransaction.createdAt, Date) == query_date,
                            MerchantSandBoxTransaction.merchant_id == user_id
                        )))
                merchant_date = merchant_date_obj.scalars().all()

                # Search Transaction by Time
                merchant_time_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                        and_(cast(MerchantSandBoxTransaction.createdAt, Time) == query_time,
                            MerchantSandBoxTransaction.merchant_id == user_id
                            )
                    ))
                merchant_time = merchant_time_obj.scalars().all()


                if merchant_order:
                    merchant_sb_transactions_obj = merchant_order
                elif merchant_transactionID:
                    merchant_sb_transactions_obj = merchant_transactionID
                elif merchant_mop:
                    merchant_sb_transactions_obj = merchant_mop
                elif merchant_amount:
                    merchant_sb_transactions_obj = merchant_amount
                elif merchant_currency:
                    merchant_sb_transactions_obj = merchant_currency
                elif merchant_status:
                    merchant_sb_transactions_obj = merchant_status
                elif merchant_date:
                    merchant_sb_transactions_obj = merchant_date
                elif merchant_time:
                    merchant_sb_transactions_obj = merchant_time
                else:
                    merchant_sb_transactions_obj = []

                if not merchant_sb_transactions_obj:
                    return json({'message': 'No transaction found'}, 404)
                

                for transaction in merchant_sb_transactions_obj:
                    combined_data.append({
                        'id': transaction.id,
                        'currency': transaction.currency,
                        'amount': transaction.amount,
                        'merchantOrderId': transaction.merchantOrderId,
                        'merchantRedirectMode': transaction.merchantRedirectMode,
                        'merchantMobileNumber': transaction.merchantMobileNumber,
                        'is_completd': transaction.is_completd,
                        'merchant_id': transaction.merchant_id,
                        'payment_mode': transaction.payment_mode,
                        'transaction_id': transaction.transaction_id,
                        'status': transaction.status,
                        'createdAt': transaction.createdAt,
                        'merchantRedirectURl': transaction.merchantRedirectURl,
                        'merchantCallBackURL': transaction.merchantCallBackURL,
                        'merchantPaymentType': transaction.merchantPaymentType
                    })

                return json({'success': True, 'merchant_searched_sb_transactions': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)