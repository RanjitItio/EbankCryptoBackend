from blacksheep import json, Request, FromJSON
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from app.auth import update_merchant_secret_key, generate_merchant_unique_public_key
from app.controllers.controllers import get
from sqlmodel import select, and_
from Models.models import MerchantProfile, HashValue, UserKeys, Users
from datetime import datetime







#Generate New Secret Key for Every Merchant
class GenerateMerchantSecretKey(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Generate Merchant Keys'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/genearte/keys/'
    
    @auth('userauth')
    @get()
    async def Generate_merchnant_Keys(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                #Get The Business profile related to the user
                try:
                    merchant_key_obj = await session.execute(select(UserKeys).where(
                        UserKeys.user_id == user_id
                    ))
                    merchant_key = merchant_key_obj.scalar()

                    if not merchant_key:
                        user_obj = await session.execute(select(Users).where(
                            Users.id == user_id
                        ))
                        user = user_obj.scalar()

                        if not user:
                            return json({'error': 'User not found'}, 404)
                        
                        user_keys_obj = UserKeys(
                            user_id    = user.id,
                            public_key = '',
                            secret_key = '',
                            created_at = datetime.now()
                        )

                        session.add(user_keys_obj)
                        await session.commit()
                        await session.refresh(user_keys_obj)

                        merchant_key = user_keys_obj
                        
                except Exception as e:
                    return json({'msg': 'User Key fetch error', 'error': f'{str(e)}'}, 400)
                
                #Get The secret key
                secret_key = merchant_key.secret_key

                #Generate new public and secret key
                new_secret_key = await update_merchant_secret_key(merchant_key.user_id, secret_key)
                new_public_key = await generate_merchant_unique_public_key()

                merchant_key.secret_key = new_secret_key
                merchant_key.public_key = new_public_key
                merchant_key.created_at = datetime.now()
                
                session.add(merchant_key)
                await session.commit()
                await session.refresh(merchant_key)

                return json({'msg': 'Key generated successfully', 'data': merchant_key}, 200)

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        


    