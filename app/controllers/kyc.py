from blacksheep.server.controllers import APIController, post, get, put
from Models.schemas import Kycschema
from sqlmodel import select, update
from database.db import async_engine, AsyncSession
from Models.models import Users,Kycdetails
from blacksheep import Request, json
from sqlalchemy.exc import SQLAlchemyError
from app.auth import generate_access_token, generate_refresh_token, decode_token ,check_password ,encrypt_password ,send_password_reset_email,encrypt_password_reset_token ,decrypt_password_reset_token
from Models.schemas import UpdateKycSchema




class UserKYCController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/user/kyc'

    @classmethod
    def class_name(cls):
        return "Users KYC"
    
    @get()
    async def get_kyc(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:

                try:
                    kyc_details = await session.execute(select(Kycdetails))
                    all_kyc     = kyc_details.scalars().all()
                except Exception as e:
                    return json({'error': f'{str(e)}'}, 400)
                
                if not all_kyc:
                    return json({'msg': 'No Kyc available'}, 404)
                
                return json({'All_Kyc': all_kyc})
            
        except Exception as e:
            return json({'error': f'{str(e)}'})


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
                            user_id=kyc_data.user_id,
                            firstname=kyc_data.firstname,
                            lastname=kyc_data.lastname,
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

                #Authenticate user
                # try:
                #     header_value = request.get_first_header(b"Authorization")

                #     if not header_value:
                #         return json({'msg': 'Authentication Failed Please provide auth token'}, 401)
                    
                #     header_value_str = header_value.decode("utf-8")

                #     parts = header_value_str.split()

                #     if len(parts) == 2 and parts[0] == "Bearer":
                #         token = parts[1]
                #         user_data = decode_token(token)

                #         if user_data == 'Token has expired':
                #             return json({'msg': 'Token has expired'})
                #         elif user_data == 'Invalid token':
                #             return json({'msg': 'Invalid token'})
                #         else:
                #             user_data = user_data
                            
                #         user_id = user_data["user_id"]

                #         # check the user is Admin or not
                #         try:
                #             user_object      = select(Users).where(Users.id == user_id)
                #             save_to_db       = await session.execute(user_object)
                #             user_object_data = save_to_db.scalar()

                #             if user_object_data.is_admin == False:
                #                 return json({'msg': 'Only Admin can update the Kyc'})
                            
                #         except Exception as e:
                #             return json({'msg': f'{str(e)}'})
                        
                # except Exception as e:
                #    return json({'msg': 'Authentication Failed'})
    

                try:
                    stmt       = select(Kycdetails).where(Kycdetails.id == update_kyc.kyc_id)
                    result     = await session.execute(stmt)
                    kyc_detail = result.scalar()
                except Exception as e:
                    return json({'msg': 'Unable to locate kyc'})
                
                try:
                    user_id = kyc_detail.user_id

                    get_user          = select(Users).where(Users.id == user_id)
                    get_user_obj      = await session.execute(get_user)
                    get_user_obj_data = get_user_obj.scalar()
                    
                    if not get_user_obj_data:
                        return json({'msg': 'User not found'})
                    
                except Exception as e:
                    return json({'msg': f'{str(e)}'})
                

                if update_kyc.status == "Pending":
                    try:
                        if kyc_detail:
                            try:
                                kyc_detail.status = 'Pending'
                                session.add(kyc_detail)
                                await session.commit()
                                await session.refresh(kyc_detail)
                            except Exception:
                                return json({'msg': 'Error while updating KYC details'})

                            return json({'msg': 'Updated successfully'})
                        
                        else:
                            return json({'msg': 'Kyc not found'})

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
            return json({'Final_error': f'{str(e)}'})