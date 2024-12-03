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
        """
            This API Endpoint is responsible for creating a new crypto wallet for user in the system.<br/><br/>

            Parameters:<br/>
                - request (Request): The incoming request object containing user identity and payload data.<br/>
                - schema (CreateWalletRequestSchema): The schema object containing the crypto name.<br/><br/>
            
            Returns:<br/>
            - JSON: Json response containing the success message and  a boolean value.<br/>
            - Wallet already exists for given crypto: if the wallet already exists for the given user.<br/><br/>

            Error message:
                - 500: Server Error<br/>c
                - 400: Bad Request<br/>
                - 404: Wallet not found<br/>
        """
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
        """
            This API Endpoint is responsible for retrieving all the crypto wallets requested by a user.<br/><br/>

            Parameters:<br/>
            - request (Request): The incoming request object containing user identity.<br/>
            - limit (int): The maximum number of wallets to retrieve per page. Default is 6.<br/>
            - offset (int): The number of wallets to skip before starting to retrieve. Default is 0.<br/><br/>

            Returns:<br/>
            - JSON: Json response containing the success message, user's crypto wallet data, and the total number of pages.<br/><br/>

            Error message:<br/>
            - 500: Server Error.<br/>
        """
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
        """
            This function retrieves all the crypto wallets of a user.<br/><br/>
            
            Parameters:<br/>
                - request (Request): The incoming request object containing user identity.<br/><br/>
            
            Returns:<br/>
                - JSON response with success status 200 and user's crypto wallets if found.<br/>
                - JSON response with error status 404 and message if no wallets found.<br/>
                - JSON response with error status 500 and message if any exception occurs during the database operations.<br/><br/>

            Error message:<br/>
              - No wallets found - if the user does not have any wallets.<br/>
        """
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
        return "User's Crypto wallet Address"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/user/crypto/wallet/address/{crypto_wallet}/'
    
    
    @auth('userauth')
    @get()
    async def get_userWalletAddress(self, request: Request, crypto_wallet: int):
        """
            This function retrieves the wallet address of the specified crypto wallet of the user. It requires an authenticated user.<br/><br/>

            Parameters:<br/>
                - request (Request): The HTTP request object containing the user's identity.<br/>
                - crypto_wallet (int): The ID of the crypto wallet to retrieve the address for.<br/><br/>
            
            Returns:<br/>
                - JSON: A JSON response containing the wallet address and success status.<br/><br/>

            Error Messages:<br/>
                - Wallet not found: If the specified crypto wallet ID does not exist for the user.<br/>
                - Server Error: If an error occurs during the database operations.<br/>
        """
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



        
