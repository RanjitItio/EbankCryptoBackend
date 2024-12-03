from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from Models.models import Users, Wallet, Currency
from Models.crypto import CryptoBuy, CryptoSell, CryptoWallet
from sqlmodel import select, desc, and_, func
from Models.Crypto.schema import AdminUpdateCryptoBuySchema, AdminUpdateCryptoSellSchema, AdminFilterCryptoTransactionsSchema
from app.dateFormat import get_date_range
from datetime import datetime, timedelta




## Crypto Buy Controller
class CryptoBuyController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Update Crypto Deposit'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/admin/crypto/buy/'
    
    
    ## Update Crypto Deposites by Admin
    @auth('userauth')
    @put()
    async def update_cryptoDeposit(self, request: Request, schema: AdminUpdateCryptoBuySchema):
        """
            Update the status of a crypto deposit transaction by an admin user.<br/>
            This function authenticates the admin user, verifies the validity of the transaction and wallets,
            and updates the transaction status and wallet balances accordingly.<br/>
            This function allows an admin to update the status of a crypto deposit transaction.<br/><br/>

            Parameters:<br/>
            - request (Request): The incoming HTTP request object containing user identity information.<br/>
            - schema (AdminUpdateCryptoBuySchema): The schema containing the crypto_buy_id and the new status.<br/><br/>

            Returns:<br/>
            - JSON response with success or error message, along with HTTP status code.<br/><br/>

            Error message:<br/>
                JSON: A JSON response indicating the success or failure of the operation.<br/>
                - On success: {'success': True, 'message': 'Updated Successfully'}<br/>
                - On failure: {'message': 'Error message'} with appropriate HTTP status code.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin authentication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ## Get payload Data
                cryptoBuyId = schema.crypto_buy_id
                status      = schema.status

                ## Get The crypto buy transactions
                user_crypto_buy_transaction_obj = await session.execute(select(CryptoBuy).where(
                    CryptoBuy.id == cryptoBuyId
                ))
                user_crypto_buy_transaction = user_crypto_buy_transaction_obj.scalar()

                if not user_crypto_buy_transaction:
                    return json({'message': 'Invalid Transaction'}, 400)
                
                ## Crypto Wallet Validation
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == user_crypto_buy_transaction.crypto_wallet_id
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 400)
                
                ## Fiat Wallet Validation
                user_fiat_wallet_obj = await session.execute(select(Wallet).where(
                    Wallet.id == user_crypto_buy_transaction.wallet_id
                ))
                user_fiat_wallet = user_fiat_wallet_obj.scalar()

                if not user_fiat_wallet:
                    return json({'message': 'Invalid FIAT wallet'}, 400)
                
                ### Calculte total amount to deduct
                amount_buy      = user_crypto_buy_transaction.buying_amount
                transaction_fee = user_crypto_buy_transaction.fee_value

                total_deduct_amount = amount_buy + transaction_fee

                ## Balance Validation
                if user_fiat_wallet.balance <= total_deduct_amount:
                    return json({'message': 'Insufficient funds'}, 400)
                
                ## Already Approved
                if user_crypto_buy_transaction.is_approved:
                    return json({'message': 'Already approved'}, 400)
                

                if status == 'Approved':
                    ## Add crypto into Crypto wallet
                    user_crypto_wallet.balance += user_crypto_buy_transaction.crypto_quantity

                    ### Deduct from FIAT Wallet
                    user_fiat_wallet.balance -= total_deduct_amount

                    ## Save into CryptoBuy Table
                    user_crypto_buy_transaction.status      = 'Approved'
                    user_crypto_buy_transaction.is_approved = True

                    session.add(user_fiat_wallet)
                    session.add(user_crypto_wallet)
                    session.add(user_crypto_buy_transaction)

                else:
                    user_crypto_buy_transaction.status      = status
                    user_crypto_buy_transaction.is_approved = False

                    session.add(user_crypto_buy_transaction)

                await session.commit()
                await session.refresh(user_fiat_wallet)
                await session.refresh(user_crypto_wallet)
                await session.refresh(user_crypto_buy_transaction)

                return json({
                    'success': True,
                    'message': 'Updated successfully'
                }, 200)


        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)




## Crypto Sell Controller
class CryptoSellController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Update Crypto Deposit'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/admin/crypto/sell/'
    
   
    ## Update Crypto Sell by Admin
    @auth('userauth')
    @put()
    async def update_cryptoSell(self, request: Request, schema: AdminUpdateCryptoSellSchema):
        """
            This function allows an admin to update the status of a crypto sell transaction.<br/>
            This function authenticates the admin user, verifies the validity of the transaction and wallets,
            and updates the transaction status and wallet balances accordingly.<br/><br/>
            
            Parameters:<br/>
                - request (Request): The HTTP request object containing the user's identity.<br/>
                - schema (AdminUpdateCryptoSellSchema): The schema containing the crypto_sell_id and status to be updated.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response indicating the success or failure of the operation.<br/>
                - On success: {'success': True,'message': 'Updated Successfully'}<br/>
                - On failure: {'message': 'Error message'} with appropriate HTTP status code.<br/><br/>

            Error message:<br/>
                - Error 401: 'Unauthorized'<br/>
                - Error 404: 'Invalid Transaction' or 'Invalid Crypto Wallet'<br/>
                - Error 500: 'Server Error'<br/><br/>

            Raises:<br/>
                - Exception: If any error occurs during the database query or response generation.<br/>
                - Error 401: 'Unauthorized'<br/>
                - Error 404: 'Invalid Transaction' or 'Invalid Crypto Wallet'<br/>
                - Error 500: 'Server Error'<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                ## Admin authentication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ## Get payload data
                cryptoSellId = schema.crypto_sell_id
                status      = schema.status

                ## Get The crypto sell transactions
                user_crypto_sell_transaction_obj = await session.execute(select(CryptoSell).where(
                    CryptoSell.id == cryptoSellId
                ))
                user_crypto_sell_transaction = user_crypto_sell_transaction_obj.scalar()

                if not user_crypto_sell_transaction:
                    return json({'message': 'Invalid Transaction'}, 404)
                
                ## Crypto Wallet Validation
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == user_crypto_sell_transaction.crypto_wallet_id
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 400)
                
                ## Fiat Wallet Validation
                user_fiat_wallet_obj = await session.execute(select(Wallet).where(
                    Wallet.id == user_crypto_sell_transaction.wallet_id
                ))
                user_fiat_wallet = user_fiat_wallet_obj.scalar()

                if not user_fiat_wallet:
                    return json({'message': 'Invalid FIAT wallet'}, 400)
                

                ### Calculate the amount to deduct
                crypto_sell_quantity = user_crypto_sell_transaction.crypto_quantity
                sell_transaction_fee = user_crypto_sell_transaction.fee_value

                toal_crypto_deduct = crypto_sell_quantity + sell_transaction_fee


                ## Balance Validation
                if user_crypto_wallet.balance <= toal_crypto_deduct:
                    return json({'message': 'Insufficient funds'}, 400)
                
                ## Already Approved
                if user_crypto_sell_transaction.is_approved:
                    return json({'message': 'Already approved'}, 400)
                

                if status == 'Approved':
                   
                    ## Deduct from crypto into Crypto wallet
                    user_crypto_wallet.balance -= toal_crypto_deduct

                    ## Add into fiat Wallet
                    user_fiat_wallet.balance += user_crypto_sell_transaction.received_amount

                    ## Save into CryptoBuy Table
                    user_crypto_sell_transaction.status = 'Approved'
                    user_crypto_sell_transaction.is_approved = True

                    session.add(user_fiat_wallet)
                    session.add(user_crypto_wallet)
                    session.add(user_crypto_sell_transaction)

                else:
                    user_crypto_sell_transaction.status      = status
                    user_crypto_sell_transaction.is_approved = False

                    session.add(user_crypto_sell_transaction)

                await session.commit()
                await session.refresh(user_fiat_wallet)
                await session.refresh(user_crypto_wallet)
                await session.refresh(user_crypto_sell_transaction)

                return json({
                    'success': True,
                    'message': 'Updated successfully'
                }, 200)


        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)



