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
    """
        Get all the Admin users.<br/>
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            - limit (optional): Limit the number of records returned (default: 10).<br/>
            - offset (optional): Offset the number of records to skip (default: 0).<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the list of all admin users and the total number of rows.<br/><br/>

        Raises:<br/>
            - 401: Unauthorized request if the user is not an admin.<br/>
            - 500: Server error if an error occurs during the database operations.<br/>
            - 404: Not Found if no admin users are found.<br/>
        
        Error Messages:<br/>
            - Unauthorized: If the user is not an admin.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
    """
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
    """
        This function exports all admin users data for admin users after authentication.<br/><br/>
        
        Parameters:<br/>
        - request (Request): The HTTP request object received by the API endpoint.<br/><br/>
        
        Returns:<br/>
        - JSON: A JSON response containing the exported admin user data.<br/>
        - HTTP Status Code: 200<br/>
        - HTTP Status Code: 500 in case of server errors.<br/>
        - HTTP Status Code: 401 in case of unauthorized access.<br/><br/>

        Raises:<br/>
        - BadRequest: If the request data is invalid.<br/>
        - SQLAlchemyError: If there is an error during database operations.<br/>
        - Exception: If any other unexpected error occurs.<br/>
    """
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
    """
        Admin will be able to search Admin users by their first name, last name, email, and status.<br/><br/>

        Parameters:<br/>
            query (str): Search query for first name, last name, email, and status.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            JSON: Returns a list of user details that match the search query.<br/>
            'searched_admin_users': List of user details<br/>
            'success': successful transaction status.<br/><br/>

        Raises:<br/>
            Exception: If any error occurs during the database query or response generation.<br/>
            Error 401: 'error': 'Unauthorized Access'.<br/>
            Error 500: 'error': 'Server Error'.<br/><br/>

        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
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