from blacksheep import Request, json
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from app.controllers.controllers import post
from app.auth import encrypt_password
from Models.Merchant.schema import ChangePasswordSchema
from Models.models import Users
from sqlmodel import select




# Change users password
class UserChangePasswordController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/change_password'
    
    @classmethod
    def class_name(cls):
        return "Users change password"
    

    @auth('userauth')
    @post()
    async def change_password(self, request: Request, schema: ChangePasswordSchema):
        """
            Change users password, Authenticated Route.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing user identity and payload data.<br/>
                - schema(ChangePasswordSchema): The `schema` parameter in the `change_password` function represents the data schema for changing password.<br/><br/>

            Returns:<br/>
                - JSON response with success status, message if successful.<br/>
                - JSON response with error status and message if an exception occurs.<br/><br/>

            Raises:<br/>
                - JSON response with error status and message if an exception occurs.<br/>
                - JSON response with error status and message if password did not match.<br/><br/>
            
            Error message:<br/>
            - 'Password did not match': If the password did not match.<br/>
            - 'User not found': If the user does not.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Get the payload data
                password1    = schema.password1
                password2    = schema.password2
                
                if password1 != password2:
                    return json({'msg': 'Password did not match'}, 403)
                
                # get the user
                user       = await session.execute(select(Users).where(Users.id == user_id))
                user_obj   = user.scalar()
                
                if user_obj:
                    # Change password
                    encrypted_password = encrypt_password(password1)
                    user_obj.password  = encrypted_password

                    session.add(user_obj)
                    await session.commit()
                    await session.refresh(user_obj)

                    return json({
                        'message': 'Password Changed Successfully'
                    }, 200)
                
                else:
                    return json({'message': 'User not found'}, 400)
                
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)