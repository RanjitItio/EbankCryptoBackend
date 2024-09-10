from blacksheep.server.controllers import APIController
from blacksheep.exceptions import BadRequest
from blacksheep import Request, json, put as PUT
from blacksheep.server.authorization import auth
from blacksheep.server.authorization import auth
from database.db import async_engine, AsyncSession
from Models.models import Users,Kycdetails, Group
from Models.schemas import UpdateKycSchema
from app.controllers.controllers import get, post, put, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select, desc, func
from decouple import config
from datetime import datetime
from pathlib import Path
import uuid




#View all the available applied KYC of merchants
class MerchantKYCController(APIController):

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
        return "Merchant KYC"
    

    # Save user uploaded document
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
    
    
    #Get all applied KYC by Admin
    @auth('userauth')
    @get()
    async def get_Merchantkyc(self, request: Request, limit: int = 20, offset: int = 0):
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
                #Authentication end here

                # Count all available rows
                count_stmt = select(func.count(Users.id)).where(Users.is_merchent == True)
                execute_statement = await session.execute(count_stmt)
                total_available_user_row_obj = execute_statement.scalar()

                total_user_row_count = total_available_user_row_obj / limit

                user_data = []
                kyc_data  = []

                # Users Data
                all_merchant_user_obj = await session.execute(select(Users).where(
                    Users.is_merchent == True
                ).order_by(
                    desc(Users.id)).limit(limit).offset(offset)
                )
                all_merchant_user_ = all_merchant_user_obj.scalars().all()

                if not all_merchant_user_:
                    return json({
                        'message': 'No user available'
                    }, 404)


                # All users kyc
                for merchant_user in all_merchant_user_:

                    group_query = select(Group).where(Group.id == merchant_user.group)
                    group_result = await session.execute(group_query)
                    group_data = group_result.scalar()

                    group_name = group_data.name if group_data else None

                    user_data.append({
                        "user_id": merchant_user.id,
                        "firstname": merchant_user.first_name,
                        "lastname": merchant_user.lastname,
                        "email": merchant_user.email,
                        "phoneno": merchant_user.phoneno,
                        'ip_address': merchant_user.ipaddress, 
                        'lastlogin': merchant_user.lastlogin, 
                        'merchant': merchant_user.is_merchent, 
                        'admin': merchant_user.is_admin,
                        'active': merchant_user.is_active,
                        'verified': merchant_user.is_verified,
                        'group': merchant_user.group,
                        'group_name': group_name,
                        'status': 'Active' if merchant_user.is_active else 'Inactive',
                        'document': f'{self.media_url}/{merchant_user.picture}'
                    })

                    merchant_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == merchant_user.id
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
        

    # Apply new kyc
    @post()
    async def create_kyc(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:

                request_body        = await request.form()

                # Get the data from payload
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

                # Get the user ID
                user_obj = await session.execute(select(Users).where(
                    Users.id == int(user_id)
                ))
                user_detail = user_obj.scalar()

                # Invalid user id
                if user_detail is None:
                    return json({'message': 'User not found'}, 404)
                

                # Get the user kyc
                is_kyc_submitted_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == int(user_id)
                ))
                is_kyc_submitted = is_kyc_submitted_obj.scalar()
                

                # If the users kyc is already exists
                if is_kyc_submitted:
                    return json({'message': 'Kyc already applied'}, 403)
                
                
                # Upload the document
                try:
                    files = await request.files()
                    
                    if not files:
                        return json({'msg': 'Please upload document'}, 400)

                    user_image_path = await self.save_user_document(request)
                except Exception as e:
                    return json({'msg': f'Image upload error {str(e)}'}, 400)
                

                if is_kyc_submitted is None:
                    # Create new KYC data
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
                            uploaddocument = user_image_path if user_image_path else '', 
                        )

                        # User kyc submitted
                        user_detail.is_kyc_submitted = True
                    
                        session.add(kyca) 
                        session.add(user_detail)             
                        await session.commit() 
                        await session.refresh(kyca)
                        await session.refresh(user_detail)

                    except Exception as e:
                        return json({'error': f'{str(e)}'}, 500)
                                     
                    return json({"msg": "KYC data submitted successfully"}, 200)
                else:
                    return json({"msg": "KYC data already submitted"}, 404)
                
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)
        

        
    # Update Kyc data by Admin
    @auth('userauth')
    @put()
    async def update_kyc(self, request: Request, update_kyc: UpdateKycSchema):

        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Admin authentication ends here
                try:
                    user_object      = select(Users).where(Users.id == user_id)
                    save_to_db       = await session.execute(user_object)

                    user_object_data = save_to_db.scalar()

                    if user_object_data.is_admin == False:
                        return json({'msg': 'Only Admin can update the Kyc'}, 400)
                    
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
                                return json({'msg': 'Error while updating KYC details'}, 400)
                            
                            try:
                                get_user_obj_data.is_active = True
                                get_user_obj_data.is_verified = True

                                session.add(get_user_obj_data)
                                await session.commit()
                                await session.refresh(get_user_obj_data)

                            except Exception as e:
                                return json({'msg': 'Error while updating the user'}, 400)


                            return json({'msg': 'Updated successfully'}, 200)
                        
                        else:
                            return json({'msg': 'Kyc not found'}, 404)

                    except Exception as e:
                        return json({'msg': f'{str(e)}'}, 400)

                else:
                    try:
                        if kyc_detail:
                            try:
                                kyc_detail.status = 'Rejected'
                                session.add(kyc_detail)
                                await session.commit()
                                await session.refresh(kyc_detail)
                            except Exception:
                                return json({'msg': 'Error while updating KYC details'}, 400)

                            try:
                                get_user_obj_data.is_active = False
                                get_user_obj_data.is_verified = False

                                session.add(get_user_obj_data)
                                await session.commit()
                                await session.refresh(get_user_obj_data)

                            except Exception as e:
                                return json({'msg': 'Error while updating the user'}, 400)
                            
                            return json({'msg': 'Updated successfully'}, 200)
                        
                        else:
                            return json({'msg': 'Kyc not found'})

                    except Exception as e:
                        return json({'msg': f'{str(e)}'}, 500)

        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'}, 500)
        



