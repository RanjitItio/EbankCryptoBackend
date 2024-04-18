from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import AdminCreateSchema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users, Admin
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import encrypt_password


class AdminController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/admin/register'

    @classmethod
    def class_name(cls):
        return "Admin register"

    @get()
    async def get_user(self, email: str):
        try:
            async with AsyncSession(async_engine) as session:
                statement = select(Admin).where(Admin.email == email)
                results = await session.execute(statement)
                users = [user.to_dict() for user in results.scalars()]
                return json({'users': users})

        except SQLAlchemyError as e:
            return json({"Error": str(e)})

    @post()
    async def add_user(self, user: AdminCreateSchema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                existing_user = await session.execute(select(Admin).where(Admin.email == user.email))
                existing_user = existing_user.scalars().first()
                if existing_user:
                    return json({'msg': f"{existing_user.email} already exists"}, 400)
                
                user_instance = Admin(
                    first_name=user.firstname,
                    lastname=user.lastname,
                    email=user.email,
                    password=encrypt_password(user.password)
                )
                
                session.add(user_instance)
                await session.commit()
                await session.refresh(user_instance)
                return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)

        except SQLAlchemyError as e:
            return json({"Error": str(e)})

    @put()
    async def update_user(self):
        return {'msg': 'update user'}

    @delete()
    async def delete_user(self):
        return {'msg': 'Delete user'}
