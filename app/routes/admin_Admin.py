from blacksheep import Request, get, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Group
from URLs.admin_urls import all_admin_users
from sqlmodel import select, desc





# Get all the Admin users
@auth('userauth')
@get(f'{all_admin_users}')
async def AdminUsers(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'message': 'Admin authorization failed'}, 401)
            # Admin authentication ends here

            # Execute Join query to get user data
            stmt = select(
                Users.id,
                Users.full_name,
                Users.email,
                Users.phoneno,
                Users.address1,
                Users.is_admin,
                Users.is_active,

                Group.name.label('user_group')
            ).join(
                Group, Group.id == Users.group
            ).where(
                Users.is_admin == True
            ).order_by(
                desc(Users.id)
            )

            all_admin_user_obj = await session.execute(stmt)
            all_admin_user     = all_admin_user_obj.all()

            for admin_user in all_admin_user:
                combined_data.append({
                    'id': admin_user.id,
                    'full_name': admin_user.full_name,
                    'email': admin_user.email,
                    'mobile_number': admin_user.phoneno,
                    'group': admin_user.user_group,
                    'admin': admin_user.is_admin,
                    'status': admin_user.is_active
                })

            return json({'success': True, 'all_admin_users': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