#View all the available applied KYC of merchants
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
        return '/api/v2/kyc/user/'

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
    async def get_UserKyc(self, request: Request, limit: int = 50, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                limit  = limit
                offset = offset
               
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

                # Get the users(Non Merchant)
                users_data_obj = await session.execute(select(Users).where(
                    Users.is_merchent == False
                ).order_by(
                    desc(Users.id)
                ))
                users_data = users_data_obj.scalars().all()
                
                user_dict = {user.id: user for user in users_data}

                kyc_data = []

                for user in users_data:
                    # Get the KYC related to the users
                    kyc_query  = select(Kycdetails).where(Kycdetails.user_id == user.id)
                    kyc_result = await session.execute(kyc_query)
                    kyc_detail = kyc_result.scalar()

                    if kyc_detail:
                        kyc_data.append(kyc_detail)

                    combined_data = []

                    # Append the data in combined_data
                    for kyc_detail in kyc_data:
                        user_id = kyc_detail.user_id
                        user_data = user_dict.get(user_id)

                        if user_data:
                            group_query = select(Group).where(Group.id == user_data.group)
                            group_result = await session.execute(group_query)
                            group_data = group_result.scalar()

                            group_name = group_data.name if group_data else None

                            user_info = {
                                'ip_address': user_data.ipaddress,
                                'lastlogin': user_data.lastlogin,
                                'merchant': user_data.is_merchent,
                                'admin': user_data.is_admin,
                                'active': user_data.is_active,
                                'verified': user_data.is_verified,
                                'group': user_data.group,
                                'group_name': group_name,
                                'status': 'Active' if user_data.is_active else 'Inactive',
                                'document': f'{self.media_url}/{kyc_detail.uploaddocument}'
                            }

                            combined_data.append({
                                'user_kyc_details': kyc_detail,
                                'user': user_info
                                })

                return json({'allKyc': combined_data}, 200)
            
        except Exception as e:
            return json({'msg': 'Server error','error': f'{str(e)}'}, 500)

  
    
