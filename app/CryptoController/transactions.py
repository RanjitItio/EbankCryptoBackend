from app.controllers.controllers import post, get
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.crypto import CryptoWallet, CryptoBuy, CryptoSell
from Models.models import Wallet, Currency
from Models.fee import FeeStructure
from Models.Crypto.schema import BuyUserCryptoSchema, SellUserCryptoSchema, UserFilterCryptoTransactionSchema
from app.CryptoController.calculateFee import CalculateFee
from datetime import datetime, timedelta
from app.dateFormat import get_date_range
import uuid







## Buy Crypto Wallet
class CryptoBuyController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/buy/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Buy Crypto'
    

    @auth('userauth')
    @post()
    async def create_cryptoBuy(self, request: Request, schema: BuyUserCryptoSchema):
        """
            This function creates a new crypto buy transaction for a user, handling validations and fee
            calculations.<br/><br/>

            Parameters:<br/>
            request: The `request` parameter in the `create_cryptoBuy` function represents the HTTP
            request object that contains information about the incoming request such as headers, body,
            method, etc. It allows users to access and process data sent by the client making the request. <br/>
            schema: The `schema` parameter in the `create_cryptoBuy` function represents the data schema for creating a new crypto buy transaction. <br/>
            It contains the following fields: type schema: BuyUserCryptoSchema <br/><br/>
            
            Return:<br/>
            The code is returning a JSON response with a success message if the operation is
            successful, along with an HTTP status code of 200. If there is an error during the process, it
            will return a JSON response with an error message and an HTTP status code of 500.
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ## Get payload data
                cryptoWalletId          = schema.crypto_wallet_id
                paymentType             = schema.payment_type
                walletId                = schema.wallet_id
                buyingAmount            = schema.buy_amount
                cryptoConvertedQuantity = schema.converted_crypto_quantity

                ## Get the crypto wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    and_(
                        CryptoWallet.id      == cryptoWalletId,
                        CryptoWallet.user_id == user_id
                    )
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 400)
                
                # Get the user Wallet
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.id      == walletId,
                        Wallet.user_id == user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'Invalid Wallet'}, 400)
                
                # Wallet balance validation
                if user_wallet.balance < int(buyingAmount):
                    return json({'message': 'Insufficient fund'}, 400)
                
                if not user_crypto_wallet.is_approved:
                    return json({'message': 'Crypto wallet has not approved'}, 400)
                
                ## Get Buying Currency
                buying_currency_obj = await session.execute(select(Currency).where(
                    Currency.id == user_wallet.currency_id
                ))
                buying_currency = buying_currency_obj.scalar()

                # Get fee to Buy Crypto
                buy_crypto_fee_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == 'Crypto Buy'
                ))
                buy_crypto_fee = buy_crypto_fee_obj.scalar()

                if buy_crypto_fee:
                    float_amt = float(buyingAmount)

                    calculated_amount = await CalculateFee(buy_crypto_fee.id, float_amt)

                    crypto_buy = CryptoBuy(
                        user_id          = user_id,
                        crypto_wallet_id = user_crypto_wallet.id,
                        crypto_quantity  = cryptoConvertedQuantity,
                        payment_type     = paymentType,
                        wallet_id        = user_wallet.id,
                        buying_currency  = buying_currency.name,
                        buying_amount    = float(buyingAmount),
                        fee_id           = buy_crypto_fee.id,
                        fee_value        = calculated_amount,
                        status           = 'Pending'        
                    )

                    session.add(crypto_buy)

                else:
                    calculated_amount = 10

                    # Create Crypto Buy request
                    crypto_buy = CryptoBuy(
                        user_id          = user_id,
                        crypto_wallet_id = user_crypto_wallet.id,
                        crypto_quantity  = cryptoConvertedQuantity,
                        payment_type     = paymentType,
                        wallet_id        = user_wallet.id,
                        buying_currency  = buying_currency.name,
                        buying_amount    = float(buyingAmount),
                        fee_value        = calculated_amount,
                        status           = 'Pending'   
                    )
                    session.add(crypto_buy)

                await session.commit()
                await session.refresh(crypto_buy)

                return json({
                    'success': True,
                    'message': "Updated Successfully"
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


## Sell Crypto Controller
class CryptoSellController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/sell/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Sell Crypto'
    
    
    #### Create new Crypto Sell Transaction
    @auth('userauth')
    @post()
    async def create_cryptoSell(self, request: Request, schema: SellUserCryptoSchema):
        """
            This API Endpoint will create a new Crypto Sell Transaction with the specified schema.

            Parameters:<br/><br/>
                - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
                - schema(SellUserCryptoSchema): The schema object containing the crypto wallet id, wallet id, selling quantity, and converted amount.<br/><br/>

            Returns:<br/>
                - JSON: A JSON response containing the success status, msg, or error details.<br/>
                - HTTP Status Code: 200 if successful, 400 if invalid request data, or 500 if an error occurs.<br/><br/>
            
            Error Messages:<br/>
                - Invalid request data: If the request data does not match the SellUserCryptoSchema.<br/>
                - Server Error: If an error occurs during the database operations.<br/>
                - Insufficient fund: If the user does not have enough balance in the crypto wallet.<br/>
                - Crypto wallet has not approved: If the crypto wallet has not been approved by the admin.<br/>
                - Invalid wallet: If the wallet id provided does not match any wallet in the system.<br/>
                - Error 400: 'Invalid request data'<br/>
                - Error 500: 'Server Error'<br/><br/>

            Raises:<br/>
                - BadRequest: If the request data is invalid or the file data is not provided.<br/>
                - SQLAlchemyError: If there is an error during database operations.<br/>
                - Exception: If any other unexpected error occurs.<br/>
                - ValueError: If the form data is invalid.<br/><br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ## Get payload data
                cryptoWalletId = schema.crypto_wallet_id
                walletId       = schema.wallet_id
                sellingQty     = schema.selling_qty
                received_amt   = schema.converted_amount

                ## Get the crypto wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    and_(
                        CryptoWallet.id      == cryptoWalletId,
                        CryptoWallet.user_id == user_id
                    )
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Invalid Crypto Wallet'}, 400)
                
                # Wallet balance validation
                if user_crypto_wallet.balance < float(sellingQty):
                    return json({'message': 'Insufficient fund'}, 400)
                
                ## Approved validation
                if not user_crypto_wallet.is_approved:
                    return json({'message': 'Crypto wallet has not approved'}, 400)

                # Get the user Wallet
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.id      == walletId,
                        Wallet.user_id == user_id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'Invalid Wallet'}, 400)

                # Get fee to Buy Crypto
                crypto_sell_fee_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == 'Crypto Sell'
                ))
                crypto_sell_fee = crypto_sell_fee_obj.scalar()

                unique_id = str(uuid.uuid4())[:33]

                if crypto_sell_fee:
                    float_qty = float(sellingQty)

                    calculated_amount = await CalculateFee(crypto_sell_fee.id, float_qty)

                    unique_id = str(uuid.uuid4())[:30]

                    crypto_sell = CryptoSell(
                        user_id          = user_id,
                        crypto_wallet_id = user_crypto_wallet.id,
                        crypto_quantity  = float(sellingQty),
                        wallet_id        = user_wallet.id,
                        received_amount  = float(received_amt),
                        fee_id           = crypto_sell_fee.id,
                        fee_value        = float(calculated_amount),
                        status           = 'Pending',
                        transaction_id   = unique_id
                    )

                    session.add(crypto_sell)

                else:
                    calculated_amount = 10

                    # Create Crypto Buy request
                    crypto_sell = CryptoSell(
                        user_id          = user_id,
                        crypto_wallet_id = user_crypto_wallet.id,
                        crypto_quantity  = float(sellingQty),
                        wallet_id        = user_wallet.id,
                        received_amount  = float(received_amt),
                        fee_value        = calculated_amount,
                        status           = 'Pending',
                        transaction_id   = unique_id 
                    )
                    session.add(crypto_sell)

                await session.commit()
                await session.refresh(crypto_sell)

                return json({
                    'success': True,
                    'message': "Updated Successfully"
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

        



### User Crypto Transactions
class CryptoTransactionControlller(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/transactions/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Transactions'
    
    
    ### Get all Buy and Sell Crypto Transactions
    @auth('userauth')
    @get()
    async def get_cryptoTransactions(self, request: Request, limit: int = 4, offset: int = 0):
        """
            This API Endpoint will return all crypto transactions in descending order.
            The transactions are ordered by transaction_id in descending order.<br/><br/>

            Parameters:<br/>
                - request(Request): The HTTP request object containing identity and other relevant information.<br/>
                - limit(int, optional): The maximum number of transactions to return per page. Default is 4.<br/>
                - offset(int, optional): The number of transactions to skip before starting to retrieve logs. Default is 0.<br/><br/>

            Returns:<br/>
                - JSON response containing the following keys:<br/> 
                - success(bool): A boolean indicating whether the operation was successful.<br/>
                - crypto_transactions(list): A list of dictionaries, each representing a transaction.<br/>
                - total_row_count(int): The total number of transactions available for the user.<br/><br/>

            Raises:<br/>
                - Exception: If any error occurs during the database query or response generation.<br/>
                - Error 401: 'error': 'Unauthorized'.<br/>
                - Error 404: 'error': 'No transaction available'.<br/>
                - Error 500: 'error': 'Server Error'.<br/><br/>

            Error Messages:<br/>
                - Error 404: 'error': 'No transaction available'.<br/>
                - Error 500: 'error': 'Server Error'.<br/><br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

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
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                ).where(
                    CryptoBuy.user_id == user_id
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
                ).join(
                    CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                ).join(
                    Wallet, Wallet.id == CryptoSell.wallet_id
                ).where(
                    CryptoSell.user_id == user_id
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

                ## Get all th cryptoBuy Transactions of user
                crypto_buy_transaction_obj = await session.execute(buy_stmt)
                crypto_buy_transaction     = crypto_buy_transaction_obj.all()

                ## Get all th cryptoSell Transactions of user
                crypto_sell_transaction_obj = await session.execute(sell_stmt)
                crypto_sell_transaction = crypto_sell_transaction_obj.all()

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
                        'created_at': buyTransaction.created_at

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
                        'created_at': sellTransaction.created_at

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
        


#### Filter Crypto Transactions
class UserCryptoTransactionFilterController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Crypto Transaction Filter Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/filter/crypto/transactions/'
    
    
    ### Filter all crypto transaction
    @auth('userauth')
    @post()
    async def filter_userCryptoTransaction(self, request: Request, schema: UserFilterCryptoTransactionSchema, limit: int = 5, offset: int = 0):
        """
            This API Endpoint filter all crypto transactions according to the specified schema(dateRange, transactionType, status, crypto, start_date, end_date) and returns paginated results.<br/><br/>

            Parameters:<br/>
                - limit: Number of transactions to return per page (default: 5).<br/>
                - offset: Number of transactions to skip before returning results (default: 0).<br/>
                - schema: UserFilterCryptoTransactionSchema: Schema to filter crypto transactions (default: None).<br/><br/>

            Returns:<br/>
                - JSON: A JSON object containing the filtered crypto transactions.<br/>
                - HTTPException: If the request payload is invalid or if the user is not authenticated.<br/>
                - HTTPStatus: 500 Internal Server Error if an error occurs.<br/><br/>
            
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

                buy_conditions  = []
                sell_conditions = []

                ### Get the payload data
                dateRange       = schema.dateRange
                transactionType = schema.transactionType
                status          = schema.status
                cryptoName      = schema.crypto
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
                
                ### Date range filter
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

                
                ### Filter status wise
                if status:
                    buy_conditions.append(
                        CryptoBuy.status.ilike(f"{status}%")
                    )

                    sell_conditions.append(
                        CryptoSell.status.ilike(f"{status}%")
                    )

                ## Execute Buy Query
                # buy_stmt = select(
                #     CryptoBuy.id,
                #     CryptoBuy.crypto_quantity,
                #     CryptoBuy.payment_type,
                #     CryptoBuy.buying_currency,
                #     CryptoBuy.buying_amount,
                #     CryptoBuy.fee_value,
                #     CryptoBuy.created_at,
                #     CryptoBuy.status,

                #     CryptoWallet.crypto_name,
                # ).join(
                #     CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                # ).where(
                #     CryptoBuy.user_id == user_id
                # ).order_by(
                #     desc(CryptoBuy.id)
                # ).limit(
                #     limit
                # ).offset(
                #     offset
                # )


                # ## Execute Sell Query
                # sell_stmt = select(
                #     CryptoSell.id,
                #     CryptoSell.crypto_quantity,
                #     CryptoSell.payment_type,
                #     CryptoSell.received_amount,
                #     CryptoSell.fee_value,
                #     CryptoSell.created_at,
                #     CryptoSell.status,

                #     CryptoWallet.crypto_name,
                #     Wallet.currency.label('wallet_currency')
                # ).join(
                #     CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                # ).join(
                #     Wallet, Wallet.id == CryptoSell.wallet_id
                # ).where(
                #     CryptoSell.user_id == user_id
                # ).order_by(
                #     desc(CryptoSell.id)
                # ).limit(
                #     limit
                # ).offset(
                #     offset
                # )

                # user_buy_transaction  = []
                # user_sell_transaction = []
                # buy_count  = 0
                # sell_count = 0

                ### Buy Transaction
                # if buy_conditions:
                #     # Count Buy Transactions
                #     buy_count_stmt = select(func.count()).select_from(CryptoBuy).where(
                #         CryptoBuy.user_id == user_id, *buy_conditions
                #     )
                #     buy_count = (await session.execute(buy_count_stmt)).scalar()

                #     pagination_limit = 10

                #     buy_statement = buy_stmt.where(and_(*buy_conditions))

                #     user_buy_transaction_obj = await session.execute(buy_statement)
                #     user_buy_transaction     = user_buy_transaction_obj.fetchall()

                # ### Sell Transaction
                # if sell_conditions:
                #      # Count Sell Transactions
                #     sell_count_stmt = select(func.count()).select_from(CryptoSell).where(
                #         CryptoSell.user_id == user_id, *sell_conditions
                #     )
                #     sell_count = (await session.execute(sell_count_stmt)).scalar()

                #     pagination_limit = 10

                #     sell_statement = sell_stmt.where(and_(*sell_conditions))

                #     user_sell_transactio_obj = await session.execute(sell_statement)
                #     user_sell_transaction    = user_sell_transactio_obj.fetchall()

                ### Transaction Type Filter
                # if transactionType == 'Buy':
                #     # Count Buy Transactions
                #     buy_count_stmt = select(func.count(CryptoBuy.id)).where(CryptoBuy.user_id == user_id)
                #     buy_count = (await session.execute(buy_count_stmt)).scalar()

                #     pagination_limit = 5

                #     user_buy_transaction_obj = await session.execute(buy_stmt)
                #     user_buy_transaction     = user_buy_transaction_obj.fetchall()

                # elif transactionType == 'Sell':
                #     sell_count_stmt = select(func.count(CryptoSell.id)).where(CryptoSell.user_id == user_id)
                #     sell_count      = (await session.execute(sell_count_stmt)).scalar()

                #     pagination_limit = 5

                #     user_sell_transactio_obj = await session.execute(sell_stmt)
                #     user_sell_transaction    = user_sell_transactio_obj.fetchall()


                if transactionType == 'Buy' or not transactionType:
                    buy_stmt = select(
                        CryptoBuy.id,
                        CryptoBuy.crypto_quantity, 
                        CryptoBuy.payment_type,
                        CryptoBuy.buying_currency, 
                        CryptoBuy.buying_amount, 
                        CryptoBuy.fee_value,
                        CryptoBuy.created_at, 
                        CryptoBuy.status,
                        CryptoWallet.crypto_name
                    ).join(
                        CryptoWallet, CryptoWallet.id == CryptoBuy.crypto_wallet_id
                    )

                    if buy_conditions:
                        buy_stmt = buy_stmt.where(and_(*buy_conditions))

                    # Apply ordering, limit, and offset
                    buy_stmt = buy_stmt.order_by(desc(CryptoBuy.id)).limit(limit).offset(offset)

                    # Count query
                    buy_count_stmt = select(func.count()).select_from(CryptoBuy)

                    if buy_conditions:
                        buy_count_stmt = buy_count_stmt.where(and_(*buy_conditions))
                    
                    # Execute the queries
                    buy_count = (await session.execute(buy_count_stmt)).scalar()

                    user_buy_transaction_obj = await session.execute(buy_stmt)
                    user_buy_transaction = user_buy_transaction_obj.fetchall()

                else:
                    user_buy_transaction = []
                    buy_count = 0

                if transactionType == 'Sell' or not transactionType:
                    sell_stmt = select(
                        CryptoSell.id, 
                        CryptoSell.crypto_quantity, 
                        CryptoSell.payment_type,
                        CryptoSell.received_amount, 
                        CryptoSell.fee_value, 
                        CryptoSell.created_at,
                        CryptoSell.status, 
                        CryptoWallet.crypto_name, 
                        Wallet.currency.label('wallet_currency')
                        
                    ).join(
                        CryptoWallet, CryptoWallet.id == CryptoSell.crypto_wallet_id
                    ).join(
                        Wallet, Wallet.id == CryptoSell.wallet_id
                    )

                    # Apply conditions only if sell_conditions is not empty
                    if sell_conditions:
                        sell_stmt = sell_stmt.where(and_(*sell_conditions))

                    # Apply ordering, limit, and offset
                    sell_stmt = sell_stmt.order_by(desc(CryptoSell.id)).limit(limit).offset(offset)

                    # Count query
                    sell_count_stmt = select(func.count()).select_from(CryptoSell)
                    if sell_conditions:
                        sell_count_stmt = sell_count_stmt.where(and_(*sell_conditions))
                    
                    # Execute the queries
                    sell_count = (await session.execute(sell_count_stmt)).scalar()
                    
                    user_sell_transactio_obj = await session.execute(sell_stmt)
                    user_sell_transaction = user_sell_transactio_obj.fetchall()

                else:
                    user_sell_transaction = []
                    sell_count = 0

                ### No data found
                if not user_buy_transaction and not user_sell_transaction:
                    return json({'message': 'No data found'}, 404)


                ### Count Paginated value
                total_buy_sell_count = buy_count + sell_count
                paginated_count      = total_buy_sell_count / limit if limit > 0 else 1

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
                        'created_at': buyTransaction.created_at

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
                        'created_at': sellTransaction.created_at

                    } for sellTransaction in user_sell_transaction
                ]

                
                if not combined_transaction:
                    return json({'message': 'No data found'}, 404)
            
                return json({
                    'success': True,
                    'filtered_user_crypto_transaction': combined_transaction,
                    'paginated_count': paginated_count
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)


