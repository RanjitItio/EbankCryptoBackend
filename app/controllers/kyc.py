from blacksheep.server.controllers import APIController
from Models.schemas import Kycschema
from sqlmodel import select, update
from database.db import async_engine, AsyncSession
from Models.models import Users,Kycdetails, Group
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
from Models.schemas import UpdateKycSchema, AllKycByAdminSchema
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post, put, delete
from blacksheep.server.authorization import auth
from blacksheep import FromQuery




#View all the available applied KYC
class UserKYCController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/kyc'

    @classmethod
    def class_name(cls):
        return "Users KYC"
    
    @auth('userauth')
    @get()
    async def get_kyc(self, request: Request, limit: int = 25, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:

                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                limit  = limit
                offset = offset

                # check the user is Admin or not
                try:
                    user_object      = select(Users).where(Users.id == user_id)
                    save_to_db       = await session.execute(user_object)
                    user_object_data = save_to_db.scalar()

                    if user_object_data.is_admin == False:
                        return json({'msg': 'Only admin can view all the KYC'}, 400)
                    
                except Exception as e:
                    return json({'msg': 'Unable to get Admin detail','error': f'{str(e)}'}, 400)
                #Authentication end here

                try:
                    kyc_details = await session.execute(select(Kycdetails).order_by(Kycdetails.id.desc()).limit(limit).offset(offset))
                    all_kyc     = kyc_details.scalars().all()
                except Exception as e:
                    return json({'msg': 'Unknown Error occure during kyc process','error': f'{str(e)}'}, 400)
                
                try:
                    user_obj      = await session.execute(select(Users))
                    user_obj_data = user_obj.scalars().all()

                    if not user_obj_data:
                        return json({'msg': 'User not available'}, 404)
                    
                except Exception as e:
                    return json({'msg': 'User not found'}, 400)
                
                if not all_kyc:
                    return json({'msg': 'No Kyc available'}, 404)
                
                user_dict = {user.id: user for user in user_obj_data}

                combined_data = []

                for kyc_details in all_kyc:

                    user_id   = kyc_details.user_id
                    user_data = user_dict.get(user_id)

                    group_obj      = await session.execute(select(Group).where(Group.id == user_data.group))
                    group_obj_data = group_obj.scalar()
                    group_name     = group_obj_data.name if group_obj_data else None

                    user_data = {
                        'ip_address': user_data.ipaddress, 
                        'lastlogin': user_data.lastlogin, 
                        'merchant': user_data.is_merchent, 
                        'admin': user_data.is_admin,
                        'active': user_data.is_active,
                        'verified': user_data.is_verified,
                        'group': user_data.group,
                        'group_name': group_name,
                        'status': 'Active' if user_data.is_active else 'Inactive'
                        }

                    combined_data.append({
                        'user_kyc_details': kyc_details,
                        'user': user_data
                        })

                return json({'all_Kyc': combined_data}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'}, 500)


    @post()
    async def create_kyc(self, kyc_data: Kycschema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # user_id = await decode_token(request.headers.get("Authorization"))
                try:
                    user             = await session.get(Users,kyc_data.user_id)
                    is_kyc_submitted = await session.get(Kycdetails, kyc_data.user_id)
                except Exception as e:
                    return json({'msg': 'unable to get user'})
                
                if user is None:
                    return json({'msg': 'User not found'}, 404)
                
                if is_kyc_submitted is None:
                    # user.kyc_data = kyc_data
                    try:
                        kyca =  Kycdetails(
                            firstname      = kyc_data.firstname,
                            user_id        = kyc_data.user_id,
                            lastname       = kyc_data.lastname,
                            dateofbirth    = kyc_data.dateofbirth,
                            gander         = kyc_data.gender,
                            marital_status = kyc_data.marital_status,
                            email          = kyc_data.email,
                            phoneno        = kyc_data.phoneno,
                            address        = kyc_data.address,
                            landmark       = kyc_data.landmark,
                            zipcode        = kyc_data.zipcode,
                            city           = kyc_data.city,
                            state          = kyc_data.state,
                            country        = kyc_data.country,
                            nationality    = kyc_data.nationality,
                            id_type        = kyc_data.id_type,
                            id_number      = kyc_data.id_number,
                            id_expiry_date = kyc_data.id_expiry_date,
                            uploaddocument = kyc_data.uploaddocument
                        )
                    
                        session.add(kyca)              
                        await session.commit() 

                    except Exception as e:
                        return json({'error': f'{str(e)}'})
                                     
                    return json({"msg": "KYC data submitted successfully"}, 200)
                else:
                    return json({"msg": "KYC data already submitted"}, 404)
                
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)
        
    
    @put()
    async def update_kyc(self, request: Request, update_kyc: UpdateKycSchema):

        try:
            async with AsyncSession(async_engine) as session:

                # Authenticate user
                try:
                    header_value = request.get_first_header(b"Authorization")

                    if not header_value:
                        return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
                    header_value_str = header_value.decode("utf-8")

                    parts = header_value_str.split()

                    if len(parts) == 2 and parts[0] == "Bearer":
                        token = parts[1]
                        user_data = decode_token(token)

                        if user_data == 'Token has expired':
                            return json({'msg': 'Token has expired'}, 400)
                        elif user_data == 'Invalid token':
                            return json({'msg': 'Invalid token'}, 400)
                        else:
                            user_data = user_data
                            
                        user_id = user_data["user_id"]

                        # check the user is Admin or not
                        try:
                            user_object      = select(Users).where(Users.id == user_id)
                            save_to_db       = await session.execute(user_object)
                            user_object_data = save_to_db.scalar()

                            if user_object_data.is_admin == False:
                                return json({'msg': 'Only Admin can update the Kyc'})
                            
                        except Exception as e:
                            return json({'msg': f'{str(e)}'})
                        
                except Exception as e:
                   return json({'msg': 'Authentication Failed'}, 400)

                #Authentication ends here

                try:
                    stmt       = select(Kycdetails).where(Kycdetails.id == update_kyc.kyc_id)
                    result     = await session.execute(stmt)
                    kyc_detail = result.scalar()
                except Exception as e:
                    return json({'msg': 'Unable to locate kyc'}, 400)

                try:
                    user_id = kyc_detail.user_id

                    get_user          = select(Users).where(Users.id == user_id)
                    get_user_obj      = await session.execute(get_user)
                    get_user_obj_data = get_user_obj.scalar()
                    
                    if not get_user_obj_data:
                        return json({'msg': 'User not found'}, 400)
                    
                except Exception as e:
                    return json({'msg': 'Error while fetching user detail','error': f'{str(e)}'}, 400)
                

                if update_kyc.status == "Pending":
                    try:
                        if kyc_detail:
                            try:
                                kyc_detail.status = 'Pending'
                                
                                session.add(kyc_detail)
                                await session.commit()
                                await session.refresh(kyc_detail)
                            except Exception:
                                return json({'msg': 'Error while updating KYC details'}, 400)

                            return json({'msg': 'Updated successfully'}, 400)
                        
                        else:
                            return json({'msg': 'Kyc not found'}, 400)

                    except Exception as e:
                        return json({'msg': f'{str(e)}'})
                    
                # If the Status is Approved
                elif update_kyc.status == "Approved":
                    try:
                        if kyc_detail:
                            try:
                                kyc_detail.status = 'Approved'
                                session.add(kyc_detail)
                                await session.commit()
                                await session.refresh(kyc_detail)

                            except Exception:
                                return json({'msg': 'Error while updating KYC details'})
                            
                            try:
                                get_user_obj_data.is_active = True
                                get_user_obj_data.is_verified = True

                                session.add(get_user_obj_data)
                                await session.commit()
                                await session.refresh(get_user_obj_data)

                            except Exception as e:
                                return json({'msg': 'Error while updating the user'})


                            return json({'msg': 'Updated successfully'})
                        
                        else:
                            return json({'msg': 'Kyc not found'})

                    except Exception as e:
                        return json({'msg': f'{str(e)}'})

                else:
                    try:
                        if kyc_detail:
                            try:
                                kyc_detail.status = 'Rejected'
                                session.add(kyc_detail)
                                await session.commit()
                                await session.refresh(kyc_detail)
                            except Exception:
                                return json({'msg': 'Error while updating KYC details'})

                            try:
                                get_user_obj_data.is_active = False
                                get_user_obj_data.is_verified = False

                                session.add(get_user_obj_data)
                                await session.commit()
                                await session.refresh(get_user_obj_data)

                            except Exception as e:
                                return json({'msg': 'Error while updating the user'})
                            
                            return json({'msg': 'Updated successfully'})
                        
                        else:
                            return json({'msg': 'Kyc not found'})

                    except Exception as e:
                        return json({'msg': f'{str(e)}'})

        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'})
        




from blacksheep import FromFiles, FromBytes, FileInput
from pathlib import Path
from blacksheep.exceptions import BadRequest
from datetime import datetime

# from blacksheep.messages import 

class UserKYCController(APIController):

    @classmethod
    def route(cls):
        return '/file-upload'

    @classmethod
    def class_name(cls):
        return "File Upload test"
    
    # @auth('userauth')
    @post()
    async def post_fileupload(self, request: Request, files: FromFiles):
            try:
                async with AsyncSession(async_engine) as session:
                    # image_part = await request.form()
                    # image = image_part['image']

                    # # if image_part is None:
                    # #     raise ValueError("No file with the name 'image' was uploaded.")

                    # # file_name = image_part

                    # print(image)
                    current_time = datetime.now()
                    formattedtime = current_time.strftime("%H:%M %p")
                    ip = request.original_client_ip
                    
                    user_identity = request.identity
                    user_id = user_identity.claims.get("user_id") if user_identity else None

                    return json({'msg': formattedtime, 'ip': ip, 'user_id': user_id})
                
            except Exception as e:
                return json({'error': f'{str(e)}'})