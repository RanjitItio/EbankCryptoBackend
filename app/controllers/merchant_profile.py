from blacksheep import Request, json, FromFiles
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from blacksheep.exceptions import BadRequest
from app.controllers.controllers import get, put, post
from app.req_stream import upload_merchant_profile_Image, delete_old_file
from database.db import AsyncSession, async_engine
from Models.Merchant.schema import UpdateMerchantProfileSchema
from Models.models import Users, Kycdetails
from sqlmodel import select
from datetime import datetime
from pathlib import Path
from .environment import media_url



# Merchant Profile Section
class MerchantProfileController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Profile'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/merchant/profile/'

    @auth('userauth')
    @get()
    async def get_merchantProfile(self, request: Request):
        """
            This API Endpoint retrieves and returns a merchant's profile information, including user details and KYC documents.<br/><br/>

            Parameters:<br/>
            - request: The HTTP Request object.<br/><br/>
            
            Returns:<br/>
            - JSON response with the following structure:<br/>
            - If the operation is successful:<br/>
            - 'success': True<br/>
            - 'message': 'Data fetched successfully'<br/>
            - 'merchant_profile': A dictionary containing the merchant profile information.<br/>
            - If the operation fails.<br/>
            - 'error': A string describing the error occurred.<br/><br/>
            
            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                # Execute database query
                stmt = select(
                    Users.id,
                    Users.email,
                    Users.phoneno,
                    Users.full_name,
                    Users.is_merchent,
                    Users.picture,

                    Kycdetails.state,
                    Kycdetails.country,
                    Kycdetails.address,
                    Kycdetails.city,
                    Kycdetails.landmark,
                    Kycdetails.zipcode,
                    Kycdetails.nationality,
                    Kycdetails.dateofbirth,
                    Kycdetails.gander,
                    Kycdetails.marital_status,
                    Kycdetails.id_type,
                    Kycdetails.id_number,
                    Kycdetails.id_expiry_date,
                    Kycdetails.status,
                    Kycdetails.uploaddocument
                ).join(
                    Kycdetails, Kycdetails.user_id == Users.id
                ).where(
                    Users.id == user_id
                )

                merchant_profile_obj = await session.execute(stmt)
                merchant_profile     = merchant_profile_obj.first()

                # Get the picture 
                merchant_picture_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                merchant_picture = merchant_picture_obj.scalar()

                # Get the Document 
                merchant_doc_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == user_id
                ))
                merchant_doc = merchant_doc_obj.scalar()


                if merchant_profile:
                    # Convert the result row to a dictionary
                    merchant_profile_dict = merchant_profile._asdict()
                    
                    merchant_profile_dict['picture'] = f"{media_url}{merchant_picture.picture}" if merchant_profile_dict['picture'] else None
                    merchant_profile_dict['uploaddocument'] = f"{media_url}{merchant_doc.uploaddocument}" if merchant_profile_dict['uploaddocument'] else None

                    return json({
                        'success': True, 
                        'message': 'Data fetched successfully',
                        'merchant_profile': merchant_profile_dict
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f"{str(e)}"}, 500)
    

    # Update merchant profile by merchant
    @auth('userauth')
    @put()
    async def update_merchantProfile(self, request: Request, schema: UpdateMerchantProfileSchema):
        """
            This API Endpoint update merchant's profile information, including user details and KYC documents.<br/><br/>

            Parameters:<br/>
            - request: The HTTP Request object.<br/><br/>
            - schema(UpdateMerchantProfileSchema): The schema object containing validated payload data.<br/><br/>
            
            Returns:<br/>
            - JSON response with the following structure:<br/>
            - If the operation is successful:<br/>
            - 'success': True<br/>
            - 'message': 'Updated Successfully'<br/><br/>
            
            Raises:<br/>
            - Error 400: 'error': 'Email already exists'.<br/>
            - Error 400: 'error': 'Phone number already exists'.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate user
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                # Get the payload data
                email          = schema.email
                phoneno        = schema.phoneno
                full_name      = schema.full_name
                state          = schema.state
                city           = schema.city
                landmark       = schema.landmark
                zipcode        = schema.zipcode
                country        = schema.country
                address        = schema.address
                nationality    = schema.nationality
                dob            = schema.dob
                gender         = schema.gender
                marital_status = schema.marital_status


                dob_date =  datetime.strptime(dob, "%Y-%m-%d")

                existing_user_email   = await session.execute(select(Users).where(Users.email == email, Users.id != user_id))
                existing_user_phoneno = await session.execute(select(Users).where(Users.phoneno == phoneno, Users.id != user_id))

                # Validations
                if existing_user_email.scalar():
                    return json({'error': 'Email already exists'}, 400)
                
                if existing_user_phoneno.scalar():
                    return json({'error': 'Phone number already exists'}, 400)
                

                # Get the Merchant Profile 
                merchant_profile_obj = await session.execute(select(Users).where(Users.id == user_id))
                merchant_profile     = merchant_profile_obj.scalar()

                # Get the merchant kyc profile
                merchant_kyc_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == user_id
                ))
                merchant_kyc = merchant_kyc_obj.scalar()

                # Update data in user table
                merchant_profile.email     = email
                merchant_profile.phoneno   = phoneno
                merchant_profile.full_name = full_name
                
                # Update data in Kyc table
                merchant_kyc.phoneno  = phoneno
                merchant_kyc.email    = email
                merchant_kyc.state    = state
                merchant_kyc.city     = city
                merchant_kyc.landmark = landmark
                merchant_kyc.zipcode        = zipcode
                merchant_kyc.country  = country
                merchant_kyc.address  = address
                merchant_kyc.nationality    = nationality
                merchant_kyc.dateofbirth    = dob_date
                merchant_kyc.gander         = gender
                merchant_kyc.marital_status = marital_status

                session.add(merchant_profile)
                session.add(merchant_kyc)
                await session.commit()
                await session.refresh(merchant_profile)
                await session.refresh(merchant_kyc)

                return json({'success': True, 'message': 'Updated Successfully'}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Upload profile Picture by merchant
class UploadProfilePicture(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Upload Merchant Profile Picture'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/upload/profile/pic/'
    

    @auth('userauth')
    @post()
    async def upload_profilePic(self, request: Request, files: FromFiles):
        """
            This API endpoint handles uploading profile pictures of merchants.<br/><br/>

            Parameters:<br/>
                - request (Request): The request object containing the user's identity and payload data.<br/>
                - files (FromFiles): The file containing the merchant's profile picture.<br/><br/>

            Returns:<br/>
                - JSON response with success status, message, or error details.<br/>
                - On success, returns a 200 status code with a success message and the profile picture ID.<br/>
                - On failure, returns a 400 status code with an error message.<br/>
                - If the server encounters an error during the database operations, returns a 500 status code.<br/>
                - If the file exceeds the maximum allowed size, returns a 403 status code.<br/>
                - If the file name is missing, returns a 403 status code.<br/>
                - If the file type is not supported, returns a 400 status code.<br/><br/>
            
            Raises:<br/>
                - BadRequest: If the request data is invalid or the file data is not provided.<br/>
                - SQLAlchemyError: If there is an error during database operations.<br/>
                - Exception: If any other unexpected error occurs.<br/><br/>
            
            Error message:<br/>
                 - Error 403: 'File size exceeds the maximum allowed size', 'File name is missing', or 'Unsupported file type'<br/>
                 - Error 400: 'Image upload error'<br/>
                 - Error 500: 'Server Error'<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                picture = files.value

                # Get the user Profile
                user_profile_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                user_profile = user_profile_obj.scalar()


                # Save profile picture
                if picture:
                    try:
                        profile_picture_path = await upload_merchant_profile_Image(picture)

                        if profile_picture_path == 'File size exceeds the maximum allowed size':
                            return json({'message': 'File size exceeds the maximum allowed size'}, 403)
                        
                        elif profile_picture_path == 'File name is missing':
                            return json({'message': 'File name is missing'}, 403)
                        
                        else:
                            if user_profile.picture:
                                old_doc = Path('Static') / user_profile.picture
                                delete_old_file(old_doc)

                    except Exception as e:
                        return json({'msg': f'Image upload error {str(e)}'}, 400)
                else:
                    profile_picture_path = user_profile.picture

                # Update the profile Picture
                user_profile.picture = profile_picture_path

                session.add(user_profile)
                await session.commit()
                await session.refresh(user_profile)

                return json({'success': True, 'message': 'Uploaded Successfully'}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

