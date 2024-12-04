from Models.models import Users, Group
from database.db import AsyncSession, async_engine
from sqlmodel import select
from app.auth import encrypt_password
import asyncio

async def main():
    await CreateAdminUser()


async def CreateAdminUser():
    try:
        async with AsyncSession(async_engine) as session:
            user_email = input("Enter Email address: ").strip()
            user_password = input("Enter Password: ").strip()
            first_name    = input("Enter your first name: ").strip()
            last_name     = input("Enter Last Name: ").strip()
            phone_number  = input("Enter your Mobile number: ").strip()

             # Validate email and password
            if not user_email:
                return print("Email required.")
            
            if not user_password:
                return print("Password required.")
            
            if not first_name:
                return print("First Name required.")
            
            if not last_name:
                return print("Last Name required.")
            
            if not phone_number:
                return print("Last Name required.")
            
            if not user_email or not user_password and first_name and last_name and phone_number:
                return print("Please fill all the fields")
            
            existing_user_obj = await session.execute(select(Users).where(
                Users.email == user_email
            ))
            existing_user = existing_user_obj.scalars().first()

            if existing_user:
                return print("Email already exists")
            
            existing_user_number_obj = await session.execute(select(Users).where(
                Users.phoneno == phone_number
            ))
            existing_user_number = existing_user_number_obj.scalars().first()

            if existing_user_number:
                return print("Mobile Number already exists")
            
            user_group     = await session.execute(select(Group).where(Group.name == 'Admin'))
            user_group_obj = user_group.scalars().first()

            if not user_group_obj:
                # Create a group
                new_group = Group(
                    name = 'Admin'
                )

                session.add(new_group)
                await session.commit()
                await session.refresh(new_group)

                user_group_id = new_group.id
            else:
                user_group_id = user_group_obj.id


            create_admin_user = Users(
                first_name  = first_name,
                lastname    = last_name,
                email       = user_email,
                phoneno     = phone_number,
                password    = encrypt_password(user_password),
                group       = user_group_id,
                is_active   = True,
                is_admin    = True,
                is_verified = True
            )

            session.add(create_admin_user)
            await session.commit()
            await session.refresh(create_admin_user)

            return print("Admin created successfully")
    
    except Exception as e:
        return f'ERROR: {str(e)}'


 
if __name__ == "__main__":
    asyncio.run(main())


    
