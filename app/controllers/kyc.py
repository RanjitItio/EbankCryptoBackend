from blacksheep.server.controllers import APIController
from Models.schemas import Kycschema
from sqlmodel import select, update
from database.db import async_engine, AsyncSession
from Models.models import Users,Kycdetails, Group
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from Models.schemas import UpdateKycSchema, AllKycByAdminSchema
from blacksheep.server.authorization import auth
from app.controllers.controllers import get, post, put, delete
from blacksheep.server.authorization import auth
import uuid
from decouple import config





#View all the available applied KYC
class UserKYCController(APIController):

    SERVER_MODE     = config('IS_DEVELOPMENT')
    DEVELOPMENT_URL = config('DEVELOPMENT_URL_MEDIA')
    PRODUCTION_URL  = config('PRODUCTION_URL_MEDIA')


    if SERVER_MODE == 'True':
        media_url = DEVELOPMENT_URL
    else:
        media_url = PRODUCTION_URL

    @classmethod
    def route(cls):
        return '/api/v1/user/kyc'

    @classmethod
    def class_name(cls):
        return "Users KYC"
    

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
    
    
    #Get all applied KYC
    @auth('userauth')
    @get()
    async def get_kyc(self, request: Request, limit: int = 50, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:

                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                limit  = limit
                offset = offset
                
                # print(self.media_url)
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
                        'status': 'Active' if user_data.is_active else 'Inactive',
                        'document': f'{self.media_url}/{kyc_details.uploaddocument}'
                        }

                    combined_data.append({
                        'user_kyc_details': kyc_details,
                        'user': user_data
                        })

                return json({'all_Kyc': combined_data}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'}, 500)


    @post()
    async def create_kyc(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:

                request_body        = await request.form()

                user_email          =  request_body['email']
                user_mobile_no      =  request_body['phoneno']
                user_firstname      =  request_body['firstname']
                user_lastname       =  request_body['lastname']
                user_id             =  request_body['user_id']
                user_dob            =  request_body['dateofbirth']
                user_gender         =  request_body['gender']
                user_marital_status =  request_body['marital_status']
                user_address        =  request_body['address']
                user_landmark       =  request_body['landmark']
                user_city           =  request_body['city']
                user_zipcode        =  request_body['zipcode']
                user_state          =  request_body['state']
                user_country        =  request_body['country']
                user_nationality    =  request_body['nationality']
                user_id_type        =  request_body['id_type']
                user_id_number      =  request_body['id_number']
                user_id_expiry_date =  request_body['id_expiry_date']

                try:
                    user             = await session.get(Users,int(user_id))
                    is_kyc_submitted = await session.get(Kycdetails, int(user_id))
                except Exception as e:
                    return json({'msg': 'unable to get user'}, 400)
                
                if user is None:
                    return json({'msg': 'User not found'}, 404)
                
                try:
                    files = await request.files()
                    
                    if not files:
                        return json({'msg': 'Please upload document'}, 400)

                    user_image_path = await self.save_user_document(request)
                except Exception as e:
                    return json({'msg': f'Image upload error {str(e)}'}, 400)
                
                if is_kyc_submitted is None:
                    # user.kyc_data = kyc_data
                    try:
                        kyca =  Kycdetails(
                            firstname      = user_firstname,
                            user_id        = int(user_id),
                            lastname       = user_lastname,
                            dateofbirth    = datetime.strptime(user_dob, "%Y-%m-%d").date(),
                            gander         = user_gender,
                            marital_status = user_marital_status,
                            email          = user_email,
                            phoneno        = user_mobile_no,
                            address        = user_address,
                            landmark       = user_landmark,
                            zipcode        = user_zipcode,
                            city           = user_city,
                            state          = user_state,
                            country        = user_country,
                            nationality    = user_nationality,
                            id_type        = user_id_type,
                            id_number      = user_id_number,
                            id_expiry_date = datetime.strptime(user_id_expiry_date, "%Y-%m-%d").date(),
                            uploaddocument = user_image_path if user_image_path else '' 
                        )
                    
                        session.add(kyca)              
                        await session.commit() 

                    except Exception as e:
                        return json({'error': f'{str(e)}'}, 500)
                                     
                    return json({"msg": "KYC data submitted successfully"}, 200)
                else:
                    return json({"msg": "KYC data already submitted"}, 404)
                
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)
        
    @auth('userauth')
    @put()
    async def update_kyc(self, request: Request, update_kyc: UpdateKycSchema):

        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # check the user is Admin or not
                try:
                    user_object      = select(Users).where(Users.id == user_id)
                    save_to_db       = await session.execute(user_object)

                    user_object_data = save_to_db.scalar()

                    if user_object_data.is_admin == False:
                        return json({'msg': 'Only Admin can update the Kyc'})
                    
                except Exception as e:
                    return json({'msg': f'{str(e)}'})
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