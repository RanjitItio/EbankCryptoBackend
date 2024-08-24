from blacksheep import Request, json, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import UserKeys, Users
from sqlmodel import select





# Get Merchant Keys by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/keys/')
async def merchantKeys(self, request: Request, merchant_id: int):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()
            
            if not adminUser.is_admin:
                return json({'message': 'Unauthorized Access'}, 401)
            
            # Admin authentication ends

            # Get the keys of the merchant
            merchantKeysobj = await session.execute(select(UserKeys).where(
                UserKeys.user_id == merchant_id
            ))
            merchantKeys = merchantKeysobj.scalar()

            return json({'success': True, 'admin_merchant_keys': merchantKeys}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)