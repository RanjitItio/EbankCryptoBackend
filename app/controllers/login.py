from blacksheep.server.controllers import APIController
from Models.schemas import UserCreateSchema, UserLoginSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users, Kycdetails
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password
from datetime import datetime
from app.controllers.controllers import get, post, put, delete




# Login user
class UserLoginController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/login/'

    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @post()
    async def login_user(self, user: UserLoginSchema):
        """
            Login user with given email and password.<br/><br/>

            Parameters:<br/>
                user (UserLoginSchema): An instance of UserLoginSchema containing the user's email and password.<br/><br/>
            
            Returns:<br/>
                JSON response with access and refresh tokens if the login is successful.<br/>
                JSON response with error message if the user is not available, unable to get the user, not an admin, or invalid credentials.<br/><br/>

            Raises:<br/>
                JSON response with error message if a SQLAlchemyError occurs.<br/><br/>

            Error message:<br/>
                'Only PG users allowed' if the user belongs to Crypto and FIAT Section.<br/>
                'Your account is not active. Please contact the administrator': If the user account is not approved by Admin.<br/>
                'Invalid credentials': If the user's email or password is incorrect.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Users).where(Users.email == user.email))
                first_user = existing_user.scalars().first()
                
                # Password validation
                if first_user and check_password(user.password,first_user.password):

                    if not first_user.is_merchent:
                        return json({'message': 'Only PG users allowed'}, 400)

                    # Check kyc is exist for the user
                    merchnat_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == first_user.id
                    ))
                    merchnat_kyc_ = merchnat_kyc_obj.scalar()

                    # If kyc not submitted
                    if not first_user.is_kyc_submitted and not first_user.is_admin and not merchnat_kyc_:
                        return json({
                            'message': 'Kyc not submitted',  
                            'first_name':  first_user.first_name,
                            'last_name': first_user.lastname,
                            'contact_number': first_user.phoneno,
                            'email': first_user.email,
                            'user_id': first_user.id                
                            }, 400)

                    # For active users
                    if first_user.is_active:
                        current_time = datetime.now()
                        login_count  = first_user.login_count
                       
                        if login_count == None:
                            login_count = 0
                            
                        try:
                            first_user.lastlogin = current_time

                            if login_count == 0:
                                count = login_count + 1
                                first_user.login_count = count

                            elif login_count > 0:
                                count = login_count + 1
                                first_user.login_count = count

                            await session.commit()
                            await session.refresh(first_user)
                            
                        except Exception as e:
                            return json({'msg': 'Login time error', 'error': f'{str(e)}'}, 400)
                        
                        response = json({
                            'is_merchant': first_user.is_merchent,
                            'user_name': first_user.full_name,
                            'access_token': generate_access_token(first_user.id),
                            'refresh_token': generate_refresh_token(first_user.id)
                        },200)

                        return response
                    
                    else:
                        return json({'msg': 'Your account is not active. Please contact the administrator'}, 400)
                    
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)




