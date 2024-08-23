from blacksheep import get, json, Request
from blacksheep.server.authorization import auth
from Models.models import Users
from Models.models2 import CollectedFees
from database.db import AsyncSession, async_engine
from URLs.admin_urls import get_revenues
from sqlmodel import select




# Get all collected Revenues
@auth('userauth')
@get(f'{get_revenues}')
async def GetAdminRevenues(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'message': 'Unauthorized access'}, 401)
            # Authentication ends here

            collctedFeesObj = await session.execute(select(CollectedFees))
            collectedFees   = collctedFeesObj.scalars().all()

            return json({'success': True, 'collectedFees': collectedFees}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)







