from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from sqlmodel import select, desc, func, and_
from database.db import AsyncSession, async_engine
from Models.crypto import CryptoExchange, CryptoWallet
from Models.models import Wallet
from Models.fee import FeeStructure
from Models.Crypto.schema import UserCreateCryptoExchangeSchema, UserFilterCryptoExchangeSchema
from app.generateID import generate_new_crypto_exchange_transaction_id
from app.CryptoController.calculateFee import CalculateFee
from app.dateFormat import get_date_range
from datetime import datetime, timedelta



### User Crypto Exchange controller
class UserCryptoExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Exchange Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/user/crypto/exchange/'
    
    
    ### Create new Crypto Exchange Transaction for user
    @auth('userauth')
    @post()
    async def create_cryptoExchange(self, request: Request, schema: UserCreateCryptoExchangeSchema):
        """
            This API Endpoint will create a new Crypto Exchange Transaction with the specified schema.<br/><br/>

            Parameters:<br/>
             - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
             - schema(UserCreateCryptoExchangeSchema): The schema object containing the crypto wallet id, wallet id, exchange_amount, and converted_amount.<br/><br/>

             Returns:<br/>
             - JSON: A JSON response containing the success status, msg, or error details.<br/>
             - HTTP Status Code: 200 if successful, 400 if invalid request data, or 500 if an error occurs.<br/><br/>

             Error Messages:<br/>
             - Invalid request data: If the request data does not match the UserCreateCryptoExchangeSchema.<br/>
             - Server Error: If an error occurs during the database operations.<br/>
             - Invalid Crypto Wallet: If the crypto wallet id provided does not match any wallet in the system.<br/>
             - Invalid FIAT Wallet: If the fiat wallet id provided does not match any wallet in the system.<br/>
             - Insufficient balance in Account: If the user does not have enough balance in the crypto wallet.<br/><br/>

             Raises:<br/>
              - BadRequest: If the request data is invalid or the file data is not provided.<br/>
              - SQLAlchemyError: If there is an error during database operations.<br/>
              - Exception: If any other unexpected error occurs.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get the payload data
                cryptoWalletID  = schema.crypto_wallet_id
                fiatWalletID    = schema.fiat_wallet_id
                exchangeAmount  = schema.exchange_amount
                convertedAmount = schema.converted_amount

                ## Get the user Crypto Wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                   and_(
                       CryptoWallet.id == cryptoWalletID,
                       CryptoWallet.user_id == user_id
                       )
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 404)
                
                ## Get the fiat Wallet
                user_fiat_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.id      == fiatWalletID,
                        Wallet.user_id == user_id
                    )
                ))
                user_fiat_wallet = user_fiat_wallet_obj.scalar()

                if not user_fiat_wallet:
                    return json({'message': 'Invalid FIAT Wallet'}, 404)
                
                ## Crypto Wallet balance validation
                if user_crypto_wallet.balance < float(exchangeAmount if exchangeAmount else 0):
                    return json({'message': 'Insufficient balance in Account'}, 400)
                
                # Get fee for Exchange Crypto
                crypto_exchange_fee_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == 'Crypto Exchange'
                ))
                crypto_exchange_fee = crypto_exchange_fee_obj.scalar()

                exchange_transaction_id = await generate_new_crypto_exchange_transaction_id()

                if crypto_exchange_fee:
                    float_qty      = float(exchangeAmount)
                    calculated_fee = await CalculateFee(crypto_exchange_fee.id, float_qty)

                    create_crypto_exchange_transaction = CryptoExchange(
                            user_id                = user_id,
                            transaction_id         = exchange_transaction_id,
                            crypto_wallet          = user_crypto_wallet.id,
                            fiat_wallet            = user_fiat_wallet.id,
                            exchange_crypto_amount = float(exchangeAmount),
                            converted_fiat_amount  = float(convertedAmount),
                            status                 = 'Pending',
                            fee_value              = float(calculated_fee)
                    )

                    session.add(create_crypto_exchange_transaction)

                else:
                    calculated_fee = 10

                    create_crypto_exchange_transaction = CryptoExchange(
                            user_id                = user_id,
                            transaction_id         = exchange_transaction_id,
                            crypto_wallet          = user_crypto_wallet.id,
                            fiat_wallet            = user_fiat_wallet.id,
                            exchange_crypto_amount = float(exchangeAmount),
                            converted_fiat_amount  = float(convertedAmount),
                            status                 = 'Pending',
                            fee_value              = float(calculated_fee)
                    )

                    session.add(create_crypto_exchange_transaction)

                await session.commit()
                await session.refresh(create_crypto_exchange_transaction)

                return json({
                    'success': True,
                    'message': 'Transaction Created Successfully'
                    }, 200)
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        
    
    ### Get all Crypto Exchange of the user
    @auth('userauth')
    @get()
    async def get_cryptoExchange(self, request: Request, limit: int = 10, offset: int = 0):
        """
            This API Endpoint will retrieve all the Crypto Exchange Transactions of the specified user.<br/><br/>
            
            Parameters:<br/>
                - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
                - limit(int, optional): The number of transactions to retrieve per page. Default is 10.<br/>
                - offset(int, optional): The number of transactions to skip before starting to retrieve. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, msg, and data.<br/>
                - HTTP Status Code: 200 if successful, 401 if the user is not authenticated, or 500 if an error occurs.<br/><br/>

            Error Messages:<br/>
                - Unauthorized: If the user is not authenticated.<br/>
                - Server Error: If an error occurs during the database operations.<br/><br/>
            
            Raises:<br/><br/>
                - BadRequest: If the request data is invalid or the file data is not provided.<br/>
                - SQLAlchemyError: If there is an error during database operations.<br/>
                - Exception: If any other unexpected error occurs.<br/><br/>
          """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                combined_data = []

                ### Count all availble rows for paginated data
                select_rows  = select(func.count(CryptoExchange.id)).where(CryptoExchange.user_id == user_id)
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
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, and_(Wallet.id == CryptoExchange.fiat_wallet)
                ).where(
                    CryptoExchange.user_id == user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                all_crypto_exchange_transaction_obj = await session.execute(stmt)
                all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

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
                        'fiat_currency': transaction.currency
                    })


                return json({
                    'success': True,
                    'user_crypto_exchange_data': combined_data,
                    'paginated_rows': paginated_rows
                }, 200)


        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



### Filter Crypto Exchange Transaction
class UserFilterCryptoExchangeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User filter crypto exchange transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v6/user/filter/crypto/exchange/'
    

    ### Filter Crypto Exchange Transaction
    @auth('userauth')
    @post()
    async def filter_userCryptoExchange(self, request: Request, schema: UserFilterCryptoExchangeSchema, limit: int = 10, offset: int = 0):
        """
            This API Endpoint filter user's Crypto Exchange Transaction.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing user identity and other information.<br/>
                - schema (UserFilterCryptoExchangeSchema): The schema containing the filter criteria.<br/>
                - limit (int, optional): The number of transactions to retrieve per page. Default is 10.<br/>
                - offset (int, optional): The number of transactions to retrieve per page. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, data and availale rows in db.<br/>
                - HTTP Status Code: 200 if successful, 401 if the user is not authenticated, or 500 if an error occurs.<br/><br/>

            Error Messages:<br/>
                - Unauthorized: If the user is not authenticated.<br/>
                - Server Error: If an error occurs during the database operations.<br/>
                - Error response status code 404: 'message': 'No data found'.<br/>
                - Error response status code 404: 'message': 'Invalid FIAT Wallet'.<br/><br/>

            Raises:<br/>
                - BadRequest: If the request data is invalid or the file data is not provided.<br/>
                - SQLAlchemyError: If there is an error during database operations.<br/>
                - Exception: If any other unexpected error occurs.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ### Get payload Data
                dateRange  = schema.dateRange
                cryptoName = schema.crypto_name
                fiat       = schema.fiat
                status     = schema.status
                startDate  = schema.start_date
                endDate    = schema.end_date

                conditions = []
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
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoExchange.crypto_wallet
                ).join(
                    Wallet, Wallet.id == CryptoExchange.fiat_wallet
                ).where(
                    CryptoExchange.user_id == user_id
                ).order_by(
                    desc(CryptoExchange.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                ### Status wise Filter
                if status:
                    conditions.append(
                        CryptoExchange.status == status
                    )

                ### Filter Date Time Wise
                if dateRange and dateRange == 'CustomRange':
                    start_date = datetime.strptime(startDate, "%Y-%m-%d")
                    end_date   = datetime.strptime(endDate, "%Y-%m-%d")

                    conditions.append(
                        and_(
                            CryptoExchange.created_at >= start_date,
                            CryptoExchange.created_at < (end_date + timedelta(days=1))
                        )
                    )
                    
                elif dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(
                            CryptoExchange.created_at <= end_date,
                            CryptoExchange.created_at >= start_date
                        )
                    )
                
                ### Flter Crypto Name wise
                if cryptoName:
                    crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                        CryptoWallet.crypto_name == cryptoName
                    ))
                    crypto_wallet = crypto_wallet_obj.scalars().all()

                    if not crypto_wallet:
                        return json({'message': 'No data found'}, 404)
                    
                    conditions.append(
                        CryptoExchange.crypto_wallet.in_([wallet.id for wallet in crypto_wallet])
                    )

                ### Filter FIAT Wallet Wise
                if fiat:
                    user_wallet_obj = await session.execute(select(Wallet).where(
                        and_(
                            Wallet.currency == fiat,
                            Wallet.user_id == user_id
                            )
                    ))
                    user_wallet = user_wallet_obj.scalar()

                    if not user_wallet:
                        return json({'message': 'Invalid FIAT Wallet'}, 404)
                    
                    conditions.append(
                        CryptoExchange.fiat_wallet == user_wallet.id
                    )

                # Count Exchange Transactions
                swap_count_stmt = select(func.count()).select_from(CryptoExchange).where(
                    CryptoExchange.user_id == user_id, *conditions
                )
                swap_count = (await session.execute(swap_count_stmt)).scalar()

                paginated_value = swap_count / limit

                ### IF data found
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    all_crypto_exchange_transaction_obj = await session.execute(statement)
                    all_crypto_exchange_transaction     = all_crypto_exchange_transaction_obj.fetchall()

                    if not all_crypto_exchange_transaction:
                        return json({'message': 'No data found'}, 404)
                    
                else:
                    return json({'message': 'No data found'}, 404)
                

                ### Get all data in a list
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
                        'fiat_currency': transaction.currency
                    })
                
                return json({
                    'success': True,
                    'user_filtered_crypto_exchange': combined_data,
                    'paginated_count': paginated_value
                })
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)