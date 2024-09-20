from blacksheep import json, Request
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep.exceptions import BadRequest
from app.controllers.controllers import get
from database.db import AsyncSession, async_engine
from Models.models import Users, Kycdetails, Group
from sqlmodel import select, desc, func, and_
from decouple import config
from datetime import datetime
from pathlib import Path
import uuid
from typing import List



SERVER_MODE = config('IS_DEVELOPMENT')
DEVELOPMENT_URL = config('DEVELOPMENT_URL_MEDIA')
PRODUCTION_URL  = config('PRODUCTION_URL_MEDIA')


if SERVER_MODE == 'True':
    media_url = DEVELOPMENT_URL
else:
    media_url = PRODUCTION_URL



# View all the available applied KYC of merchants
class CryptoUserKYCController(APIController):

    SERVER_MODE     = config('IS_DEVELOPMENT')
    DEVELOPMENT_URL = config('DEVELOPMENT_URL_MEDIA')
    PRODUCTION_URL  = config('PRODUCTION_URL_MEDIA')


    if SERVER_MODE == 'True':
        media_url = DEVELOPMENT_URL
    else:
        media_url = PRODUCTION_URL


    @classmethod
    def route(cls):
        return '/api/v2/crypto/user/kyc/'


    @classmethod
    def class_name(cls):
        return "User's KYC"
    

    # Save user document
    async def save_user_document(self, request: Request):
        file_data = await request.files()
    
        for part in file_data:
            file_bytes = part.data
            original_file_name  = part.file_name.decode()

        file_extension = original_file_name.split('.')[-1]

        file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}.{file_extension}"

        if not file_name:
            return BadRequest("File name is missing")

        file_path = Path("Static/User") / file_name

        try:
            with open(file_path, mode="wb") as user_files:
                user_files.write(file_bytes)

        except Exception:
            file_path.unlink()
            raise
        
        return str(file_path.relative_to(Path("Static")))
    
    
    #Get all applied KYC of user(Non Merchant)
    @auth('userauth')
    @get()
    async def get_UserKyc(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None
                
                # Admin Authnetication
                try:
                    user_object      = select(Users).where(Users.id == user_id)
                    save_to_db       = await session.execute(user_object)
                    user_object_data = save_to_db.scalar()

                    if user_object_data.is_admin == False:
                        return json({'msg': 'Only admin can view all the KYC'}, 400)
                    
                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail','error': f'{str(e)}'}, 400)
                #Authentication ends

                count_stmt = select(func.count(Users.id)).where(Users.is_merchent == True)
                execute_statement = await session.execute(count_stmt)
                total_available_user_row_obj = execute_statement.scalar()

                total_user_row_count = total_available_user_row_obj / limit

                user_data = []
                kyc_data  = []

                # Get all Users Data
                all_user_obj = await session.execute(select(Users).where(
                    Users.is_merchent == False
                ).order_by(
                    desc(Users.id)).limit(limit).offset(offset)
                )
                all_user_ = all_user_obj.scalars().all()

                if not all_user_:
                    return json({
                        'message': 'No user available'
                    }, 404)
                

                # All users kyc
                for user in all_user_:

                    group_query = select(Group).where(Group.id == user.group)
                    group_result = await session.execute(group_query)
                    group_data = group_result.scalar()

                    group_name = group_data.name if group_data else None

                    user_data.append({
                        "user_id": user.id,
                        "firstname": user.first_name,
                        "lastname": user.lastname,
                        "email": user.email,
                        "phoneno": user.phoneno,
                        'ip_address': user.ipaddress, 
                        'lastlogin': user.lastlogin, 
                        'merchant': user.is_merchent, 
                        'admin': user.is_admin,
                        'active': user.is_active,
                        'verified': user.is_verified,
                        'group': user.group,
                        'group_name': group_name,
                        'status': 'Active' if user.is_active else 'Inactive',
                        'document': f'{self.media_url}/{user.picture}'
                    })

                    user_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == user.id
                    ))
                    user_kyc_ = user_kyc_obj.scalars().all()

                    if user_kyc_:
                        for kyc in user_kyc_:
                            
                            kyc_data.append({
                                "gander": kyc.gander,
                                "state":  kyc.state,
                                "status": kyc.status,
                                "marital_status": kyc.marital_status,
                                "country": kyc.country,
                                "email": kyc.email,
                                "nationality": kyc.nationality,
                                "user_id": kyc.user_id,
                                "firstname": kyc.firstname,
                                "phoneno": kyc.phoneno,
                                "id_type": kyc.id_type,
                                "address": kyc.address,
                                "id_number": kyc.id_number,
                                "id_expiry_date": kyc.id_expiry_date,
                                "id": kyc.id,
                                "landmark": kyc.landmark,
                                "lastname": kyc.lastname,
                                "city": kyc.city,
                                "uploaddocument": f'{self.media_url}/{kyc.uploaddocument}',
                                "dateofbirth": kyc.dateofbirth,
                                "zipcode": kyc.zipcode
                            })

                return json({
                    'all_Kyc': kyc_data if kyc_data else [],
                    'all_users': user_data if user_data else [],
                    'total_row_count': total_user_row_count
                    }, 200)
            
        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'}, 500)
        


