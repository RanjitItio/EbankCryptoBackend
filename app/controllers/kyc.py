from blacksheep.server.controllers import post, APIController
from Models.schemas import Kycschema
from sqlmodel import select
from database.db import async_engine, AsyncSession
from Models.models import Users,Kycdetails
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
import time

class UserKYCController(APIController):
    @classmethod
    def route(cls):
        return '/api/v1/user/kyc'

    @classmethod
    def class_name(cls):
        return "Users KYC"

    @post()
    async def submit_kyc(self, kyc_data: Kycschema, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # user_id = await decode_token(request.headers.get("Authorization"))
                # user = await session.get(Users, user_id)
                is_kyc_submitted = await session.get(Kycdetails, kyc_data.user_id)

                if is_kyc_submitted is None:
                    # user.kyc_data = kyc_data
                    kyca =  Kycdetails(
                        user_id=kyc_data.user_id,
                        first_name=kyc_data.firstname,
                        last_name=kyc_data.lastname,
                        dateofbirth=kyc_data.dateofbirth,
                        gander=kyc_data.gander,
                        marital_status=kyc_data.marital_status,
                        email=kyc_data.email,
                        phoneno=kyc_data.phoneno,
                        address=kyc_data.address,
                        landmark=kyc_data.landmark,
                        city=kyc_data.city,
                        zipcode=kyc_data.zipcode,
                        state=kyc_data.state,
                        country=kyc_data.country,
                        nationality=kyc_data.nationality,
                        id_type=kyc_data.id_type,
                        id_number=kyc_data.id_number,
                        id_expiry_date=kyc_data.id_expiry_date,
                        uploaddocument=kyc_data.uploaddocument
                    )
                    
                        
                    
                    session.add(kyca)              
                    await session.commit()                    
                    
                    return json({"msg": "KYC data submitted successfully"}, 200)
                else:
                    return json({"msg": "KYC data already submitted"}, 404)
        except SQLAlchemyError as e:
            return json({"Error": str(e)}, 500)