## Crypto Transaction Controller
class CryptoTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Crypto Transaction Controller'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/admin/crypto/transactions/'
    
    
    ## Get all crypto transactions
    @auth('userauth')
    @get()
    async def get_cryptoTransactions(self, request: Request,  limit: int = 5, offset: int = 0):
        """
            This function retrieves crypto buy and sell transactions with pagination and combines them into
            a single list.<br/><br/>

            Params:<br/>    
               - request(Request): The `request` parameter represents the HTTP request object
                                   that contains information about the incoming request, such as headers, query parameters, and the<br/>
                                   request body. It allows the function to access and process data sent by the client.<br/>
               - limit(int): The `limit` parameter specifies the maximum number of transactions to retrieve in a single request. It determines the number of<br/>
                             transactions that will be returned in the response. the default value for `limit` is set to 5, meaning, defaults to 5 transactions per page.<br/>
               - offset(int): The `offset` parameter is used to specify the starting point from which data should be retrieved. It determines how many records
                              to skip before fetching the data.<br/><br/>

            Returns:<br/>
                A JSON response containing the following keys:<br/>
                  - success(bool): Indicates if the operation was successful.<br/>
                  - pagination_count(float): The total number of pages based on the `limit`.<br/>
                  - admin_crypto_transactions(list): A list of dictionaries, each containing details of a crypto transaction.<br/>
                  - total_rows(int): The total number of records available for the admin user.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin authentication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                combined_transaction = []

                 ## Execute Buy Query
                buy_stmt = select(
                    CryptoBuy.id,
                    CryptoBuy.crypto_quantity,
                    CryptoBuy.payment_type,
                    CryptoBuy.buying_currency,
                    CryptoBuy.buying_amount,
                    CryptoBuy.fee_value,
                    CryptoBuy.created_at,
                    CryptoBuy.status,

                    CryptoWallet.crypto_name,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                ).join(
                    Users, Users.id == CryptoBuy.user_id
                ).order_by(
                    desc(CryptoBuy.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                # Execute Sell Query
                sell_stmt = select(
                    CryptoSell.id,
                    CryptoSell.crypto_quantity,
                    CryptoSell.payment_type,
                    CryptoSell.received_amount,
                    CryptoSell.fee_value,
                    CryptoSell.created_at,
                    CryptoSell.status,

                    CryptoWallet.crypto_name,

                    Wallet.currency.label('wallet_currency'),

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')

                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                ).join(
                    Wallet, Wallet.id == CryptoSell.wallet_id
                ).join(
                    Users, Users.id == CryptoSell.user_id
                ).order_by(
                    desc(CryptoSell.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ## Count total row of sell and Buy transactions
                buy_row_stmt = select(func.count(CryptoBuy.id))
                exec_buy_row_stmt = await session.execute(buy_row_stmt)

                sell_row_stmt = select(func.count(CryptoSell.id))
                exec_sell_row_stmt = await session.execute(sell_row_stmt)

                buy_row_count = exec_buy_row_stmt.scalar()
                sell_row_count = exec_sell_row_stmt.scalar()

                total_row_count = (buy_row_count + sell_row_count) / (2 * limit)

                ## Get all cryptoBuy Transactions of user
                crypto_buy_transaction_obj = await session.execute(buy_stmt)
                crypto_buy_transaction     = crypto_buy_transaction_obj.all()

                ## Get all cryptoSell Transactions of user
                crypto_sell_transaction_obj = await session.execute(sell_stmt)
                crypto_sell_transaction     = crypto_sell_transaction_obj.all()

                combined_transaction = [
                    {
                        'id': buyTransaction.id,
                        'type': 'Buy',
                        'crypto_name': buyTransaction.crypto_name,
                        'crypto_qty': buyTransaction.crypto_quantity,
                        'payment_mode': buyTransaction.payment_type,
                        'amount': buyTransaction.buying_amount,
                        'currency': buyTransaction.buying_currency,
                        'status': buyTransaction.status,
                        'created_at': buyTransaction.created_at,
                        'user_name': buyTransaction.user_name,
                        'user_email': buyTransaction.user_email,
                        'fee': buyTransaction.fee_value

                    } for buyTransaction in crypto_buy_transaction
                ] + [
                    {
                        'id': sellTransaction.id,
                        'type': 'Sell',
                        'payment_mode': sellTransaction.payment_type,
                        'crypto_name': sellTransaction.crypto_name,
                        'crypto_qty': sellTransaction.crypto_quantity,
                        'currency': sellTransaction.wallet_currency,
                        'amount': sellTransaction.received_amount,
                        'status': sellTransaction.status,
                        'created_at': sellTransaction.created_at,
                        'user_name': sellTransaction.user_name,
                        'user_email': sellTransaction.user_email,
                        'fee': sellTransaction.fee_value

                    } for sellTransaction in crypto_sell_transaction
                ]


                return json({
                    'success': True,
                    'crypto_transactions': combined_transaction,
                    'total_row_count': total_row_count
                }, 200)


        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
                }, 500) 
        
    
    ## Filter Crypto Transactions
    @auth('userauth')
    @post()
    async def filter_cryptoTransactions(self, request: Request, schema: AdminFilterCryptoTransactionsSchema, limit: int = 5, offset: int = 0):
        """
            This function filters crypto transactions based on various criteria
            such as date range, user email, crypto name, and status, and returns paginated results along
            with total count.<br/><br/>

            Parameters:<br/>
                - request(Request): The `request` parameter represents the HTTP request object that contains information about the incoming request such as headers,
                                    body, method, etc.<br/>
                - schema(AdminFilterCryptoTransactionsSchema): The `schema` parameter function represents the schema object that contains the filtering criteria for the crypto transactions. It includes
                          fields such as `date_range`, `user_email`, `crypto_name`, `status`, `start_date`, and `end_date`.<br/>
                - limit(int): The `limit` parameter determines the maximum number of transactions to retrieve in a single request. It is used for pagination,
                         allowing you to control how many transactions are returned per page or request. <br/>
                - offset(int): The `offset` parameter is used to specify the starting point from which data should be retrieved. It determines how many records
                               should be skipped from the beginning of the result set before returning data.<br/><br/>

            Returns:<br/>
            - JSON: A JSON response containing the following keys and values:<br/>
            - 'Success': True if the operation was successful<br/>
            - 'filtered_data': A list of crypto transaction data, including details such as transaction ID, type (Buy or Sell), crypto name, quantity, payment mode, amount, currency, status, creation date, user name, user email, and fee<br/>
            - 'paginated_count': True if pagination is applied to the result set<br/><br/>

            Raises ValueError:<br/>
            - If any invalid input is provided in the request parameters.<br/>
            - HTTPException: If the request payload is invalid or if the admin is not authenticated.<br/>
            - HTTPStatus: 400 Bad Request if the request payload is invalid.<br/>
            - HTTPException: If the admin is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/><br/>

            Exception:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin authentication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                combined_transaction = []
                buy_conditions  = []
                sell_conditions = []
                buy_count       = 0
                sell_count      = 0

                ## Get payload data
                dateRange       = schema.date_range
                userEmail       = schema.user_email
                cryptoName      = schema.crypto_name
                status          = schema.status
                startDate       = schema.start_date
                endDate         = schema.end_date


                ## Filter date range wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    buy_conditions.append(
                        and_(
                            CryptoBuy.created_at >= start_date,
                            CryptoBuy.created_at < (end_date + timedelta(days=1))
                        )
                    )

                    sell_conditions.append(
                        and_(
                            CryptoSell.created_at >= start_date,
                            CryptoSell.created_at < (end_date + timedelta(days=1))
                        )
                    )

                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    buy_conditions.append(
                        and_(
                            CryptoBuy.created_at >= start_date,
                            CryptoBuy.created_at <= end_date
                        )
                    )

                    sell_conditions.append(
                        and_(
                            CryptoSell.created_at >= start_date,
                            CryptoSell.created_at <= end_date
                        )
                    )
                
                ## Filter email wise
                if userEmail:
                    user_email_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{userEmail}%")
                    ))
                    user_email = user_email_obj.scalar()

                    if not user_email:
                         return json({'message': 'Invalid Email'}, 400)
                    
                    buy_conditions.append(
                        CryptoBuy.user_id == user_email.id
                    )

                    sell_conditions.append(
                        CryptoSell.user_id == user_email.id
                    )

                # Filter Crypto Name wise
                if cryptoName:
                    crypto_wallet_name_obj = await session.execute(select(CryptoWallet).where(
                        CryptoWallet.crypto_name.ilike(f"{cryptoName}%")
                    ))
                    crypto_wallet_name = crypto_wallet_name_obj.scalars().all()

                    buy_conditions.append(
                        CryptoBuy.crypto_wallet_id.in_([wallet.id for wallet in crypto_wallet_name])
                    )

                    sell_conditions.append(
                        CryptoSell.crypto_wallet_id.in_([wallet.id for wallet in crypto_wallet_name])
                    )

                if status:
                    buy_conditions.append(
                        CryptoBuy.status.ilike(f"{status}%")
                    )

                    sell_conditions.append(
                        CryptoSell.status.ilike(f"{status}%")
                    )

                ## Execute Buy Query
                buy_stmt = select(
                    CryptoBuy.id,
                    CryptoBuy.crypto_quantity,
                    CryptoBuy.payment_type,
                    CryptoBuy.buying_currency,
                    CryptoBuy.buying_amount,
                    CryptoBuy.fee_value,
                    CryptoBuy.created_at,
                    CryptoBuy.status,

                    CryptoWallet.crypto_name,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                ).join(
                    Users, Users.id == CryptoBuy.user_id
                ).order_by(
                    desc(CryptoBuy.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                # Execute Sell Query
                sell_stmt = select(
                    CryptoSell.id,
                    CryptoSell.crypto_quantity,
                    CryptoSell.payment_type,
                    CryptoSell.received_amount,
                    CryptoSell.fee_value,
                    CryptoSell.created_at,
                    CryptoSell.status,

                    CryptoWallet.crypto_name,

                    Wallet.currency.label('wallet_currency'),

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')

                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                ).join(
                    Wallet, Wallet.id == CryptoSell.wallet_id
                ).join(
                    Users, Users.id == CryptoSell.user_id
                ).order_by(
                    desc(CryptoSell.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )


                user_buy_transaction  = []
                user_sell_transaction = []

                ### Buy transaction fond
                if buy_conditions:
                    buy_statement = buy_stmt.where(and_(*buy_conditions))

                    user_buy_transaction_obj = await session.execute(buy_statement)
                    user_buy_transaction     = user_buy_transaction_obj.fetchall()

                    ### Count Buy Rows
                    buy_count_stmt = select(func.count()).select_from(CryptoBuy)
                    buy_count_stmt = buy_count_stmt.where(and_(*buy_conditions))
                    buy_count      = (await session.execute(buy_count_stmt)).scalar()

                ### If sell transaction Found
                if sell_conditions:
                    sell_statement = sell_stmt.where(and_(*sell_conditions))

                    user_sell_transactio_obj = await session.execute(sell_statement)
                    user_sell_transaction    = user_sell_transactio_obj.fetchall()

                    ### Count Sell rows
                    sell_count_stmt = select(func.count()).select_from(CryptoSell)
                    sell_count_stmt = sell_count_stmt.where(and_(*sell_conditions))
                    sell_count      = (await session.execute(sell_count_stmt)).scalar()

                if not user_buy_transaction and not user_sell_transaction:
                    return json({'message': 'No data found'}, 404)
                

                ### Count Paginated Value
                total_buy_sell_count = buy_count + sell_count
                paginated_count      = total_buy_sell_count / (limit * 2) if limit > 0 else 1


                ## Combine all the data
                combined_transaction = [
                    {
                        'id': buyTransaction.id,
                        'type': 'Buy',
                        'crypto_name': buyTransaction.crypto_name,
                        'crypto_qty': buyTransaction.crypto_quantity,
                        'payment_mode': buyTransaction.payment_type,
                        'amount': buyTransaction.buying_amount,
                        'currency': buyTransaction.buying_currency,
                        'status': buyTransaction.status,
                        'created_at': buyTransaction.created_at,
                        'user_name': buyTransaction.user_name,
                        'user_email': buyTransaction.user_email,
                        'fee': buyTransaction.fee_value

                    } for buyTransaction in user_buy_transaction
                ] + [
                    {
                        'id': sellTransaction.id,
                        'type': 'Sell',
                        'payment_mode': sellTransaction.payment_type,
                        'crypto_name': sellTransaction.crypto_name,
                        'crypto_qty': sellTransaction.crypto_quantity,
                        'currency': sellTransaction.wallet_currency,
                        'amount': sellTransaction.received_amount,
                        'status': sellTransaction.status,
                        'created_at': sellTransaction.created_at,
                        'user_name': sellTransaction.user_name,
                        'user_email': sellTransaction.user_email,
                        'fee': sellTransaction.fee_value

                    } for sellTransaction in user_sell_transaction
                ]


                return json({
                    'success': True,
                    'filtered_data': combined_transaction,
                    'paginated_count': paginated_count

                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        


## Export Crypto transaction controller for Admin
class ExportCryptoTransactionDataController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Crypto Transactions'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/admin/export/crypto/transactions/'
    
    
    ## Export all Crypto transactions
    @auth('userauth')
    @get()
    async def export_cryptoTransaction(self, request: Request):
        """
            This function exports combined cryptocurrency buy and sell transactions for an authenticated admin user.<br/><br/>

            Parameters:<br/>
            - request (Request): The HTTP request object.<br/><br/>
            
            Returns:<br/>
              - JSON response: A JSON object containing the combined transaction data for both crypto buy and sell transactions.<br/>
              - If the user is not an admin, returns a JSON response with an error message.<br/>
              - If no transactions are found, returns a JSON response with a 'No data found' message.<br/>
              - In case of an error, returns a JSON response with an error message.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                ## Admin authentication
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                combined_transaction = []

                 ## Execute Buy Query
                buy_stmt = select(
                    CryptoBuy.id,
                    CryptoBuy.crypto_quantity,
                    CryptoBuy.payment_type,
                    CryptoBuy.buying_currency,
                    CryptoBuy.buying_amount,
                    CryptoBuy.fee_value,
                    CryptoBuy.created_at,
                    CryptoBuy.status,

                    CryptoWallet.crypto_name,

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                ).join(
                    Users, Users.id == CryptoBuy.user_id
                ).order_by(
                    desc(CryptoBuy.id)
                )

                # Execute Sell Query
                sell_stmt = select(
                    CryptoSell.id,
                    CryptoSell.crypto_quantity,
                    CryptoSell.payment_type,
                    CryptoSell.received_amount,
                    CryptoSell.fee_value,
                    CryptoSell.created_at,
                    CryptoSell.status,

                    CryptoWallet.crypto_name,

                    Wallet.currency.label('wallet_currency'),

                    Users.full_name.label('user_name'),
                    Users.email.label('user_email')

                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                ).join(
                    Wallet, Wallet.id == CryptoSell.wallet_id
                ).join(
                    Users, Users.id == CryptoSell.user_id
                ).order_by(
                    desc(CryptoSell.id)
                )

                ## Get all cryptoBuy Transactions of user
                crypto_buy_transaction_obj = await session.execute(buy_stmt)
                crypto_buy_transaction     = crypto_buy_transaction_obj.all()

                ## Get all cryptoSell Transactions of user
                crypto_sell_transaction_obj = await session.execute(sell_stmt)
                crypto_sell_transaction     = crypto_sell_transaction_obj.all()

                combined_transaction = [
                    {
                        'id': buyTransaction.id,
                        'type': 'Buy',
                        'crypto_name': buyTransaction.crypto_name,
                        'crypto_qty': buyTransaction.crypto_quantity,
                        'payment_mode': buyTransaction.payment_type,
                        'amount': buyTransaction.buying_amount,
                        'currency': buyTransaction.buying_currency,
                        'status': buyTransaction.status,
                        'created_at': buyTransaction.created_at,
                        'user_name': buyTransaction.user_name,
                        'user_email': buyTransaction.user_email,
                        'fee': buyTransaction.fee_value

                    } for buyTransaction in crypto_buy_transaction
                ] + [
                    {
                        'id': sellTransaction.id,
                        'type': 'Sell',
                        'payment_mode': sellTransaction.payment_type,
                        'crypto_name': sellTransaction.crypto_name,
                        'crypto_qty': sellTransaction.crypto_quantity,
                        'currency': sellTransaction.wallet_currency,
                        'amount': sellTransaction.received_amount,
                        'status': sellTransaction.status,
                        'created_at': sellTransaction.created_at,
                        'user_name': sellTransaction.user_name,
                        'user_email': sellTransaction.user_email,
                        'fee': sellTransaction.fee_value

                    } for sellTransaction in crypto_sell_transaction
                ]

                return json({
                    'success': True,
                    'export_crypto_transactions_data': combined_transaction
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)

