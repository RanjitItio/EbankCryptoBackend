from blacksheep.server.controllers import get, post, put, delete, APIController
from Models.schemas import AdminCreateSchema
from sqlmodel import Session, select
from database.db import engine
from Models.models import Users,Admin
from blacksheep import Request
from blacksheep import  json
from sqlalchemy.exc import SQLAlchemyError





class AdminController(APIController):

    @classmethod
    def route(cls):
        return 'api/v1/admin/'
    
    @classmethod
    def class_name(cls):
        return "Admin register"
    
    @get()
    async def get_user(email: str):
        with Session(engine) as session:
            users = []
            get_email = email
            statement = select(Admin).where(Admin.email == get_email)
            results = session.exec(statement)
            for op in results:
                users.append(op)

            return json({'users': users})

    @post()
    async def add_user(self, user: AdminCreateSchema, request: Request):
        try:
            with Session(engine) as session:
                existing_user = session.exec(select(Admin).where(Admin.email == user.email)).first()
                if existing_user:
                    if existing_user.email:
                        return json({'msg':f"{existing_user.email} already exists"}, 400)
                    
                else:
                    user_instance = Admin(first_name=user.firstname,lastname=user.lastname, email=user.email, password=user.password)
                    session.add(user_instance)
                    session.commit()
                    session.refresh(user_instance)
                    return json({'msg': f'User created successfully {user_instance.first_name} {user_instance.lastname}'}, 201)
        except SQLAlchemyError as e:
            return json({"Error": str(e)})
 

    @put()
    async def update_user():
        return {'msg': 'update user'}
    

    @delete()
    async def delete_user():
        return {'msg': 'Delete user'}
    
