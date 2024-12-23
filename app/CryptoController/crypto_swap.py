from app.controllers.controllers import get, post, put
from app.generateID import generate_new_swap_transaction_id
from app.CryptoController.calculateFee import CalculateFee
from app.dateFormat import get_date_range
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from Models.Crypto.schema import CreateUserCryptoSwapTransactionSchema, UserFilterCryptoSwapSchema
from Models.crypto import CryptoWallet, CryptoSwap
from Models.fee import FeeStructure
from sqlmodel import select, and_, desc, func
from sqlalchemy.orm import aliased
from database.db import AsyncSession,  async_engine
from datetime import datetime, timedelta






### Crypto Swap Controller
class UserCryptoSwapController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Swap Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/swap/'
    
    
    ## Create new Crypto swap Transaction
    @auth('userauth')
    @post()
    async def create_crypto_swap(self, request: Request, schema: CreateUserCryptoSwapTransactionSchema):
        """
            This API Endpoint will create a new Crypto Swap Transaction with the specified schema.<br/><br/>

            Parameters:<br/><br/>
                - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
                - schema(CreateUserCryptoSwapTransactionSchema): The schema object containing the crypto wallet id, wallet id, swap_amount, and converted_crypto.<br/><br/>
            
            Returns:<br/>
                - JSON: A JSON response containing the success status, message, or error details.<br/><br/>

            Error Messages:<br/>
                - Invalid From Wallet: If the From wallet does not exist.<br/>
                - Invalid To Wallet: If the To wallet does not exist.<br/>
                - Insufficient fund in account: If the From wallet does not have sufficient balance.<br/>
                - Server Error: If an error occurs during the database operations.<br/>
                - Error 400: 'Insufficient fund in account'<br/>
                - Error 404: 'Invalid From Wallet' or 'Invalid To Wallet'<br/><br/>

            Raises:<br/>
                - BadRequest: If the request data is invalid or the file data is not provided.<br/>
                - SQLAlchemyError: If there is an error during database operations.<br/>
                - Exception: If any other unexpected error occurs.<br/>
                - ValueError: If the form data is invalid.<br/>
                - Error 404: 'Requested transaction not found'<br/>
                - Error 500: 'Server Error'<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                fromWalletID    = schema.from_wallet_id
                toWalletID      = schema.to_wallet_id
                swapAmount      = schema.swap_amount
                convertedCrypto = schema.converted_crypto
                
                ### Get The from Crypto Wallet
                from_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == fromWalletID
                ))
                from_crypto_wallet = from_crypto_wallet_obj.scalar()

                if not from_crypto_wallet:
                    return json({'message': 'Invalid From Wallet'}, 404)
                
                ### Get To Crypto Wallet
                to_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == toWalletID
                ))
                to_crypto_wallet = to_crypto_wallet_obj.scalar()

                if not to_crypto_wallet:
                    return json({'message': 'Invalid To Wallet'}, 404)
                
                ## Balance check
                if float(swapAmount) > from_crypto_wallet.balance:
                    return json({'message': 'Insufficient fund in account'}, 400)
                
                # Get fee to Swap Crypto
                crypto_swap_fee_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == 'Crypto Swap'
                ))
                crypto_swap_fee = crypto_swap_fee_obj.scalar()

                ## Generate new transaction ID
                swap_transaction_id = await generate_new_swap_transaction_id()

                if crypto_swap_fee:
                    float_qty = float(swapAmount)
                    calculated_amount = await CalculateFee(crypto_swap_fee.id, float_qty)

                    ### Create Crypto Swap Transaction
                    create_crypto_swap = CryptoSwap(
                        user_id               = user_id,
                        from_crypto_wallet_id = from_crypto_wallet.id,
                        to_crypto_wallet_id   = to_crypto_wallet.id,
                        swap_quantity         = float(swapAmount),
                        credit_quantity       = float(convertedCrypto),
                        status                = 'Pending',
                        fee_value             = float(calculated_amount),
                        transaction_id        = swap_transaction_id
                    )

                    session.add(create_crypto_swap)

                else:
                    calculated_amount = 10

                    ### Create Crypto Swap Transaction
                    create_crypto_swap = CryptoSwap(
                        user_id               = user_id,
                        from_crypto_wallet_id = from_crypto_wallet.id,
                        to_crypto_wallet_id   = to_crypto_wallet.id,
                        swap_quantity         = float(swapAmount),
                        credit_quantity       = float(convertedCrypto),
                        status                = 'Pending',
                        fee_value             = float(calculated_amount),
                        transaction_id        = swap_transaction_id
                    )

                    session.add(create_crypto_swap)

                await session.commit()
                await session.refresh(create_crypto_swap)

                return json({
                    'success': True,
                    'message': "Created Successfully"
                }, 201)
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
                }, 500)
        
    

    ### Get all the swap transaction
    @auth('userauth')
    @get()
    async def get_cryptoSwap(self, request: Request, limit: int = 10, offset: int = 0):
        """
            This API Endpoint will get all the Crypto Swap Transactions for the specified user.<br/><br/>

            Parameters:<br/>
                - request(Request): The HTTP request object containing the user's identity.<br/>
                - limit(int): The number of rows to be returned. Default is 10.<br/>
                - offset(int): The offset of the rows to be returned. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the user_crypto_swap_transactions, success, message, and the paginated_rows.<br/><br/>
            
            Error Messages:<br/>
                - Server Error: If an error occurs during the database operations.<br/>
                - Error 500: 'Server Error'<br/><br/>

            Raises:<br/>
                - Exception: If any other unexpected error occurs.<br/>
                - ValueError: If the form data is invalid.<br/>
                - Error 404: 'Requested transaction not found'<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                fromCryptoWallet = aliased(CryptoWallet)
                ToCryptoWallet   = aliased(CryptoWallet)

                ### Get all availabel rows
                select_rows = select(func.count(CryptoSwap.id)).where(CryptoSwap.user_id == user_id)
                exec_row    = await session.execute(select_rows)
                total_rows  = exec_row.scalar()

                paginated_rows = total_rows / limit

                ### Select all the Column
                stmt = select(
                    CryptoSwap.id,
                    CryptoSwap.user_id,
                    CryptoSwap.swap_quantity,
                    CryptoSwap.credit_quantity,
                    CryptoSwap.created_at,
                    CryptoSwap.status,
                    CryptoSwap.fee_value,
                    CryptoSwap.transaction_id,

                    fromCryptoWallet.crypto_name.label('from_crypto_name'),
                    ToCryptoWallet.crypto_name.label('to_crypto_name'),

                ).join(
                    fromCryptoWallet, fromCryptoWallet.id == CryptoSwap.from_crypto_wallet_id
                ).join(
                    ToCryptoWallet, ToCryptoWallet.id == CryptoSwap.to_crypto_wallet_id
                ).where(
                    CryptoSwap.user_id == user_id
                ).order_by(
                    desc(CryptoSwap.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ### Execute Query
                all_crypto_swap_transaction_obj = await session.execute(stmt)
                all_crypto_swap_transaction     = all_crypto_swap_transaction_obj.fetchall()

                for transaction in all_crypto_swap_transaction:
                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'transaction_id': transaction.transaction_id,
                        'swap_quantity': transaction.swap_quantity,
                        'credit_quantity': transaction.credit_quantity,
                        'created_at': transaction.created_at,
                        'status': transaction.status,
                        'fee': transaction.fee_value,
                        'from_crypto_name': transaction.from_crypto_name,
                        'to_crypto_name': transaction.to_crypto_name
                    })

                return json({
                    'success': True,
                    'user_crypto_swap_transactions': combined_data,
                    'paginated_rows': paginated_rows
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        



#### Filter Crypto Swap for user
class UserCryptoSwapFilterController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Swap Filter Controller'

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/filter/crypto/swap/'
    
    @auth('userauth')
    @post()
    async def filter_userCryptoSwap(self, request: Request, schema: UserFilterCryptoSwapSchema, limit: int = 10, offset: int = 0):
        """
           This API Endpoint is responsible for filtering users CryptoSwap transactions.<br/><br/>

           Parameters:<br/>
            - request (Request): The HTTP request object containing the payload data.<br/>
            - schema (UserFilterCryptoSwapSchema): The schema object containing the validated data.<br/>
            - limit (int, optional): The maximum number of records to return. Defaults to 10.<br/>
            - offset (int, optional): The number of records to skip before starting to return records. Defaults to 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the following keys and values:<br/>
                -'success': True if the operation was successful.<br/>
                - 'user_filter_crypto_swap_transactions': A list of dictionaries containing transaction details.<br/>
                - 'paginated_count': The total number of pages based on the limit.<br/><br/>

            Raises:
                - HTTPException: If the user is not authorized to access the admin functionality.<br/>
                - HTTPException: If the payload data is not valid or if the date_time field is not in the correct format.<br/><br/>

            Error Messages:<br/>
                - 'Invalid payload data': If the payload data is not valid.<br/>
                - 'Invalid date range': If the start_date and end_date fields are not in the correct format.<br/>
                - 'Invalid status': If the status field is not in the valid status list.<br/>
                - 'Server Error': If any other error occurs.<br/>
                - 'No data found': If no transaction is found based on the provided filters.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                dateRange       = schema.dateRange
                status          = schema.status
                fromCrypto      = schema.from_crypto
                toCrypto        = schema.to_crypto
                startDate       = schema.start_date
                endDate         = schema.end_date

                combined_data = []
                conditions    = []

                ### Aliased Table
                fromCryptoWallet = aliased(CryptoWallet)
                ToCryptoWallet   = aliased(CryptoWallet)


                ### Select all the Column
                stmt = select(
                    CryptoSwap.id,
                    CryptoSwap.user_id,
                    CryptoSwap.swap_quantity,
                    CryptoSwap.credit_quantity,
                    CryptoSwap.created_at,
                    CryptoSwap.status,
                    CryptoSwap.fee_value,
                    CryptoSwap.transaction_id,

                    fromCryptoWallet.crypto_name.label('from_crypto_name'),
                    ToCryptoWallet.crypto_name.label('to_crypto_name'),

                ).join(
                    fromCryptoWallet, fromCryptoWallet.id == CryptoSwap.from_crypto_wallet_id
                ).join(
                    ToCryptoWallet, ToCryptoWallet.id == CryptoSwap.to_crypto_wallet_id
                ).where(
                    CryptoSwap.user_id == user_id
                ).order_by(
                    desc(CryptoSwap.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ### Filter Custom Date range wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            CryptoSwap.created_at >= start_date,
                            CryptoSwap.created_at < (end_date + timedelta(days=1))
                        )
                    )
                
                ### Filter Date Range wise
                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(
                            CryptoSwap.created_at <= end_date,
                            CryptoSwap.created_at >= start_date
                        )
                    )
                
                ### Status wise Filter
                if status:
                    conditions.append(
                        CryptoSwap.status == status
                    )
                
                ### Flter From Crypto Name wise
                if fromCrypto:
                    crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                        CryptoWallet.crypto_name == fromCrypto
                    ))
                    crypto_wallet = crypto_wallet_obj.scalars().all()

                    if not crypto_wallet:
                        return json({'message': 'No data found'}, 404)
                    
                    conditions.append(
                        CryptoSwap.from_crypto_wallet_id.in_([wallet.id for wallet in crypto_wallet])
                    )

                ### Filter To Crypto Wise
                if toCrypto:
                    crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                        CryptoWallet.crypto_name == toCrypto
                    ))
                    crypto_wallet = crypto_wallet_obj.scalars().all()

                    if not crypto_wallet:
                        return json({'message': 'No data found'}, 404)
                    
                    conditions.append(
                        CryptoSwap.to_crypto_wallet_id.in_([wallet.id for wallet in crypto_wallet])
                    )

                ### Count total paginated value
                swap_count_stmt =  select(func.count()).select_from(CryptoSwap).where(
                        CryptoSwap.user_id == user_id, *conditions
                    )
                swap_count = (await session.execute(swap_count_stmt)).scalar()

                paginated_value = swap_count / limit

                 ### IF data found
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    all_crypto_swap_transaction_obj = await session.execute(statement)
                    all_crypto_swap_transaction     = all_crypto_swap_transaction_obj.fetchall()

                    if not all_crypto_swap_transaction:
                        return json({'message': 'No data found'}, 404)
                    
                else:
                    return json({'message': 'No data found'}, 404)
                
                for transaction in all_crypto_swap_transaction:
                    combined_data.append({
                        'id': transaction.id,
                        'user_id': transaction.user_id,
                        'transaction_id': transaction.transaction_id,
                        'swap_quantity': transaction.swap_quantity,
                        'credit_quantity': transaction.credit_quantity,
                        'created_at': transaction.created_at,
                        'status': transaction.status,
                        'fee': transaction.fee_value,
                        'from_crypto_name': transaction.from_crypto_name,
                        'to_crypto_name': transaction.to_crypto_name
                    })

                return json({
                    'success': True,
                    'user_filter_crypto_swap_transactions': combined_data,
                    'paginated_count': paginated_value
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)