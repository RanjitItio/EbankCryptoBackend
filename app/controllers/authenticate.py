from app.controllers.controllers import get, post
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Wallet, Currency
from Models.crypto import CryptoWallet
from sqlmodel import select, and_




class AuthenticateCheckController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Authenticated Route'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/authenticate/user/'
    
    @auth('userauth')
    @get()
    async def check_authentication():
        return json({'authenticated': True}, 200)
    


### User email authentication
class UserEmailAuthentication(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Authenticate Email Address'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/authenticate/email/'
    

    @post()
    async def authenticate_user_email(self, request: Request):
        """
            Authenticates a user's email address and checks if the user has a wallet for the specified currency.<br /><br />
    
            Parameters:<br />
            - request (Request): The incoming request object containing the user's email and currency.<br /><br />
    
            Returns:<br />
            - JSON response with success status and message if the authentication and wallet existence checks pass.<br />
            - JSON response with error status and message if any exception occurs or if the authentication or wallet existence checks fail.<br />
        """
        try:
            async with AsyncSession(async_engine) as session:
                request_data = await request.json()

                email    = request_data['email']
                currency = request_data['currency']

                user_email_authenticate_obj = await session.execute(select(Users).where(
                    Users.email == email
                ))
                user_email_authenticate = user_email_authenticate_obj.scalar()

                ## Get the Currency
                user_currency_obj = await session.execute(select(Currency).where(
                    Currency.name == currency
                ))
                user_currency = user_currency_obj.scalar()

                if not user_currency:
                    return json({'message': 'Invalid Receiver Currency'}, 400)
                
                
                if not user_email_authenticate:
                    return json({
                        'message': 'Email address not found'
                    }, 404)
                
                ## Get user Wallet
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.user_id     == user_email_authenticate.id,
                        Wallet.currency_id == user_currency.id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'User wallet not found'}, 404)
                
                
                return json({
                    'success': True
                }, 200)

        except Exception as e:
            return json({
                        'error': 'Server Error',
                         'message': f'{str(e)}'
                         }, 500)



### Check user Wallet Balance
class UserWalletBalanceController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'User Wallet Balance Check'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/user/wallet/balance/check/'
    
    
    @auth('userauth')
    @post()
    async def user_wallet_balance(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_data    = await request.json()
                sender_currency = request_data['sender_currency']
                send_amount     = request_data['send_amount']

                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == sender_currency
                ))
                currency = currency_obj.scalar()

                #### User Wallet
                user_wallet_obj = await session.execute(select(Wallet).where(
                    and_(
                        Wallet.user_id == user_id,
                        Wallet.currency_id  == currency.id
                    )
                ))
                user_wallet = user_wallet_obj.scalar()

                if not user_wallet:
                    return json({'message': 'Wallet does not exists for given currency'}, 404)
                
                if float(send_amount) > user_wallet.balance:
                    return json({'message': 'Donot have sufficient balance in Wallet'}, 400)
                
                return json({
                    'success': True
                }, 200)
                
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



## Check Crypto Wallet Balance
class UserCryptoWalletBalanceCheck(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Check Crypto Wallet Balance Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/user/crypto/wallet/balance/check/'
    
    
    ### Check user crypto wallet balance
    @auth('userauth')
    @post()
    async def crypto_wallet_balance_check(self, request: Request):
        """
            This function is responsible for checking the balance of a specified crypto wallet.<br/><br/>

            Parameters:<br/>
              - request (Request): The incoming request object containing user identity and wallet details.<br/><br/>

            Returns:<br/>
              - JSON response with success status and message if the balance is sufficient.<br/>
              - JSON response with error status and message if an exception occurs or the balance is insufficient.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_data = await request.json()
                wallet_id    = request_data['wallet_id']
                amount       = request_data['amount']

                ## Get the Crypto wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == wallet_id
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Wallet not found'}, 404)
                
                if not user_crypto_wallet.is_approved:
                    return json({'message': 'Inactive Wallet'}, 400)
                
                if user_crypto_wallet.balance < float(amount):
                    return json({'message': 'Donot have sufficient balance in Wallet'}, 400)
                

                return json({'success': True}, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
                




### Check Crypto Wallet Active or Inactive
class UserCryptoWalletBalanceCheck(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Check Crypto Wallet Active Status'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/user/crypto/wallet/active/status/'
    
    
    ### Check user crypto wallet balance
    @auth('userauth')
    @post()
    async def crypto_wallet_active_status(self, request: Request):
        """
            This function checks the active status of a user's crypto wallet.<br/><br/>

            Parameters:<br/>
            - request (Request): The incoming request object containing user identity and wallet ID.<br/><br/>

            Returns:<br/>
            - JSON response:<br/>
                - If the wallet is found and active, returns a success message with status code 200.<br/>
                - If the wallet is not found, returns a not found message with status code 404.<br/>
                - If the wallet is inactive, returns an inactive wallet message with status code 400.<br/>
                - If an error occurs during processing, returns a server error message with status code 500.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_data = await request.json()
                wallet_id    = request_data['wallet_id']

                ## Get the Crypto wallet
                user_crypto_wallet_obj = await session.execute(select(CryptoWallet).where(
                    CryptoWallet.id == wallet_id
                ))
                user_crypto_wallet = user_crypto_wallet_obj.scalar()

                if not user_crypto_wallet:
                    return json({'message': 'Wallet not found'}, 404)
                
                if not user_crypto_wallet.is_approved:
                    return json({'message': 'Inactive Wallet'}, 400)


                return json({'success': True}, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)