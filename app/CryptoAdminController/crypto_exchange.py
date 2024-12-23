from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from sqlmodel import select, and_, desc, func
from database.db import AsyncSession, async_engine
from Models.models import Users, Wallet
from Models.crypto import CryptoExchange, CryptoWallet
from Models.Admin.Crypto.schema import AdminUpdateCryptoExchange, AdminFilterCryptoExchangeSchema
from app.dateFormat import get_date_range
from datetime import datetime, timedelta




### Crypto Exchange Controller for Admin
class AdminCryptoExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Crypto Exchange Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/crypto/exchange/'
    
    
    ### Get all Crypto Exchange Data
    @auth('userauth')
    @get()
    async def get_adminCryptoExchanges(self, request: Request, limit: int = 10, offset: int = 0):
        """
        This function retrieves all crypto exchange transactions for admin users.<br/>
        It fetches data from the database, performs pagination, and returns the result in JSON format.<br/>
        
        Parameters:<br/>
        - request: The request object containing user identity and other relevant information.<br/>
        - limit: The maximum number of records to return per page. Default is 10.<br/>
        - offset: The number of records to skip before starting to return records. Default is 0.<br/><br/>

        Returns:<br/>
        - A JSON response containing the following keys:<br/>
          - success: A boolean indicating whether the request was successful.<br/>
          - admin_user_crypto_exchange_data: A list of dictionaries, each representing a crypto exchange transaction.<br/>
          - paginated_rows: The total number of pages available for pagination.<br/><br/>

        Raises:<br/>
        - Exception: If any error occurs during the database query or response generation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                combined_data = []

                ### Count all availble rows for paginated data
                select_rows  = select(func.count(CryptoExchange.id))
                execute_quey = await session.execute(select_rows)

                total_rows = execute_quey.scalar()

                paginated_rows = total_rows / limit

                ## Select the data
                stmt = select(
                    CryptoExchange.id,
                    CryptoExchange.user_id,
                    CryptoExchange.transaction_id,
                    CryptoExchange.created_at,
                    CryptoExchange.exchange_crypto_amount,
                    CryptoExchange.converted_fiat_amount,
                    CryptoExchange.status,
                    CryptoExchange.fee_value,

                    CryptoWallet.crypto_name,
                    Wallet.currency,

                    Users.email,
                    Users.full_name,
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).join(
                    Users, Users.id == CryptoExchange.user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                all_crypto_exchange_transaction_obj = await session.execute(stmt)
                all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

                if not all_crypto_exchange_transaction:
                    return json({'message': 'No transaction found'}, 404)
                

                for transaction in all_crypto_exchange_transaction:

                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'transaction_id': transaction.transaction_id,
                        'created_at': transaction.created_at,
                        'exchange_crypto_amount': transaction.exchange_crypto_amount,
                        'converted_fiat_amount': transaction.converted_fiat_amount,
                        'status': transaction.status,
                        'fee_value': transaction.fee_value,
                        'crypto_name': transaction.crypto_name,
                        'fiat_currency': transaction.currency,
                        'user_email': transaction.email,
                        'user_name': transaction.full_name
                    })


                return json({
                    'success': True,
                    'admin_user_crypto_exchange_data': combined_data,
                    'paginated_rows': paginated_rows
                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    
    #### Update Crypto Exchange Transaction
    @auth('userauth')
    @put()
    async def update_cryptoExchange(self, request: Request, schema: AdminUpdateCryptoExchange):
        """
        This function is responsible for updating the status of a crypto exchange transaction.<br/>
        It also handles the approval process, deducting the required amount from the user's crypto wallet
        and adding it to their fiat wallet.<br/><br/>

        Parameters:<br/>
        - request: The request object containing the user's identity and other relevant data.<br/>
        - schema: The schema object containing the updated status and transaction ID.<br/><br/>

        Returns:<br/>
        - A JSON response indicating success or failure, along with an appropriate message.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ### Get the payload data
                exchangeID = schema.exchange_id
                status     = schema.status

                ### Get The Crypto Exchange Transaction
                crypto_exchange_transaction_obj = await session.execute(select(CryptoExchange).where(
                    CryptoExchange.id == exchangeID
                ))
                crypto_exchange_transaction = crypto_exchange_transaction_obj.scalar()

                if not crypto_exchange_transaction:
                    return json({'message': 'Transaction not found'}, 404)
                
                ### Already approved
                if crypto_exchange_transaction.is_approved:
                    return json({'message': 'Transaction already approved'}, 400)
                
                ### Get The user Crypto Wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == crypto_exchange_transaction.crypto_wallet
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 404)
                
                ### Get the user FIAT Wallet
                user_fiat_wallet_obj = await session.execute(select(Wallet).where(
                    Wallet.id == crypto_exchange_transaction.fiat_wallet
                ))
                user_fiat_wallet = user_fiat_wallet_obj.scalar()

                if not user_fiat_wallet:
                    return json({'message': 'Invalid FIAT wallet'}, 404)

                ### Calculate Total Amount
                totalAmount = crypto_exchange_transaction.exchange_crypto_amount + crypto_exchange_transaction.fee_value

                ### Insufficient balance validation
                if user_crypto_wallet.balance < totalAmount:
                    return json({'message': 'Insufficient funds'}, 400)
                

                if status == 'Approved':
                    crypto_exchange_transaction.status = status
                    crypto_exchange_transaction.is_approved = True

                    ### Deduct the amount from Crypto Wallet
                    user_crypto_wallet.balance -= totalAmount

                    ### Add into FIAT Wallet
                    user_fiat_wallet.balance += crypto_exchange_transaction.converted_fiat_amount

                    session.add(crypto_exchange_transaction)
                    session.add(user_crypto_wallet)
                    session.add(user_fiat_wallet)

                else:
                    crypto_exchange_transaction.status = status
                    crypto_exchange_transaction.is_approved = False

                    session.add(crypto_exchange_transaction)
                
                await session.commit()
                await session.refresh(crypto_exchange_transaction)
                await session.refresh(user_crypto_wallet)
                await session.refresh(user_fiat_wallet)

                return json({
                    'success': True, 
                    'message': 'Updated Successfully'
                    }, 200)
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        
    



