from app.controllers.controllers import get, post, put
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from sqlmodel import select, and_, desc, func
from database.db import AsyncSession, async_engine
from Models.models import Users, Wallet
from Models.crypto import CryptoExchange, CryptoWallet
from Models.Admin.Crypto.schema import AdminUpdateCryptoExchange




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