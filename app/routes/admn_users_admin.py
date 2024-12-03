from blacksheep import get, Request, json, pretty_json
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from sqlmodel import select
from Models.models import Users




@auth('userauth')
@get('/api/admin/all-admin/')
async def get_all_admin(self, request: Request):
    """
        Admin will be able to view all the admin users in the system.<br/><br/>

        Parameters:<br/>
            - request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: Returns a list of admin users.<br/>
            - 'data': List of admin users<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 400: 'error': 'Only admin can view the Transactions'.<br/><br/>

        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 400: 'error': 'Only admin can view the Transactions'.<br/>
            - Error 404: 'error': 'No admin users available'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            AdminID         = user_identity.claims.get("user_id") if user_identity else None

            #Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
            try:
                all_admin_users = await session.execute(select(Users).where(Users.is_admin == True))
                all_admin_user_obj = all_admin_users.scalars().all()

                if not all_admin_user_obj:
                    return json({'msg': 'No admin users available'}, 404)
                
            except Exception as e:
                return json({'msg': 'Admin fetch error', 'error': f'{str(e)}'}, 400)
            
            filtered_data = []
            
            for admin_details in all_admin_user_obj:
                admin_data = {
                    'first_name': admin_details.first_name,
                    'last_name': admin_details.lastname,
                    'lastlogin': admin_details.lastlogin,
                    'email': admin_details.email,
                    'city': admin_details.city,
                    'state': admin_details.state,
                    'country': admin_details.country,
                }

                filtered_data.append(admin_data)

            return json({'msg': 'Data fetched successfully', 'data': filtered_data})

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)


