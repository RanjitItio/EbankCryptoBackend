from blacksheep.server.controllers import  APIController
from Models.schemas import AdminCreateSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users, Admin
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import encrypt_password
from app.controllers.controllers import get, post




class AdminController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/admin/register'

    @classmethod
    def class_name(cls):
        return "Admin register"

    # @get()
    # async def get_user(self, email: str):
    #     try:
    #         async with AsyncSession(async_engine) as session:
    #             statement = select(Users).where(Users.email == email)
    #             results = await session.execute(statement)
    #             # users = [user.to_dict() for user in results.scalars()]
    #             return json({'users': results})

    #     except SQLAlchemyError as e:
    #         return json({"Error": str(e)})


    @post()
    async def add_adminuser(self, admin: AdminCreateSchema, request: Request):

        try:
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Users).where(Users.email == admin.email))
                existing_user = existing_user.scalars().first()

                password         = admin.password
                confirm_password = admin.confirm_password

                if existing_user:
                    return json({'msg': f"{existing_user.email} already exists"}, 400)
                
                if password != confirm_password:
                    return json({'msg': "Password did not match"}, 400)
                            
                user_instance = Users(
                    first_name    = admin.firstname,
                    lastname      = admin.lastname,
                    email         = admin.email,
                    password      = encrypt_password(admin.password),
                    is_verified   = True,
                    is_active     = True,
                    is_admin      = True,
                    phoneno       = admin.phone_no
                )
                
                session.add(user_instance)
                await session.commit()
                await session.refresh(user_instance)

                return json({'msg': f'Admin user created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)

        except SQLAlchemyError as e:
            return json({"Error": str(e)})


    # @put()
    # async def update_user(self):
    #     return {'msg': 'update user'}


    # @delete()
    # async def delete_user(self):
    #     return {'msg': 'Delete user'}




# async def create_adminuser(self):

#         try:
#             async with AsyncSession(async_engine) as session:
#                 email = input('Enter your email address: ')
#                 first_name = input("Enter your First name: ")
#                 last_name = input("Enter your Last name: ")
#                 password  = input("Enter Password: ")
#                 Confirm_password  = input("Enter Confirm Password: ")

#                 existing_user = await session.execute(select(Users).where(Users.email == email))
#                 existing_user = existing_user.scalars().first()

#                 if existing_user:
#                     print(existing_user.email, 'Already exists')
#                     # return json({'msg': f"{existing_user.email} already exists"}, 400)
#                 if password != Confirm_password:
#                     print("Password did not match")
                
#                 user_instance = Users(
#                     first_name=first_name,
#                     lastname=last_name,
#                     email=email,
#                     password=encrypt_password(password),
#                     is_verified = True,
#                     is_active   = True,
#                     is_admin    = True
#                 )
                
#                 session.add(user_instance)
#                 await session.commit()
#                 await session.refresh(user_instance)

#                 print("User created successfully")
#                 # return json({'msg': f'Admin user created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)

#         except SQLAlchemyError as e:
#             print('Error')
            # return json({"Error": str(e)})()
