from blacksheep.server.controllers import APIController
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from app.controllers.controllers import get
from database.db import AsyncSession, async_engine
from Models.models import UserKeys
from sqlmodel import select





# Get merchant Public and Secret keys
class MerchantKeysController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Keys'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v3/merchant/keys/'
    
    @auth('userauth')
    @get()
    async def merchant_keys(self, request: Request):
        """
            This API Endpoint retrieves merchant keys for a user and returns them in a JSON response.<br/><br/>
            
            Parameters:<br/>
            - request: The HTTP request object<br/><br/>
            
            Returns:<br/>
            - JSON: A JSON response containing the merchant's public key, secret key, creation date, and status.<br/><br/>
            
            Raises:<br/>
            - If the user does not exist, returns a 404 status code with an error message<br/>
            - If there is an error during the process, returns a 500 status code with an error message<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                try:
                    merchant_keys_obj = await session.execute(select(UserKeys).where(
                        UserKeys.user_id == user_id
                    ))
                    merchant_keys = merchant_keys_obj.scalar()

                    if not merchant_keys:
                        return json({'error': 'Merchant key not found'}, 404)
                    
                except Exception as e:
                    return json({'error': 'Merchant key fetch error', 'error': f'{str(e)}'}, 400)
                
                merchant_public_key = merchant_keys.public_key
                merchant_secret_key = merchant_keys.secret_key
                created_date        = merchant_keys.created_at
                status              = merchant_keys.is_active

                return json({'success': True, 
                             'merchantPublicKey': merchant_public_key,
                             'merchantSecretKey': merchant_secret_key,
                             'createdAt': created_date,
                             'status': status
                             }, 200)

        except Exception as e:
            return json({'error': 'Server Error'}, 500)
