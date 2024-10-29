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
                
                if user_crypto_wallet.balance < float(amount):
                    return json({'message': 'Donot have sufficient balance in Wallet'}, 400)
                
                return json({'success': True}, 200)

        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
            }, 500)
                

