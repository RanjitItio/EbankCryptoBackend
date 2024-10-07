from blacksheep.server.controllers import APIController
from database.db import async_engine, AsyncSession
from Models.models import Wallet,  Users, Currency
from sqlmodel import select, join
from blacksheep import Request, json
from Models.schemas import CreateWalletSchemas
from blacksheep.server.responses import pretty_json
from app.auth import decode_token
from app.controllers.controllers import get, post, put, delete
from blacksheep.server.authorization import auth



## User wallet controller
class WalletController(APIController):

    @classmethod
    def route(cls):
        return 'api/v3/wallet/'
    
    @classmethod
    def class_name(cls):
        return "Wallet"
    

    @get()
    async def get_wallet():
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    available_wallets = await session.execute(select(Wallet))
                    all_wallets = available_wallets.scalars().all()

                    if not all_wallets:
                        return json({'msg': 'No wallet availabel'}, 404)

                except Exception as e:
                    return json({'msg': 'Unable to find any wallets'}, 404)
                
                return json({'wallets': all_wallets})
            
        except Exception as e:
            return json({'error': f'{str(e)}'}, 500)
        

    @post()
    async def create_wallet(self, request: Request, create_Wallet: CreateWalletSchemas):

        try:
            async with AsyncSession(async_engine) as session:

                #Get the user from mail
                try:
                    user = await session.execute(select(Users).where(Users.email == create_Wallet.email))
                    user_obj = user.scalars().first()

                    if not user_obj:
                        return json({'msg': 'User is not registered'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Unable to identify User'}, 400)
                

                try:
                    CreateWallet = Wallet(
                        user_id     = user_obj.id,
                        currency_id = create_Wallet.currency,
                        balance     = create_Wallet.balance,
                        is_active   = True
                    )
                    session.add(CreateWallet)
                    await session.commit()
                    await session.refresh(CreateWallet)

                    return json({'msg': 'Wallet created successfully', 'data': CreateWallet})

                except Exception as e:
                    return json({'error': f'Unable to create wallet'}, 400)
                
        except Exception as e:
            return json({'error': f'{str(e)}'}, 500)

    @put()
    async def update_wallet():
        async with AsyncSession(async_engine) as session:
            pass
    
    @delete
    async def delete_wallet():
        pass




# User wallet controller
class UseWiseWalletController(APIController):

    @classmethod
    def route(cls):
        return 'api/v3/user/wallet/'
    
    @classmethod
    def class_name(cls):
        return "Wallet"

    ## Get all the available wallet of the user
    @auth('userauth')
    @get()
    async def get_wallet(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                userID        = user_identity.claims.get('user_id') if user_identity else None
                
                #Get the wallets related to the user
                try:
                    user_wallet_obj = await session.execute(select(Wallet).where(
                        Wallet.user_id == userID
                        ))
                    user_wallets    = user_wallet_obj.scalars().all()

                    if not user_wallets:
                        return pretty_json({'msg': 'User Wallet not available'}, 404)

                except Exception as e:
                    return pretty_json({'msg': 'Unable to get the Wallet of user', 'error': f'{str(e)}'}, 400)
                
                return pretty_json({'msg': 'Wallet fetched suuccessfully', 'user_wallet_data': user_wallets})
            
        except Exception as e:
            return pretty_json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)