# Search users
class SearchCryptoUserController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/crypto/admin/user/search/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Search Crypto User Controller'
    
    @auth('userauth')
    @get()
    async def seacrh_crypto_user(request: Request, query: str = ''):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity    = request.identity
                adminID          = user_identity.claims.get("user_id") if user_identity else None

                # Admin authentication
                user_obj = await session.execute(select(Users).where(Users.id == adminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Admin authorization failed'}, 400)
                # Authentication Ends here

                data = query

                group_query = None
                if query.lower() ==  'merchant regular':
                    group_query_obj = await session.execute(select(Group).where(Group.name == 'Merchant Regular'))
                    group_query     = group_query_obj.scalar()

                if data.lower() == 'active':
                    searched_user_obj = await session.execute(select(Users).where(
                        and_(
                            Users.is_active == True,
                            Users.is_merchent == False)
                        ))
                

                elif data.lower() == 'inactive':
                    searched_user_obj = await session.execute(select(Users).where(
                                    and_(
                                        Users.is_active == False, 
                                        Users.is_verified    == False,
                                        Users.is_merchent    == False
                                    )))
                
                elif group_query:
                    searched_user_obj = await session.execute(select(Users).where(
                        and_(
                            Users.group == group_query.id,
                            Users.is_merchent    == False
                        )))
                    
                
                else:
                    try:
                        searched_user_obj = await session.execute(select(Users).where(
                            and_(
                            (Users.first_name.ilike(data)) |
                            (Users.lastname.ilike(data))   |
                            (Users.full_name.ilike(data))  |
                            (Users.email.ilike(data))      |
                            (Users.phoneno.ilike(data)),
                            Users.is_merchent == False
                            )
                        ))

                    except Exception as e:
                        return json({'msg': 'Search error', 'error': f'{str(e)}'}, 400)

                all_users: List[Users] = searched_user_obj.scalars().all()

                user_data = []
                kyc_data  = []

                for user in all_users:
                    group_query = select(Group).where(Group.id == user.group)
                    group_result = await session.execute(group_query)
                    group_data = group_result.scalar()

                    group_name = group_data.name if group_data else None

                    user_data.append({
                        "user_id": user.id,
                        "firstname": user.first_name,
                        "lastname": user.lastname,
                        "email": user.email,
                        "phoneno": user.phoneno,
                        'ip_address': user.ipaddress, 
                        'lastlogin': user.lastlogin, 
                        'merchant': user.is_merchent, 
                        'admin': user.is_admin,
                        'active': user.is_active,
                        'verified': user.is_verified,
                        'group': user.group,
                        'group_name': group_name,
                        'status': 'Active' if user.is_active else 'Inactive',
                        'document': f'{media_url}/{user.picture}'
                    })

                    merchant_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == user.id
                    ))
                    merchant_kyc_ = merchant_kyc_obj.scalars().all()

                    if merchant_kyc_:
                        for kyc in merchant_kyc_:
                            
                            kyc_data.append({
                                "gander": kyc.gander,
                                "state":  kyc.state,
                                "status": kyc.status,
                                "marital_status": kyc.marital_status,
                                "country": kyc.country,
                                "email": kyc.email,
                                "nationality": kyc.nationality,
                                "user_id": kyc.user_id,
                                "firstname": kyc.firstname,
                                "phoneno": kyc.phoneno,
                                "id_type": kyc.id_type,
                                "address": kyc.address,
                                "id_number": kyc.id_number,
                                "id_expiry_date": kyc.id_expiry_date,
                                "id": kyc.id,
                                "landmark": kyc.landmark,
                                "lastname": kyc.lastname,
                                "city": kyc.city,
                                "uploaddocument": f'{media_url}/{kyc.uploaddocument}',
                                "dateofbirth": kyc.dateofbirth,
                                "zipcode": kyc.zipcode
                            })

                return json({
                        'all_Kyc': kyc_data if kyc_data else [],
                        'all_users': user_data if user_data else [],
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



