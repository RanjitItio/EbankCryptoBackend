from blacksheep.server.controllers import APIController
from Models.schemas import UserLoginSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Admin, Users
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token
from app.auth import check_password
from app.controllers.controllers import post



class AdminLoginController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/admin/login'
    
    @classmethod
    def class_name(cls):
        return "Admin login"
    

    @post()
    async def login_adminuser(self,user :UserLoginSchema, request: Request):
        """
        This function handles the admin login process. It takes a UserLoginSchema object and a Request object as parameters.<br/>
        It authenticates the admin user based on the provided email and password.<br/><br/>

        Parameters:<br/>
        - user (UserLoginSchema): An object containing the email and password of the user.<br/>
        - request (Request): The request object containing information about the incoming HTTP request.<br/><br/>

        The function checks if the user exists, if it's an admin, and if the password is correct. If all checks pass, it generates access and refresh tokens. Otherwise, it returns an error message. The function also handles SQLAlchemyError exceptions.<br/>
        Returns:<br/>
        - JSON response with access and refresh tokens if the login is successful.<br/>
        - JSON response with an error message if the user is not available, unable to get the user, not an admin, or invalid credentials.<br/>
        - JSON response with an error message if a SQLAlchemyError occurs.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()

                    if not first_user:
                        return json({'msg': 'User is not available'}, 404)

                except Exception as e:
                    return json({'msg': "Unable to get the user", 'error': f'{str(e)}'}, 400)

                #Check the user is admin or not
                # Check the user is admin or not
                if not first_user.is_admin:
                    return json({'msg': 'Please provide admin credentials'}, 403)
  
                # If the user is admin and credentials are valid, generate access and refresh tokens#+
                if first_user and check_password(user.password, first_user.password):#+
                    return json({
                        'access_token': generate_access_token(first_user.id),
                        'refresh_token': generate_refresh_token(first_user.id)
                    },200)
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)

