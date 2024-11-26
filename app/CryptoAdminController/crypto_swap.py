from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from app.controllers.controllers import get, post, put
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.crypto import CryptoSwap, CryptoWallet
from sqlmodel import select, desc, func, and_
from sqlalchemy.orm import aliased
from Models.Crypto.schema import AdminUpdateCryptoSwap
from Models.Admin.Crypto.schema import AdminFilterCryptoSwapSchema
from datetime import timedelta, datetime
from app.dateFormat import get_date_range




### Crypto Swap Controller
class AdminCryptoSwapController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Crypto Swap'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/crypto/swap/'
    
     ##### Get Crypto Swap Transaction
    @auth('userauth')
    @get()
    async def get_swapTransactions(self, request: Request, limit: int = 10, offset: int = 0):
        """
        Retrieve and return a paginated list of crypto swap transactions for admin users.<br/>

        This function authenticates the admin user, fetches crypto swap transactions from the database,<br/>
        and returns the data in a paginated format. It joins data from CryptoSwap, Users, and CryptoWallet tables.<br/><br/>

        Args:<br/>
            request (Request): The incoming HTTP request object containing user identity information.<br/>
            limit (int, optional): The maximum number of records to return. Defaults to 10.<br/>
            offset (int, optional): The number of records to skip before starting to return. Defaults to 0.<br/><br/>

        Returns:<br/>
            JSON: A JSON response containing:<br/>
                - success (bool): Indicates if the operation was successful.<br/>
                - pagination_count (float): The total number of pages based on the limit.<br/>
                - admin_swap_data (list): A list of dictionaries, each containing details of a swap transaction.<br/>
                - total_rows (int): The total number of records available for the admin user.<br/><br/>
        Raises:<br/>
            HTTPException: 401 if the user is not an admin.<br/>
            HTTPException: 404 if no transactions are found.<br/>
            HTTPException: 500 for any server-side errors.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized Access'}, 401)
                ##Admin authentication ends

                fromCryptoWallet = aliased(CryptoWallet)
                ToCryptoWallet   = aliased(CryptoWallet)

                combined_data = []

                ### Calculate Paginated value
                row_stmt      = select(func.count(CryptoSwap.id))
                exec_row_stmt = await session.execute(row_stmt)
                total_rows    = exec_row_stmt.scalar()

                paginated_value = total_rows / limit

                stmt = select(
                    CryptoSwap.id,
                    CryptoSwap.user_id,
                    CryptoSwap.swap_quantity,
                    CryptoSwap.credit_quantity,
                    CryptoSwap.created_at,
                    CryptoSwap.status,
                    CryptoSwap.fee_value,

                    fromCryptoWallet.crypto_name.label('from_crypto'),
                    ToCryptoWallet.crypto_name.label('to_crypto'),
                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoSwap.user_id
                ).join(
                    fromCryptoWallet, fromCryptoWallet.id == CryptoSwap.from_crypto_wallet_id
                ).join(
                    ToCryptoWallet, ToCryptoWallet.id == CryptoSwap.to_crypto_wallet_id
                ).order_by(
                    desc(CryptoSwap.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ## Get all crypto swap transaction
                all_crypto_swap_transaction_obj = await session.execute(stmt)
                all_crypto_swap_transaction     = all_crypto_swap_transaction_obj.fetchall()
                
                if not all_crypto_swap_transaction:
                    return json({'message': 'No transaction found'}, 404)
                
                ## Serialize the data
                for crypto_swap in all_crypto_swap_transaction:
                    combined_data.append({
                        'id': crypto_swap.id,
                        'user_id': crypto_swap.user_id,
                        'from_crypto': crypto_swap.from_crypto,
                        'to_crypto': crypto_swap.to_crypto,
                        'full_name': crypto_swap.full_name,
                        'email': crypto_swap.email,
                        'swap_quantity': crypto_swap.swap_quantity,
                        'credit_quantity': crypto_swap.credit_quantity,
                        'created_at': crypto_swap.created_at,
                        'status': crypto_swap.status,
                        'fee_value': crypto_swap.fee_value,
                    })

                return json({
                    'success': True,
                    'pagination_count': paginated_value,
                    'admin_swap_data': combined_data,
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        
    

    #### Update Crypto Swap Transaction by Admin
    @auth('userauth')
    @put()
    async def update_cryptoSwap(self, request: Request, schema: AdminUpdateCryptoSwap):
        """
        Update the status of a crypto swap transaction by an admin user.<br/>
        This function authenticates the admin user, verifies the validity of the transaction and wallets,
        and updates the transaction status and wallet balances accordingly.<br/><br/>

        This function allows an admin to update the status of a crypto swap transaction.<br/>
        It verifies the admin's identity, checks the validity of the transaction and wallets,<br/>
        and updates the transaction status and wallet balances accordingly.<br/><br/>

        Args:<br/>
            request (Request): The incoming HTTP request object containing user identity information.<br/>
            schema (AdminUpdateCryptoSwap): The schema containing the swap transaction ID and the new status.<br/><br/>

        Returns:<br/>
            JSON: A JSON response indicating the success or failure of the operation.<br/>
                  - On success: {'success': True, 'message': 'Updated Successfully'}<br/>
                  - On failure: {'message': 'Error message'} with appropriate HTTP status code.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id      = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized Access'}, 401)
                ##Admin authentication ends

                ### Get the payload data
                swap_id = schema.swap_id
                status  = schema.status

                ### Get the Crypto Swap Transaction
                crypto_swap_transaction_obj = await session.execute(select(CryptoSwap).where(
                    CryptoSwap.id == swap_id
                ))
                crypto_swap_transaction = crypto_swap_transaction_obj.scalar()

                if not crypto_swap_transaction:
                    return json({'message': 'Invalid Transaction'}, 404)
                
                ## Get the from Wallet
                from_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == crypto_swap_transaction.from_crypto_wallet_id
                ))
                from_crypto_wallet = from_crypto_wallet_obj.scalar()

                if not from_crypto_wallet:
                    return json({'message': 'Invalid From Crypto Wallet'}, 404)
                
                ### Get to crypto Wallet
                to_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == crypto_swap_transaction.to_crypto_wallet_id
                ))
                to_crypto_wallet = to_crypto_wallet_obj.scalar()

                if not to_crypto_wallet:
                    return json({'message': 'Invalid To Crypto Wallet'}, 404)
                
                ### Wallets are Approved or not
                if not from_crypto_wallet.is_approved:
                    return json({'message': 'From Crypto Wallet has not approved yet'}, 400)
                
                if not to_crypto_wallet.is_approved:
                    return json({'message': 'To Crypto Wallet has not approved yet'}, 400)
                

                ### Calculate balance to deduct
                crypto_swap_quantity = crypto_swap_transaction.swap_quantity
                swap_fee             = crypto_swap_transaction.fee_value

                total_deduct_amount  = crypto_swap_quantity + swap_fee

                ### Crypto Wallet Balance validation
                if from_crypto_wallet.balance < total_deduct_amount:
                    return json({'message': 'Insufficient funds In Account'}, 400)
                
                ### Already approved transaction
                if crypto_swap_transaction.is_approved:
                    return json({'message': 'Transaction already approved'}, 400)
                
                if status == 'Approved':
                    crypto_swap_transaction.is_approved = True
                    crypto_swap_transaction.status = 'Approved'

                    ## Deduct crypto from from Waller
                    from_crypto_wallet.balance -= total_deduct_amount

                    ### Add crypto into transfer Crypto Wallet
                    to_crypto_wallet.balance += crypto_swap_transaction.credit_quantity if crypto_swap_transaction.credit_quantity else 0

                    session.add(crypto_swap_transaction)
                    session.add(from_crypto_wallet)
                    session.add(to_crypto_wallet)

                else:
                    crypto_swap_transaction.status = status

                    session.add(crypto_swap_transaction)


                await session.commit()

                await session.refresh(crypto_swap_transaction)
                await session.refresh(from_crypto_wallet)
                await session.refresh(to_crypto_wallet)

                return json({
                    'success': True,
                    'message': 'Updated Successfully'
                }, 200)
        

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        




