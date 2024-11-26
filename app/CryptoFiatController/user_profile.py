from app.controllers.controllers import get, put, post
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from blacksheep import json, Request, FromFiles
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_
from Models.models import Users, Kycdetails
from app.controllers.environment import media_url
from app.req_stream import upload_crypto_fiat_user_profile_Image, delete_old_file
from Models.FIAT.Schema import UpdateFiatCryptoUserProfileSchema
from datetime import datetime
from pathlib import Path




## User profile controller
class CryprtoFIATUserProfileController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Crypto FIAT User Profile'
    

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/fiat/crypto/user/profile/'


    @auth('userauth')
    @get()
    async def get_FiatCryptoUserProfile(self, request: Request):
        """
            This function retrieves the Fiat-Crypto user profile information.<br/>

            Parameters:<br/>
            - request (Request): The request object containing user identity and other relevant information.<br/>
    <br/>
            Returns:<br/>
            - JSON response with the following structure:<br/>
            - success (bool): Indicates whether the operation was successful.<br/>
            - message (str): Provides a message describing the outcome of the operation.<br/>
            - user_profile (dict): Contains the user profile information if the operation was successful.<br/>
    <br/>
            Raises:<br/>
            - Exception: If any error occurs during the database query or processing.<br/>
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

                user_profile_obj = await session.execute(stmt)
                user_profile     = user_profile_obj.first()

                # Get the picture 
                user_picture_obj = await session.execute(select(Users).where(
                    Users.id == user_id
                ))
                user_picture = user_picture_obj.scalar()

                # Get the Document 
                user_doc_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == user_id
                ))
                user_doc = user_doc_obj.scalar()


                if user_profile:
                    # Convert the result row to a dictionary
                    user_profile_dict = user_profile._asdict()
                    
                    user_profile_dict['picture'] = f"{media_url}{user_picture.picture}" if user_profile_dict['picture'] else None
                    user_profile_dict['uploaddocument'] = f"{media_url}{user_doc.uploaddocument}" if user_profile_dict['uploaddocument'] else None

                    return json({
                        'success': True, 
                        'message': 'Data fetched successfully',
                        'user_profile': user_profile_dict
                        }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f"{str(e)}"}, 500)
    

    # Update merchant profile by merchant
    @auth('userauth')
    @put()
    async def update_CryptoFiatUserProfile(self, request: Request, schema: UpdateFiatCryptoUserProfileSchema):
        """
            This function updates the Fiat-Crypto user profile information.<br/>
    <br/>
            Parameters:<br/>
            - request (Request): The request object containing user identity and other relevant information.<br/>
            - schema (UpdateFiatCryptoUserProfileSchema): The schema object containing the user profile data.<br/>
    <br/>
            Returns:<br/>
            - JSON response with the following structure:<br/>
            - success (bool): Indicates whether the operation was successful.<br/>
            - message (str): Provides a message describing the outcome of the operation.<br/>
    <br/>
            Raises:<br/>
            - Exception: If any error occurs during the database query or processing.<br/>
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
                user_profile_obj = await session.execute(select(Users).where(Users.id == user_id))
                user_profile     = user_profile_obj.scalar()

                # Get the merchant kyc profile
                user_kyc_obj = await session.execute(select(Kycdetails).where(
                    Kycdetails.user_id == user_id
                ))
                user_kyc = user_kyc_obj.scalar()

                # Update data in user table
                user_profile.email     = email
                user_profile.phoneno   = phoneno
                user_profile.full_name = full_name
                
                # Update data in Kyc table
                user_kyc.phoneno  = phoneno
                user_kyc.email    = email
                user_kyc.state    = state
                user_kyc.city     = city
                user_kyc.landmark = landmark
                user_kyc.zipcode        = zipcode
                user_kyc.country  = country
                user_kyc.address  = address
                user_kyc.nationality    = nationality
                user_kyc.dateofbirth    = dob_date
                user_kyc.gander         = gender
                user_kyc.marital_status = marital_status

                session.add(user_profile)
                session.add(user_kyc)
                await session.commit()
                await session.refresh(user_profile)
                await session.refresh(user_kyc)

                return json({'success': True, 'message': 'Updated Successfully'}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Upload profile Picture by merchant
class UploadCryptoFIATUserProfilePicture(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Upload Crypto FIAT User Profile Picture'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/upload/user/profile/pic/'


    @auth('userauth')
    @post()
    async def upload_user_profilePic(self, request: Request, files: FromFiles):
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
                        profile_picture_path = await upload_crypto_fiat_user_profile_Image(picture)

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