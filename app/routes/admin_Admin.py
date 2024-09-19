from blacksheep import Request, get, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users, Group
from sqlmodel import select, desc, and_, func
from typing import List




# Get all the Admin users
@auth('userauth')
@get('/api/v2/admin/users/')
async def AdminUsers(request: Request, limit: int = 10, offset: int = 0):
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

            count_stmt     = select(func.count(Users.id)).select_from(Users).where(Users.is_admin == True)
            total_rows_obj = await session.execute(count_stmt)
            total_rows     = total_rows_obj.scalar()

            total_rows_count = total_rows / limit

            # Execute Join query to get user data
            stmt = select(
                Users.id,
                Users.full_name,
                Users.email,
                Users.phoneno,
                Users.is_admin,
                Users.is_active,

                Group.name.label('user_group')
            ).join(
                Group, Group.id == Users.group
            ).where(
                Users.is_admin == True
            ).limit(
                limit
            ).offset(
                offset
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

            return json({
                'success': True, 
                'all_admin_users': combined_data,
                'total_rows': total_rows_count
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)


# Export all AdMin user data
@auth('userauth')
@get('/api/v2/export/admin/users/')
async def ExportAdminUsers(request: Request):
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

            # Execute Join query to get admin data
            stmt = select(
                Users.id,
                Users.full_name,
                Users.email,
                Users.phoneno,

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
                })
            
            return json({'success': True, 'export_admin_data': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Search Admin users
@auth('userauth')
@get('/api/v2/search/admin/users/')
async def SearchAdminUsers(request: Request, query: str = ''):
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

            # Search Active status wise
            if query.lower() == 'active':
                searched_user_obj = await session.execute(select(Users).where(
                    and_(
                    Users.is_active   == True,
                    Users.is_admin    == True
                    )))

            # Search inactive status wise
            elif query.lower() == 'inactive':
                searched_user_obj = await session.execute(select(Users).where(
                    and_(
                        Users.is_active   == False, 
                        Users.is_admin    == True
                    )))
            
            else:
                try:
                    searched_user_obj = await session.execute(select(Users).where(
                        and_(
                            (Users.first_name.ilike(query)) |
                            (Users.lastname.ilike(query))   |
                            (Users.full_name.ilike(query))  |
                            (Users.email.ilike(query))      |
                            (Users.phoneno.ilike(query)),
                        )))

                except Exception as e:
                    return json({'msg': 'Search error', 'error': f'{str(e)}'}, 400)
                
            all_users: List[Users] = searched_user_obj.scalars().all()

            for user in all_users:
                group_query = select(Group).where(Group.id == user.group)
                group_result = await session.execute(group_query)
                group_data = group_result.scalar()

                group_name = group_data.name if group_data else None

                combined_data.append({
                    'id': user.id,
                    'full_name': user.full_name,
                    'email': user.email,
                    'mobile_number': user.phoneno,
                    'group': group_name,
                    'admin': user.is_admin,
                    'status': user.is_active
                })

            return json({'success': True, 'searched_admin_users': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)