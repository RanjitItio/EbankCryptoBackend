from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from app.controllers.controllers import get
from database.db import AsyncSession, async_engine
from Models.models2 import MerchantSandBoxTransaction
from sqlmodel import select, desc, func, and_, cast, Date, Time
from datetime import datetime






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
        """
          This API Endpoint will return all the sandboxe transactions.<br/>
          The transactions are ordered by transaction_id in descending order.<br/><br/>

            Parameters:<br/>
                - request(Request): The HTTP request object containing identity and other relevant information.<br/>
                - limit(int, optional): The maximum number of transactions to return per page. Default is 10.<br/>
                - offset(int, optional): The number of transactions to skip before starting to retrieve logs. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON response containing the following keys:<br/>
                - msg(str): A boolean indicating whether the operation was successful.<br/>
                - merchant_sandbox_transactions(list): A list of dictionaries, each representing a transaction.<br/>
            - total_rows(int): The total number of transactions available for the merchant.<br/><br/>

            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
        """
        # Authenticate Users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # Fetch transactions
                merchant_transactions_object = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchant_id == user_id
                ).order_by(desc(MerchantSandBoxTransaction.id)).limit(limit).offset(offset)
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
        """
            This API Endpoint will return the sandbox transactions based on the provided query.<br/>
            The query can be a transaction id, merchant order id, or a date and time.<br/>
            The transactions are ordered by transaction_id in descending order.<br/><br/>

            Parameters:<br/>
                - request(Request): The HTTP request object containing identity and other relevant information.<br/>
                - query(str): The search query. Can be a transaction id, merchant order id, or a date and time.<br/><br/>

            Returns:<br/>
                - JSON response containing the following keys:<br/>
                - success(boolean): A boolean indicating whether the operation was successful.<br/>
                - merchant_searched_sb_transactions(list): A list of dictionaries, each representing a transaction.<br/><br/>

            Raises:<br/>
                - Exception: If any error occurs during the database query or response generation.<br/>
                - Error 500: 'error': 'Server Error'.<br/><br/>
           
            Error Messages:<br/>
                - Error 404: 'error': 'No transaction found'.<br/>
                - Error 500: 'error': 'Server Error'.<br/>
        """
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


                # Search transaction Business name wise
                merchant_business_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(
                        MerchantSandBoxTransaction.business_name == search_query,
                        MerchantSandBoxTransaction.merchant_id == user_id
                     )
                ))
                merchant_business = merchant_business_obj.scalars().all()

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

                elif merchant_business:
                    merchant_sb_transactions_obj = merchant_business

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
                        'merchantPaymentType': transaction.merchantPaymentType,
                        'business_name': transaction.business_name
                    })

                return json({'success': True, 'merchant_searched_sb_transactions': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)