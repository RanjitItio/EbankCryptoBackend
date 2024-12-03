from blacksheep import json, Request, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from app.auth import generate_access_token, generate_refresh_token
from sqlmodel import select




# Let the admin login into merchant dashboard
@auth('userauth')
@get('/api/v6/admin/merchant/login/{user_id}/')
async def merchant_login_dashboard(request: Request, user_id: int):
    """
        This API Endpoint let admin login into every merchant dashboard.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object.<br/>
            - user_id (int): The ID of the user.<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the access and refresh tokens for the admin.<br/>
            - Error: A JSON response with an error message if the user is not an admin or the user does not exist.<br/>
            - Error 401: Unauthorized.<br/><br/>

        Raises:<br/>
            - HTTPException: If the user is not authenticated or if the user does not exist.<br/>
            - HTTPStatus: 401 Unauthorized if the user is not an admin.<br/>
            - HTTPStatus: 404 Not Found if the user does not exist.<br/>
            - HTTPStatus: 400 Bad Request if the user is inactive.<br/><br/>

        Error message:<br/>
            - 'message': 'Admin authorization failed'<br/>
            - 'message': 'User not found'br/>
            - 'message': 'Inactiv user'<br/>
            - 'error': 'Server Error'<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            #Authenticate user ad admin
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id') if user_identity else None

            admin_user_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_object.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization failed'}, 401)
            # Admin authentication ends


            # Get the user
            merchant_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            merchant_user     = merchant_user_obj.scalar()

            if not merchant_user:
                return json({'message': 'User not found'}, 404)
            
            # Inactive user
            if not merchant_user.is_active:
                return json({'message': 'Inactiv user'}, 400)
            
            access_token  = generate_access_token(merchant_user.id)
            refresh_token = generate_refresh_token(merchant_user.id)

            return json({
                'success': True,
                'access': access_token,
                'refresh': refresh_token,
                'user_name': merchant_user.full_name,
                'is_merchant': merchant_user.is_merchent
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)