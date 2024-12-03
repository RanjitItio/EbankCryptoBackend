from app.controllers.controllers import get, post
from blacksheep.server.controllers import APIController
from blacksheep import Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantRefund
from Models.models2 import MerchantProdTransaction
from Models.models import Currency
from Models.PG.schema import MerchantCreateRefundSchema, FilterMerchantRefundSchema
from sqlmodel import select, and_, desc, func, cast, Date, Time, or_
from blacksheep import get as GET
from datetime import datetime, timedelta
import calendar





# Raise Refund by Merchants
class MerchantRaiseRefund(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Initiate Refund'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/merchant/refund/'
        
    
    # Initiate new Refund by Merchant
    @auth('userauth')
    @post()
    async def create_merchantRefund(self, request: Request, schema:MerchantCreateRefundSchema):
        """
            This API Endpoint Create a refund request for a merchant transaction,
            handling various validation checks and database operations.<br/><br/>

            Parameters:<br/>
                - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
                - schema(MerchantCreateRefundSchema): The schema object containing the transaction_id, comment, refund_amt.<br/><br/>

            Returns:<br/>
                - JSON response with success status, message if successful.<br/>
                - JSON response with error status and message if an exception occurs.<br/><br/>

            Raise:<br/>
                - Error Response status code 400 - "message": "Invalid Transaction ID".<br/>
                - Error Response status code 400 - "message": "Can not raise Refund request, Transaction has not completed yet".<br/>
                - Error Response status code 400 - "message": "Invalid Transaction Currency".<br/>
                - Error Response status code 400 - "message": "Refund amount should be less than or equal to Transaction amount".<br/>
                - Error Response status code 403 - "message": "Amount is greater than remaining refund amount".<br/>
                - Error Response status code 403 - "message": "All transaction amount has been refunded".<br/>
                - Error Response status code 500 - "error": "Server Error".<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Get the request payload value
                transactionID = schema.transaction_id
                comment       = schema.comment
                amount        = schema.refund_amt
                # instantRefund = schema.instant_refund

                # Get the transaction
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.transaction_id == transactionID
                ))
                merchant_prod_transaction  = merchant_prod_transaction_obj.scalar()

                if not merchant_prod_transaction:
                    return json({'message': 'Invalid Transaction ID'}, 400)
                
                # Only success transactions can be Refunded
                if merchant_prod_transaction.is_completd == False:
                    return json({'message': 'Can not raise Refund request, Transaction has not completed yet'}, 400)
                
                # Transaction Currency
                transaction_currency = merchant_prod_transaction.currency

                # Get the currency id
                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == transaction_currency
                ))
                currency = currency_obj.scalar()

                if not currency:
                    return json({'message': 'Invalid Transaction Currency'}, 400)
                

                # Refund amount should be less than or equal to transaction amount
                if merchant_prod_transaction.amount < amount:
                    return json({'message': 'Refund amount should be less than or equal to Transaction amount'}, 400)
                
                # Does the merchant raised refund for same transaction id before?
                previous_refund_obj = await session.execute(select(MerchantRefund).where(
                    and_(MerchantRefund.merchant_id    == user_id,
                         MerchantRefund.transaction_id == merchant_prod_transaction.id
                         )
                ))
                previous_refund = previous_refund_obj.scalars().all()

                if previous_refund:
                    sumAmount = 0.00
                    # Sum all the refund transaction amount
                    for refundAmount in previous_refund:
                        sumAmount += refundAmount.amount

                    if sumAmount + amount > merchant_prod_transaction.amount:
                        remaining_refunded_amount = merchant_prod_transaction.amount - sumAmount
                        
                        return json({'message': f'Amount is greater than remaining refund amount - {remaining_refunded_amount} {merchant_prod_transaction.currency}'}, 403)
                    
                    if sumAmount + amount == merchant_prod_transaction.amount:
                        merchant_prod_transaction.is_refunded = True

                    
                    # If sum amount is equal to transaction amount or greater than transaction amount
                    if sumAmount > merchant_prod_transaction.amount or sumAmount == merchant_prod_transaction.amount:
                        merchant_prod_transaction.is_refunded = True

                        return json({'message': 'All transaction amount has been refunded'}, 403)
                    

                # Create new refund request
                refund_request = MerchantRefund(
                    merchant_id     = user_id,
                    transaction_id  = merchant_prod_transaction.id,
                    amount          = amount,
                    currency        = currency.id,
                    comment         = comment,
                    is_completed    = False
                )

                session.add(refund_request)
                session.add(merchant_prod_transaction)
                await session.commit()
                await session.refresh(refund_request)
                await session.refresh(merchant_prod_transaction)

                return json({'success':True, 'message': 'Refund created successfully'}, 201)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
    
    
    # Get all the Merchant Refunds
    @auth('userauth')
    @get()
    async def get_merchantRefunds(self, request: Request, limit: int = 10, offset: int = 0):
        """
            This API Endpoint retrieves merchant refunds based on the user's identity, with pagination support and error handling.<br/><br/>

            Parameters:<br/>
               - request: The HTTP Request object.<br/>
               - limit(int, optional): The maximum number of refund requests to retrieve in a single query. Defaults to 10.<br/>
               - offset(int, optional): The starting point from which to retrieve data. Defaults to 0.<br/><br/>

            Returns:<br/>
                JSON: A JSON response containing the following keys and values:<br/>
                - 'total_count': The total number of refund requests retrieved based on the limit and offset.<br/>
                - 'merchant_refunds': A list of dictionaries, each containing details of a refund request.<br/>
                -'success': A boolean indicating whether the operation was successful.<br/><br/>

            Raise:<br/>
                HTTPException: 401 if the user is not authenticated.<br/>
                HTTPException: 403 if the user is not authorized to access this endpoint.<br/>
                HTTPException: 500 for any server-side errors.<br/>
                HTTPException: 404 if the refund transaction does not exist.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id = user_identity.claims.get('user_id')

                combined_data = []

                if limit < 0 or offset < 0:
                    return json({"message": "limit and offset value can not be negative"}, 400)
                
                # Count total rows
                count_stmt = select(func.count(MerchantRefund.id)).where(
                    MerchantRefund.merchant_id == user_id
                )
                total_rows_obj = await session.execute(count_stmt)
                total_rows = total_rows_obj.scalar()

                total_rows_count = total_rows / limit
                
                # Get all the refund made by the merchant
                stmt = select(MerchantRefund.id,
                              MerchantRefund.merchant_id,
                              MerchantRefund.instant_refund,
                              MerchantRefund.instant_refund_amount,
                              MerchantRefund.is_completed,
                              MerchantRefund.amount,
                              MerchantRefund.comment,
                              MerchantRefund.createdAt,
                              MerchantRefund.status,

                              Currency.name.label('currency_name'),
                              MerchantProdTransaction.transaction_id,
                              MerchantProdTransaction.currency.label('transaction_currency'),
                              MerchantProdTransaction.amount.label('transaction_amount'),

                              ).join(
                                  Currency, Currency.id == MerchantRefund.currency
                              ).join(
                                  MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                              ).where(
                                  MerchantRefund.merchant_id == user_id
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
                        # 'instant_refund': refunds.instant_refund,
                        # 'instant_refund_amount': refunds.instant_refund_amount,
                        'is_completed': refunds.is_completed,
                        'transaction_id': refunds.transaction_id,
                        'amount': refunds.amount,
                        'transaction_amount': refunds.transaction_amount,
                        'createdAt': refunds.createdAt,
                        'status': refunds.status
                    })

                return json({'success': True, 'total_count': total_rows_count, 'merchant_refunds': combined_data}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Download all the refunds
@auth('userauth')
@GET('/api/v6/merchant/download/refunds/')
async def download_refunds(self, request: Request):
    """
        Export all Merchant Refund Transactions made by the merchant.<br/>
        Admin authentication is required to access this endpoint.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming HTTP request.<br/><br/>

        Returns:<br/>
           JSON: A JSON response containing the list of Merchant Refund Transactions.<br/>
            - `success`(boolean): The transaction succuess status.<br/>
            - `export_merchant_refunds`(list): The list of Merchant Refund Transactions.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 404: 'message': 'No refund requests available' <br/>
            - Error 500: 'error': 'Server Error'.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/><br/>

        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
            - Error 404: 'error': 'No refund requests available'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Get all the refund made by the merchant
            stmt = select(MerchantRefund.id,
                            MerchantRefund.instant_refund,
                            MerchantRefund.instant_refund_amount,
                            MerchantRefund.amount,
                            MerchantRefund.comment,
                            MerchantRefund.createdAt,
                            MerchantRefund.status,
                            Currency.name.label('currency_name'),
                            MerchantProdTransaction.transaction_id,
                            MerchantProdTransaction.currency.label('transaction_currency'),
                            MerchantProdTransaction.amount.label('transaction_amount'),
                            ).join(
                                Currency, Currency.id == MerchantRefund.currency
                            ).join(
                                MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                            ).where(
                                MerchantRefund.merchant_id == user_id
                            )
            
            merchant_refunds_obj = await session.execute(stmt)
            merchant_refunds = merchant_refunds_obj.fetchall()

            if not merchant_refunds:
                return json({'message': 'No refund requests available'}, 404)
            
            for refunds in merchant_refunds:
                combined_data.append({
                    'refund_amount': refunds.amount,
                    "refund_currency": refunds.currency_name,
                    'transaction_amount': refunds.transaction_amount,
                    "transaction_currency": refunds.transaction_currency,
                    'transaction_id': refunds.transaction_id,
                    'time': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'export_merchant_refunds': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



# Search Merchant Refunds
@auth('userauth')
@GET('/api/v6/merchant/search/refunds/')
async def search_merchant_refunds(request: Request, query: str):
    """
        Search Merchant Refund Transactions.<br/><br/>

        Parameters:<br/>
            query (str): Search query for refund details.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            JSON: A JSON response containing the following keys:<br/>
                - searched_merchant_refunds (list): List of refunds matching the search query.<br/>
                - total_refunds (int): Total number of refunds matching the search query.<br/>
                - error (str): Error message if any.<br/><br/>
        
        Error Messages:<br/>
            - Error 401: Unauthorized Access.<br/>
            - Error 500: Server Error.<br/>
            - Error 404: No refunds found.<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 401: Unauthorized Access<br/>
            - Error 500: Server Error<br/>
            - Error 404: No refunds found<br/>
    """
    user_identity = request.identity
    user_id       = user_identity.claims.get('user_id')

    try:
        async with AsyncSession(async_engine) as session:

            search_query = query
            conditions = []
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

            # Search transaction Id wise
            merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                and_(
                    MerchantProdTransaction.transaction_id == search_query,
                    MerchantProdTransaction.merchant_id == user_id
                    )
            ))
            merchant_transaction = merchant_transaction_obj.scalars().all()

            # Search Transaction Amount wise
            merchant_refund_amount_obj = await session.execute(select(MerchantRefund).where(
                and_(
                    MerchantRefund.amount == query_as_float,
                    MerchantRefund.merchant_id == user_id
                    )
                ))
            merchant_refund_amount = merchant_refund_amount_obj.scalars().all()

            # Search currency wise
            currency_obj = await session.execute(select(Currency).where(
                Currency.name == search_query
            ))
            currency = currency_obj.scalar()


            # Search transaction status wise
            merchant_refund_status_obj = await session.execute(select(MerchantRefund).where(
                and_(
                    MerchantRefund.status == search_query,
                    MerchantRefund.merchant_id == user_id
                    )
                ))
            merchant_refund_status = merchant_refund_status_obj.scalars().all()


            # # Search Transaction by Date
            # merchant_refund_date_obj = await session.execute(select(MerchantProdTransaction).where(
            #     cast(MerchantRefund.createdAt, Date) == query_date
            #         ))
            # merchant_refund_date = merchant_refund_date_obj.scalars().all()


            # Search Transaction by Time
            # merchant_refund_time_obj = await session.execute(select(MerchantProdTransaction).where(
            #         cast(MerchantRefund.createdAt, Time) == query_time
            #     ))
            # merchant_refund_time = merchant_refund_time_obj.scalars().all()


            # Build the main query with joins
            stmt = select(
                MerchantRefund.id,
                MerchantRefund.merchant_id,
                MerchantRefund.instant_refund,
                MerchantRefund.instant_refund_amount,
                MerchantRefund.is_completed,
                MerchantRefund.amount,
                MerchantRefund.comment,
                MerchantRefund.createdAt,
                MerchantRefund.status,

                Currency.name.label('currency_name'),
                MerchantProdTransaction.currency.label('transaction_currency'),
                MerchantProdTransaction.amount.label('transaction_amount'),
                MerchantProdTransaction.transaction_id
            ).join(
                Currency, Currency.id == MerchantRefund.currency
            ).join(
                MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
            ).where(
                MerchantRefund.merchant_id == user_id
            ).order_by(
                desc(MerchantRefund.id)
            )

            # Add conditions
            if merchant_transaction:
                conditions.append(MerchantRefund.transaction_id.in_([transaction.id for transaction in merchant_transaction]))

            elif merchant_refund_amount:
                conditions.append(MerchantRefund.amount == query_as_float)

            elif currency:
                conditions.append(MerchantRefund.currency == currency.id)

            elif merchant_refund_status:
                conditions.append(MerchantRefund.status == search_query)

            elif query_date:
                conditions.append(cast(MerchantRefund.createdAt, Date) == query_date)

            elif query_time:
                conditions.append(cast(MerchantRefund.createdAt, Time) == query_time)

            if conditions:
                stmt = stmt.where(or_(*conditions))

            merchant_refunds_object = await session.execute(stmt)
            merchant_refunds        = merchant_refunds_object.all()

            merchant_refunds_data = []

            for refunds in merchant_refunds:
                merchant_refunds_data.append({
                    'id': refunds.id,
                    "currency": refunds.currency_name,
                    "transaction_currency": refunds.transaction_currency,
                    "merchant_id": refunds.merchant_id,
                    'is_completed': refunds.is_completed,
                    'transaction_id': refunds.transaction_id,
                    'amount': refunds.amount,
                    'transaction_amount': refunds.transaction_amount,
                    'createdAt': refunds.createdAt,
                    'status': refunds.status
                })

            return json({'success': True, 'searched_merchant_refunds': merchant_refunds_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'messsage': f'{str(e)}'}, 500)






# Show all success refunds on Merchant dashboard chart
@auth('userauth')
@GET('/api/merchant/dash/refund/chart/')
async def MerchantSuccessRefundChart(request: Request):
    """
        Get all success refund transactions of merchant of current month.<br/><br/>

        Parameters:<br/>
             - request (Request): The request object containing user identity and other relevant information.<br/><br/>

        Returns:<br/>
             - JSON: A JSON response containing the success status and the list of refund transactions(merchant_refunds).<br/>
             - JSON: A JSON response containing error status and error message if any.<br/><br/>

        Raises:<br/>
             - Exception: If any error occurs during the database operations or processing.<br/><br/>
        
        Error Messages:<br/>
            - Unauthorized: If the user is not authenticated.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authnticate users
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

            # Get all the refunds of the user
            merchantSuccessRefundsObject = await session.execute(select(MerchantRefund).where(
                and_(MerchantRefund.merchant_id == user_id,
                     MerchantRefund.is_completed == True,
                     MerchantRefund.createdAt >= start_of_month,
                     MerchantRefund.createdAt <= end_of_month
                     )
                ))
            merchantSuccessRefunds = merchantSuccessRefundsObject.scalars().all()

            return json({'success': True, 'merchant_refunds': merchantSuccessRefunds}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    



# Merchant Refund Transaction Filter
class FilterMerchantRefunds(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "Merchant Filter Refund Transaction"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/filter/merchant/pg/refund/'
    

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
    
    #### Filter merchant Refunds
    @auth('userauth')
    @post()
    async def filter_merchant_refund(self, request: Request, schema: FilterMerchantRefundSchema, limit: int = 10, offset: int = 0):
        """
            This API Endpoint filters merchant refund data based on various criteria and returns paginated results.<br/><br/>

            Parameters:<br/>
            - request (Request): The HTTP request object containing the payload data.<br/>
            - schema (FilterMerchantRefundSchema): The schema object containing the validated data.<br/>
            - limit: The maximum number of results to return per query. Defaults to 10.<br/>
            - offset: The number of records to skip before starting to return records. Defaults to 0.<br/><br/>

            Returns:<br/>
             JSON: A JSON object containing the following keys and values:<br/>
            - 'success': True if the operation was successful.<br/>
            - 'merchant_refunds': A list of dictionaries containing details of merchant refunds.<br/>
            - 'pagination_count': The total number of pages based on the limit.<br/><br/>
            
            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error Response status code 400 - "msg": "Missing request payload".<br/>
            - Error Response status code 400 - "msg": "Invalid Transaction ID".<br/>
            - Error Response status code 404 - "msg": "No refund requests available".<br/>
            - Error Response status code 500 - "error": "Server Error".
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                # Get the payload data
                date_time     = schema.date
                transactionId = schema.transaction_id
                refundAmount  = schema.refund_amount
                status        = schema.status
                startDate     = schema.start_date
                endDate       = schema.end_date

                conditions = []
                paginated_value = 0

                # Select table
                stmt = select(
                    MerchantRefund.id,
                    MerchantRefund.merchant_id,
                    MerchantRefund.instant_refund,
                    MerchantRefund.instant_refund_amount,
                    MerchantRefund.is_completed,
                    MerchantRefund.amount,
                    MerchantRefund.comment,
                    MerchantRefund.createdAt,
                    MerchantRefund.status,

                    Currency.name.label('currency_name'),
                    MerchantProdTransaction.transaction_id,
                    MerchantProdTransaction.currency.label('transaction_currency'),
                    MerchantProdTransaction.amount.label('transaction_amount'),

                    ).join(
                        Currency, Currency.id == MerchantRefund.currency
                    ).join(
                        MerchantProdTransaction, MerchantProdTransaction.id == MerchantRefund.transaction_id
                    ).where(
                        MerchantRefund.merchant_id == user_id
                    ).order_by(
                        desc(MerchantRefund.id)
                    ).limit(
                        limit
                    ).offset(
                        offset
                    )
                
                # Filter Date wise
                if date_time and date_time == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            MerchantRefund.createdAt   >= start_date,
                            MerchantRefund.createdAt   < (end_date + timedelta(days=1))
                        ))

                elif date_time:
                    start_date, end_date = self.get_date_range(date_time)

                    conditions.append(
                        and_(
                            MerchantRefund.createdAt   >= start_date,
                            MerchantRefund.createdAt   <= end_date
                        ))
                
                # Search Status wise
                if status:
                    status = schema.status.capitalize()
                    
                    conditions.append(
                        and_(
                            MerchantRefund.status.like(f"{status}%")
                        )
                    )

                # Filter Transaction Wise
                if transactionId:
                    # Get the transaction ID
                    merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                        MerchantProdTransaction.transaction_id.like(f"{transactionId}%")
                    ))
                    merchant_prod_transaction = merchant_prod_transaction_obj.scalar()

                    if not merchant_prod_transaction:
                        return json({'message': 'Invalid Transaction ID'}, 400)

                    conditions.append(
                        and_(
                            MerchantRefund.merchant_id == user_id,
                            MerchantRefund.transaction_id == merchant_prod_transaction.id
                        )
                    )
                
                # Filter Refund amount wise
                if refundAmount:
                    refundAmount  = float(schema.refund_amount)

                    conditions.append(
                        and_(
                            MerchantRefund.merchant_id == user_id,
                            MerchantRefund.amount      == refundAmount
                        )
                    )
                
                # If data is available
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
                        return json({'message': 'No refund requests available'}, 404)
                    
                else:
                    return json({'message': 'No refund requests available'}, 400)
                
                
                ## Store all the data inside a list
                for refunds in merchant_refunds:
                    combined_data.append({
                        'id': refunds.id,
                        "currency": refunds.currency_name,
                        "transaction_currency": refunds.transaction_currency,
                        "merchant_id": refunds.merchant_id,
                        'is_completed': refunds.is_completed,
                        'transaction_id': refunds.transaction_id,
                        'amount': refunds.amount,
                        'transaction_amount': refunds.transaction_amount,
                        'createdAt': refunds.createdAt,
                        'status': refunds.status
                    })

                return json({
                    'success': True, 
                    'merchant_refunds': combined_data,
                    'paginated_count': paginated_value
                    
                    }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
