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
                

                ## Balance Validation
                if user_fiat_wallet.balance <= user_crypto_buy_transaction.buying_amount:
                    return json({'message': 'Insufficient funds'}, 400)
                
                ## Already Approved
                if user_crypto_buy_transaction.is_approved:
                    return json({'message': 'Already approved'}, 400)
                

                if status == 'Approved':
                    ## Add crypto into Crypto wallet
                    user_crypto_wallet.balance += user_crypto_buy_transaction.crypto_quantity

                    ## Deduct from Fiat Wallet
                    calculate_fee = user_crypto_buy_transaction.buying_amount + user_crypto_buy_transaction.fee_value

                    user_fiat_wallet.balance -= calculate_fee

                    ## Save into CryptoBuy Table
                    user_crypto_buy_transaction.status = 'Approved'
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
                
                ## Balance Validation
                if user_crypto_wallet.balance <= user_crypto_sell_transaction.received_amount:
                    return json({'message': 'Insufficient funds'}, 400)
                
                ## Already Approved
                if user_crypto_sell_transaction.is_approved:
                    return json({'message': 'Already approved'}, 400)
                

                if status == 'Approved':
                   
                    ## Deduct from crypto into Crypto wallet
                    calculate_fee = user_crypto_sell_transaction.received_amount + user_crypto_sell_transaction.fee_value
                    user_crypto_wallet.balance -= calculate_fee

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
        return 'Crypto Sell Controller'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/admin/crypto/transactions/'
    
    
    ## Get all crypto transactions
    @auth('userauth')
    @get()
    async def get_cryptoTransactions(self, request: Request,  limit: int = 4, offset: int = 0):
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
    async def filter_cryptoTransactions(self, request: Request, schema: AdminFilterCryptoTransactionsSchema):
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
                conditions = []

                ## Get payload data
                dateRange       = schema.date_range
                userEmail       = schema.user_email
                cryptoName      = schema.crypto_name
                transactionType = schema.transaction_type

                ## Filter date range wise
                if dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(

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
                    
                    conditions.append(

                    )

                # Filter Crypto Name wise
                if cryptoName:
                    pass

                if transactionType:
                    pass

                return json({})

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