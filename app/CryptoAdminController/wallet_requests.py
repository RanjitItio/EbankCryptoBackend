from app.controllers.controllers import post, get, put
from app.FireBlock import Create_Wallet
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.crypto import CryptoWallet
from Models.models import Users
from Models.Crypto.schema import UpdateAdminCryptoWalletSchema, AdminFilterUserWalletSchema
from app.dateFormat import get_date_range




## Crypto Wallet Controller for Admin
class AdminCryptoWalletController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/admin/crypto/wallets/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'All user Crypto Wallets'
    
    ### Get wallet of all users
    @auth('userauth')
    @get()
    async def get_userWallets(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                # Admin authentication
                admin_user_obj = await session.execute(select(Users).where(Users.id == admin_id))
                admin_user     = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authoriztion Failed'}, 401)
                # Admin authentication ends

                # Count Total availble rows
                total_row_stmt = select(func.count(CryptoWallet.id))
                total_row_obj  = await session.execute(total_row_stmt)

                total_rows_count = total_row_obj.scalar()

                rows = total_rows_count / limit
                
                # execute query
                stmt = select(
                    CryptoWallet.id,
                    CryptoWallet.user_id,
                    CryptoWallet.wallet_address,
                    CryptoWallet.created_At,
                    CryptoWallet.crypto_name,
                    CryptoWallet.balance,
                    CryptoWallet.status,
                    CryptoWallet.is_approved,

                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoWallet.user_id
                ).order_by(
                    desc(CryptoWallet.id)
                ).limit(
                    limit
                ).offset(
                    offset
                )

                user_crypto_wallets_obj = await session.execute(stmt)
                user_crypto_wallets     = user_crypto_wallets_obj.all()

                combined_data = []

                for wallet in user_crypto_wallets:
                    combined_data.append({
                        'id': wallet.id,
                        'user_id': wallet.user_id,
                        'wallet_address': wallet.wallet_address,
                        'created_At': wallet.created_At,
                        'crypto_name': wallet.crypto_name,
                        'balance': wallet.balance,
                        'status': wallet.status,
                        'user_name': wallet.full_name,
                        'user_email': wallet.email
                    })

                return json({
                    'success': True,
                    'all_user_crypto_wallets': combined_data,
                    'total_rows': rows
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        
    
    ## Update Crypto Wallet by Admin
    @auth('userauth')
    @put()
    async def update_cryptoWallet(self, request: Request, schema: UpdateAdminCryptoWalletSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                # Admin authentication
                admin_user_obj = await session.execute(select(Users).where(Users.id == admin_id))
                admin_user     = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authoriztion Failed'}, 401)
                # Admin authentication ends

                ## Get the payload data
                walletID = schema.wallet_id
                status   = schema.status

                # Get the wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == walletID
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                # Get the user
                wallet_user_obj = await session.execute(select(Users).where(
                    Users.id == user_crypto_wallet.user_id
                ))
                wallet_user = wallet_user_obj.scalar()

                # if user_crypto_wallet.is_approved:
                #     return json({'message': 'Wallet already created'}, 400)

                if status == 'Approved':
                    if not user_crypto_wallet.wallet_address:
                        vault_name =  wallet_user.full_name + '_' + str(user_crypto_wallet.id)

                        # Call Fireblock api
                        if user_crypto_wallet.crypto_name == 'ETH':
                            asset_name = 'ETH_TEST5'
                        else:
                            asset_name = user_crypto_wallet.crypto_name + '_TEST'

                        createWallet = Create_Wallet(vault_name, asset_name)

                        if createWallet['address']:
                            user_crypto_wallet.wallet_address = createWallet['address']
                            session.add(user_crypto_wallet)
                    
                    user_crypto_wallet.is_approved = True
                    user_crypto_wallet.status      = status

                    session.add(user_crypto_wallet)

                else:
                    user_crypto_wallet.status      = status
                    user_crypto_wallet.is_approved = False

                    session.add(user_crypto_wallet)

                await session.commit()
                await session.refresh(user_crypto_wallet)


                return json({
                    'success': True,
                    'message': 'Updated Successfully'
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
        


    ## Filter Wallet Requests
    @auth('userauth')
    @post()
    async def filter_wallets(self, request: Request, schema: AdminFilterUserWalletSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                # Admin authentication
                admin_user_obj = await session.execute(select(Users).where(Users.id == admin_id))
                admin_user     = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Unauthorized'}, 401)
                # Admin authentication ends

                ## Get payload data
                dateRange    = schema.date_range
                email        = schema.email
                crypto_name  = schema.crypto_name
                status       = schema.status

                conditions    = []
                combined_data = []

                stmt = select(
                    CryptoWallet
                )

                ## Filter according to the Input date time
                if dateRange:
                    start_date, end_date = get_date_range(dateRange)

                    conditions.append(
                        and_(
                            CryptoWallet.created_At >= start_date,
                            CryptoWallet.created_At <= end_date
                        )
                    )
                
                ## Filter Email wise
                if email:
                    user_email_obj = await session.execute(select(Users).where(
                        Users.email.like(f"{email}%")
                    ))
                    user_email = user_email_obj.scalar()

                    if not user_email:
                         return json({'message': 'Invalid Email'}, 400)
                    
                    conditions.append(
                        CryptoWallet.user_id == user_email.id
                    )

                ## Filter Crypto Name wise
                if crypto_name:
                    conditions.append(
                        CryptoWallet.crypto_name.ilike(f"{crypto_name}%")
                    )

                ## Filter status wise
                if status:
                    conditions.append(
                        CryptoWallet.status.ilike(f"{status}%")
                    )


                # execute query
                stmt = select(
                    CryptoWallet.id,
                    CryptoWallet.user_id,
                    CryptoWallet.wallet_address,
                    CryptoWallet.created_At,
                    CryptoWallet.crypto_name,
                    CryptoWallet.balance,
                    CryptoWallet.status,
                    CryptoWallet.is_approved,

                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoWallet.user_id
                ).order_by(
                    desc(CryptoWallet.id)
                )
                
                if conditions:
                    statement = stmt.where(and_(*conditions))
                    
                    user_wallet_object = await session.execute(statement)
                    user_wallets        = user_wallet_object.fetchall()
     
                    if not user_wallets:
                         return json({'message': 'No wallet found'}, 404)
                    
                else:
                    return json({'message': 'No wallet found'}, 404)


                for wallet in user_wallets:
                    combined_data.append({
                        'id': wallet.id,
                        'user_id': wallet.user_id,
                        'wallet_address': wallet.wallet_address,
                        'created_At': wallet.created_At,
                        'crypto_name': wallet.crypto_name,
                        'balance': wallet.balance,
                        'status': wallet.status,
                        'user_name': wallet.full_name,
                        'user_email': wallet.email
                    })

                return json({
                    'success': True,
                    'all_user_crypto_wallets': combined_data,
                }, 200)


        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



## Export All Cryppto Wallets
class ExportWalletController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Export Crypto Wallets'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/admin/export/crypto/wallets/'
    
    
    ### Export All wallets
    @auth('userauth')
    @get()
    async def export_cryptoWallets(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                stmt = select(
                    CryptoWallet.id,
                    CryptoWallet.user_id,
                    CryptoWallet.wallet_address,
                    CryptoWallet.created_At,
                    CryptoWallet.crypto_name,
                    CryptoWallet.balance,
                    CryptoWallet.status,
                    CryptoWallet.is_approved,

                    Users.full_name,
                    Users.email,
                ).join(
                    Users, Users.id == CryptoWallet.user_id
                ).order_by(
                    desc(CryptoWallet.id)
                )

                user_crypto_wallets_obj = await session.execute(stmt)
                user_crypto_wallets     = user_crypto_wallets_obj.all()

                combined_data = []

                for wallet in user_crypto_wallets:
                    combined_data.append({
                        'id': wallet.id,
                        'user_id': wallet.user_id,
                        'wallet_address': wallet.wallet_address,
                        'created_At': wallet.created_At,
                        'crypto_name': wallet.crypto_name,
                        'balance': wallet.balance,
                        'status': wallet.status,
                        'user_name': wallet.full_name,
                        'user_email': wallet.email
                    })

                return json({
                    'success': True,
                    'export_wallets_data': combined_data
                }, 200)
            

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)