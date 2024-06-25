from blacksheep import json, Request, FromJSON
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from app.auth import generate_merchant_secret_key
from app.controllers.controllers import get
from sqlmodel import select, and_
from Models.models import MerchantProfile, HashValue
from dataclasses import dataclass








#Generate New Secret Key for Every Merchant
class GenerateMerchantSecretKey(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Generate Merchant Secret Key'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/merchant/secret/key/'
    
    @auth('userauth')
    @get()
    async def Generate_Secret_Key(self, request: Request, query: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                business_id = query

                #Get The Business profile related to the user
                try:
                    business_profile_obj = await session.execute(select(MerchantProfile).where(
                        and_(MerchantProfile.user == user_id, MerchantProfile.id == business_id)
                    ))
                    business_profile = business_profile_obj.scalar()

                    if not business_profile:
                        return json({'msg': 'Business profile not found'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'Business profile fetch error', 'error': f'{str(e)}'}, 400)
                
                #Get The secret key
                secret_key = business_profile.secret_key

                #Find the secret key in Hashtable
                if secret_key:
                    hash_key_obj = await session.execute(select(HashValue).where(HashValue.hash_value == secret_key))
                    hash_key     = hash_key_obj.scalar()

                #Generate new secret key
                new_secret_key = await generate_merchant_secret_key(business_profile.id)

                business_profile.secret_key = new_secret_key

                if hash_key:
                    await session.delete(hash_key)

                session.add(business_profile)
                await session.commit()
                await session.refresh(business_profile)

                return json({'msg': 'Key generated successfully', 'data': new_secret_key})

        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
        


    