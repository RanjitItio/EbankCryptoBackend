from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from Models.models2 import MerchantAccountBalance
from database.db import AsyncSession, async_engine
from app.controllers.controllers import get
from sqlmodel import select, and_




###########################
# Merchant Account Balance
###########################
class MerchantAccountBalanceController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Account Balance'

    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/merchant/account/balance/'
    

    @auth('userauth')
    @get()
    async def get_merchantAccountBalance(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate User
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None
                
                if user_id is None:
                    return json({'error': 'Unauthorized'}, 401)
                
                # Get merchant Account Balance
                merchantBalanceObj = await session.execute(select(MerchantAccountBalance).where(
                    MerchantAccountBalance.merchant_id == user_id
                ))
                merchantBalance = merchantBalanceObj.scalars().all()

                if not merchantBalance:
                    return json({'error': 'No Merchant Balance availabel'}, 404)
                
                return json({'success': True, 'merchantAccountBalance': merchantBalance}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500) 