### Export Crypto Swap Transactions
class AdminExportCryptoSwapTransaction(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "Export Crypto Swap Transactions"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/export/crypto/swap/'
    
    
    ### Export Crypto Swaps
    @auth('userauth')
    @get()
    async def export_cryptoSwap(self, request: Request):
        """
            This function exports crypto swap transaction data for admin users after authentication.<br/><br/>

            Parameters:<br/>
            - request (Request): The HTTP request object received by the API endpoint.<br/><br/>
            
            Returns:<br/>
             - JSON: A JSON response containing the exported crypto swap transaction data.<br/>
             - HTTP Status Code: 200<br/>
             - HTTP Status Code: 500 in case of server errors.<br/>
             - HTTP Status Code: 401 in case of unauthorized access.<br/>
             - HTTP Status Code: 404 in case of no transactions found.<br/>
             - HTTP Status Code: 400 in case of invalid query parameters.<br/>
             - HTTP Status Code: 429 in case of rate limiting.<br/>
             - HTTP Status Code: 403 in case of insufficient permissions.<br/>
             - HTTP Status Code: 414 in case of URL length exceeds the maximum limit.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized Access'}, 401)
                ##Admin authentication ends

                fromCryptoWallet = aliased(CryptoWallet)
                ToCryptoWallet   = aliased(CryptoWallet)

                combined_data = []

                stmt = select(
                    CryptoSwap.id,
                    CryptoSwap.user_id,
                    CryptoSwap.swap_quantity,
                    CryptoSwap.credit_quantity,
                    CryptoSwap.created_at,
                    CryptoSwap.status,
                    CryptoSwap.fee_value,

                    fromCryptoWallet.crypto_name.label('from_crypto'),
                    ToCryptoWallet.crypto_name.label('to_crypto'),
                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoSwap.user_id
                ).join(
                    fromCryptoWallet, fromCryptoWallet.id == CryptoSwap.from_crypto_wallet_id
                ).join(
                    ToCryptoWallet, ToCryptoWallet.id == CryptoSwap.to_crypto_wallet_id
                ).order_by(
                    desc(CryptoSwap.id)
                )

                ## Get all crypto swap transaction
                all_crypto_swap_transaction_obj = await session.execute(stmt)
                all_crypto_swap_transaction     = all_crypto_swap_transaction_obj.fetchall()
                
                if not all_crypto_swap_transaction:
                    return json({'message': 'No transaction found'}, 404)
                
                ## Serialize the data
                for crypto_swap in all_crypto_swap_transaction:
                    combined_data.append({
                        'id': crypto_swap.id,
                        'From Crypto Name': crypto_swap.from_crypto,
                        'To Crypto Name': crypto_swap.to_crypto,
                        'User Name': crypto_swap.full_name,
                        'Email': crypto_swap.email,
                        'Swap Quantity': crypto_swap.swap_quantity,
                        'Credited Quantity': crypto_swap.credit_quantity,
                        'Date Time': crypto_swap.created_at,
                        'Status': crypto_swap.status,
                        'Fee': crypto_swap.fee_value,
                    })

                return json({
                    'success': True,
                    'export_admin_swap_data': combined_data
                }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



### Filter Crypto Swap Transactions
class AdminFilterCryptoSwapController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Filter Crypto Swap'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/filter/crypto/swap/'
    

    @auth('userauth')
    @post()
    async def filter_cryptoSwap(self, request: Request, schema: AdminFilterCryptoSwapSchema, limit: int = 10, offset: int = 0):
        """
        Filter Crypto Swap Transactions<br/><br/>

        This function filters the Crypto Swap transactions based on the provided parameters.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object containing the payload data.<br/>
            - schema (AdminFilterCryptoSwapSchema): The schema object containing the filter parameters.<br/>
            - limit (int): The maximum number of results to return. Default is 10.<br/>
            - offset (int): The offset for pagination. Default is 0.<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON object containing the filtered Crypto Swap transactions.<br/>
            - HTTPException: If the request payload is invalid or if the admin is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs. <br/><br/>
        
        Raises:<br/>
        - HTTPException: If the request payload is invalid or if the admin is not authenticated.<br/>
        - HTTPStatus: 500 Internal Server Error if an error occurs. <br/>
        - HTTPException: If the request payload is invalid or if the admin is not authenticated.<br/>

        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                    Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized Access'}, 401)
                ##Admin authentication ends

                ## Get the payload data
                dateRange   = schema.dateRange
                user_email  = schema.email
                crypto_name = schema.crypto
                status      = schema.status
                startDate   = schema.start_date
                endDate     = schema.end_date

                ### Aliased table
                fromCryptoWallet = aliased(CryptoWallet)
                ToCryptoWallet   = aliased(CryptoWallet)

                combined_data = []
                conditions    = []
                swap_count    = 0

                ### Get the user email
                if user_email:
                    crypto_user_obj = await session.execute(select(Users).where(
                        Users.email.ilike(f"{user_email}%")
                    ))
                    crypto_user = crypto_user_obj.scalar()

                    if not crypto_user:
                        return json({'message': 'Invalid Email'}, 400)
                
                ### Select the table
                stmt = select(
                    CryptoSwap.id,
                    CryptoSwap.user_id,
                    CryptoSwap.swap_quantity,
                    CryptoSwap.credit_quantity,
                    CryptoSwap.created_at,
                    CryptoSwap.status,
                    CryptoSwap.fee_value,

                    fromCryptoWallet.crypto_name.label('from_crypto'),
                    ToCryptoWallet.crypto_name.label('to_crypto'),
                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoSwap.user_id
                ).join(
                    fromCryptoWallet, fromCryptoWallet.id == CryptoSwap.from_crypto_wallet_id
                ).join(
                    ToCryptoWallet, ToCryptoWallet.id == CryptoSwap.to_crypto_wallet_id
                ).order_by(
                    desc(CryptoSwap.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )
                

                ## Mail filter
                if user_email:
                    conditions.append(
                        CryptoSwap.user_id == crypto_user.id
                    )
                
                ### Status wise Filter
                if status:
                    conditions.append(
                        CryptoSwap.status == status
                    )
                
                ### Filter Date Time Wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            CryptoSwap.created_at >= start_date,
                            CryptoSwap.created_at < (end_date + timedelta(days=1))
                        )
                    )
                    
                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(
                            CryptoSwap.created_at <= end_date,
                            CryptoSwap.created_at >= start_date
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
                        CryptoSwap.from_crypto_wallet_id.in_([wallet.id for wallet in crypto_wallet])
                    )

                 ### IF data found
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    all_crypto_swap_transaction_obj = await session.execute(statement)
                    all_crypto_swap_transaction     = all_crypto_swap_transaction_obj.fetchall()

                    ### Count Swap Rows
                    swap_count_stmt = select(func.count()).select_from(CryptoSwap)
                    swap_count_stmt = swap_count_stmt.where(and_(*conditions))
                    swap_count      = (await session.execute(swap_count_stmt)).scalar()

                    if not all_crypto_swap_transaction:
                        return json({'message': 'No data found'}, 404)
                    
                else:
                    return json({'message': 'No data found'}, 404)
                
                ### Count Paginated Value
                total_swap_count = swap_count
                paginated_count      = total_swap_count / limit if limit > 0 else 1


                ## Serialize the data
                for crypto_swap in all_crypto_swap_transaction:
                    combined_data.append({
                        'id': crypto_swap.id,
                        'user_id': crypto_swap.user_id,
                        'from_crypto': crypto_swap.from_crypto,
                        'to_crypto': crypto_swap.to_crypto,
                        'full_name': crypto_swap.full_name,
                        'email': crypto_swap.email,
                        'swap_quantity': crypto_swap.swap_quantity,
                        'credit_quantity': crypto_swap.credit_quantity,
                        'created_at': crypto_swap.created_at,
                        'status': crypto_swap.status,
                        'fee_value': crypto_swap.fee_value,
                    })

                return json({
                    'success': True,
                    'admin_filter_swap_data': combined_data,
                    'paginated_count': paginated_count

                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)

