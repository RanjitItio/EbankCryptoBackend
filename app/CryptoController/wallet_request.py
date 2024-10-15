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

                return json({
                    'success': True,
                    'user_crypto_wallet_data': user_wallets
                })

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)