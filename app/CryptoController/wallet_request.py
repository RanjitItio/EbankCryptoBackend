from app.controllers.controllers import post, get
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.crypto import CryptoWallet
from Models.Crypto.schema import CreateWalletRequestSchema




## Crypto Wallet
class CryptoWalletController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/user/crypto/wallet/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Raise Wallet Request'
    
    
    ## Raise New Wallet request for user
    @auth('userauth')
    @post()
    async def create_userWallet(self, request: Request, schema: CreateWalletRequestSchema):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ## Get the data from Payload
                cryptoName = schema.crypto

                ## Wallet exists check
                user_wallet_obj = await session.execute(select(CryptoWallet).where(
                    and_(
                        CryptoWallet.user_id == user_id,
                        CryptoWallet.crypto_name == cryptoName
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if user_wallet:
                    return json({'message': 'Wallet already exists for given crypto'}, 400)


                ## Create a wallet request
                crypto_wallet = CryptoWallet(
                    user_id = user_id,
                    crypto_name = cryptoName
                )

                session.add(crypto_wallet)
                await session.commit()
                await session.refresh(crypto_wallet)

                return json({
                    'success': True,
                    'message': 'Wallet Created Successfully'
                }, 201)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        

    ## Get all the wallet requested by the user
    @auth('userauth')
    @get()
    async def get_userWallets(self, request: Request, limit: int = 6, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                ## Get the wallets related to the user
                user_wallets_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.user_id == user_id
                ).limit(
                    limit
                    ).offset(
                        offset
                    )
                )
                user_wallets = user_wallets_obj.scalars().all()

                count_stmt      = select(func.count(CryptoWallet.id))
                exec_count_stmt = await session.execute(count_stmt)
                total_rows      = exec_count_stmt.scalar()

                total_row_count = total_rows / limit

                return json({
                    'success': True,
                    'user_crypto_wallet_data': user_wallets,
                    'total_row_count': total_row_count
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
        


## All available Crypto wallets of user
class UserCryptoWalletsController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return '''User's all crypto wallets'''
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/wallets/'
    
    @auth('userauth')
    @get()
    async def get_userWallets(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get all the Wallets of user
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.user_id == user_id
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalars().all()

                return json({
                    'success': True,
                    'user_crypto_wallets': user_crypto_wallet
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
                }, 500)
        


## All available Crypto wallets of user
class UserCryptoWalletAdressController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return '''User's all crypto wallets'''
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/wallet/address/{crypto_wallet}/'
    
    
    @auth('userauth')
    @get()
    async def get_userWalletAddress(self, request: Request, crypto_wallet: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get all the Wallets of user
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    and_(
                        CryptoWallet.id      == crypto_wallet,
                        CryptoWallet.user_id == user_id
                    )
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Wallet not found'}, 404)
                
                wallet_address = user_crypto_wallet.wallet_address

                return json({
                    'success': True,
                    'wallet_address': wallet_address
                }, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)



        