### Export Crypto Exchange Transaction
class ExportCryptoExchangeTransactionsController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Crypto Exchange Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/export/crypto/exchange/'
    
    
    #### Export all crypto exchange transaction
    @auth('userauth')
    @get()
    async def export_crypto_exchange(self, request: Request):
        """
            This Python function exports crypto exchange transaction data after authenticating the user as an admin.<br/><br/>

            Parameters:<br/>
               - request: In this specific context, the `request` parameter is used to extract the identity of the user.
                          This identity is used to verify if the user making the request is authorized to access the endpoint.<br/><br/>
                          The `request` object allows access to the user's identity and other relevant data. <br/>

            Returns:<br/>
            - JSON response containing the success status and the exported exchange data.<br/>
            - JSON response containing success status and the exported exchange data, if the user is an admin.<br/>
            - JSON response containing error status and an error message, if the user is not an admin or if an exception occurs.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                combined_data = []

                ## Select the data
                stmt = select(
                    CryptoExchange.id,
                    CryptoExchange.user_id,
                    CryptoExchange.transaction_id,
                    CryptoExchange.created_at,
                    CryptoExchange.exchange_crypto_amount,
                    CryptoExchange.converted_fiat_amount,
                    CryptoExchange.status,
                    CryptoExchange.fee_value,

                    CryptoWallet.crypto_name,
                    Wallet.currency,

                    Users.email,
                    Users.full_name,
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).join(
                    Users, Users.id == CryptoExchange.user_id
                ).order_by(
                    desc(CryptoExchange.id)
                )
                
                all_crypto_exchange_transaction_obj = await session.execute(stmt)
                all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

                for transaction in all_crypto_exchange_transaction:
                    combined_data.append({
                        'Transaction_id': transaction.transaction_id,
                        'Created Date': transaction.created_at,
                        'Exchange Crypto Amount': transaction.exchange_crypto_amount,
                        'Converted FIAT Amount': transaction.converted_fiat_amount,
                        'Status': transaction.status,
                        'Transaction Fee': transaction.fee_value,
                        'Crypto Name': transaction.crypto_name,
                        'FIAT Currency': transaction.currency,
                        'User Email': transaction.email,
                        'User Name': transaction.full_name
                    })

                return json({
                    'success': True,
                    'exchange_export_data': combined_data 
                })
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        


#### Filter Crypto Exchange Transaction By Admin
class AdminFilterCryptoExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Filter Crypto Exchange Controller by Admin'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/admin/filter/crypto/exchange/transactions/'
    
    
    ### Filter Crypto Exchange Transaction
    @auth('userauth')
    @post()
    async def filter_cryptoExchange(self, request: Request, schema: AdminFilterCryptoExchangeSchema, limit: int = 10, offset: int = 0):
        """
            The filter_cryptoExchange function is responsible for filtering crypto exchange transactions based on various criteria 
            such as user email, status, date, and crypto name. It provides paginated results along with the total count of matching records.<br/><br/>
            
            Parameters:<br/>
              - request(Request): The incoming request object containing information about the client's request.<br/>
              - limit(int): The maximum number of results to return in a single query.<br/>
              - offset(int): The starting point from which to retrieve data in a paginated query.<br/>
              - schema(AdminFilterCryptoExchangeSchema): The schema containing the filtering criteria such as user email, status, date, and crypto name.<br/><br/>

            Returns:<br/>
              - A JSON response containing the following keys:<br/>
                -'success': A boolean indicating if the operation was successful<br/>
                - 'filtered_crypto_exchange_transaction': A list of dictionaries containing details of filtered crypto exchange transactions<br/>
                - 'paginated_count': The total count of paginated values<br/>
                - If an error occurs, it will return a JSON response with the keys: 'error': 'Server Error'<br/>
                - 'No data found' if no matching records are found<br/>
                - 'Invalid Email' if the provided email is not found in the database<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                ## Admin authentication ends

                ### Get the payload data
                dateTime    = schema.dateTime
                user_email  = schema.email
                crypto_name = schema.crypto
                status      = schema.status
                startDate   = schema.start_date
                endDate     = schema.end_date

                conditions    = []
                combined_data = []
                exchange_count = 0


                ### Get the user email
                if user_email:
                    crypto_user_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{user_email}%")
                    ))
                    crypto_user = crypto_user_obj.scalar()

                    if not crypto_user:
                        return json({'message': 'Invalid Email'}, 400)
                
                    
                stmt = select(
                    CryptoExchange.id,
                    CryptoExchange.user_id,
                    CryptoExchange.transaction_id,
                    CryptoExchange.created_at,
                    CryptoExchange.exchange_crypto_amount,
                    CryptoExchange.converted_fiat_amount,
                    CryptoExchange.status,
                    CryptoExchange.fee_value,

                    CryptoWallet.crypto_name,
                    Wallet.currency,

                    Users.email,
                    Users.full_name,
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).join(
                    Users, Users.id == CryptoExchange.user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )


                ## Mail filter
                if user_email:
                    conditions.append(
                        CryptoExchange.user_id == crypto_user.id
                    )
                
                ### Status wise Filter
                if status:
                    conditions.append(
                        CryptoExchange.status == status
                    )
                
                ### Filter Date Time Wise
                if dateTime and dateTime == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            CryptoExchange.created_at >= start_date,
                            CryptoExchange.created_at < (end_date + timedelta(days=1))
                        )
                    )
                    
                elif dateTime:
                    start_date, end_date = get_date_range(dateTime)

                    conditions.append(
                        and_(
                            CryptoExchange.created_at <= end_date,
                            CryptoExchange.created_at >= start_date
                        )
                    )
                
                ### Flter Crypto Name wise
                if crypto_name:
                    crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                        CryptoWallet.crypto_name == crypto_name
                    ))
                    crypto_wallet = crypto_wallet_obj.scalars().all()

                    if not crypto_wallet:
                        return json({'message': 'No data found'}, 404)
                    
                    conditions.append(
                        CryptoExchange.crypto_wallet.in_([wallet.id for wallet in crypto_wallet])
                    )
                
                ### IF data found
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    all_crypto_exchange_transaction_obj = await session.execute(statement)
                    all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

                     ### Count Swap Rows
                    exchange_count_stmt = select(func.count()).select_from(CryptoExchange)
                    exchange_count_stmt = exchange_count_stmt.where(and_(*conditions))
                    exchange_count      = (await session.execute(exchange_count_stmt)).scalar()

                    if not all_crypto_exchange_transaction:
                        return json({'message': 'No data found'}, 404)
                    
                else:
                    return json({'message': 'No data found'}, 404)
                
                ### Count Paginated Value
                total_swap_count = exchange_count
                paginated_count  = total_swap_count / limit if limit > 0 else 1
                

                ## Get all the data
                for transaction in all_crypto_exchange_transaction:
                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'transaction_id': transaction.transaction_id,
                        'created_at': transaction.created_at,
                        'exchange_crypto_amount': transaction.exchange_crypto_amount,
                        'converted_fiat_amount': transaction.converted_fiat_amount,
                        'status': transaction.status,
                        'fee_value': transaction.fee_value,
                        'crypto_name': transaction.crypto_name,
                        'fiat_currency': transaction.currency,
                        'user_email': transaction.email,
                        'user_name': transaction.full_name
                    })


                return json({
                    'success': True,
                    'filtered_crypto_exchange_transaction': combined_data,
                    'paginated_count': paginated_count

                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)