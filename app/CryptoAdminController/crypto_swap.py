from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from app.controllers.controllers import get, post, put
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.crypto import CryptoSwap, CryptoWallet
from sqlmodel import select, desc, func
from sqlalchemy.orm import aliased
from Models.Crypto.schema import AdminUpdateCryptoSwap



### Crypto Swap Controller
class AdminCryptoSwapController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Admin Crypto Swap'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/crypto/swap/'
    

    @auth('userauth')
    @get()
    async def get_swapTransactions(self, request: Request, limit: int = 10, offset: int = 0):
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
                row_stmt      = select(func.count(CryptoWallet.id))
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
