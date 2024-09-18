from blacksheep import json, Request
from blacksheep.server.controllers import APIController
from app.cryptofiatcontrollers.controllers import post
from Models.schemas import UserLoginSchema
from database.db import AsyncSession, async_engine
from sqlmodel import select
from Models.models import Users, Kycdetails
from app.auth import check_password, generate_access_token, generate_refresh_token
from datetime import datetime





# Login user
class CryptoFiatLoginController(APIController):

    @classmethod
    def route(cls):
        return '/api/v1/crypto/login/'

    @classmethod
    def class_name(cls):
        return "Users login"
    
    
    @post()
    async def login_crypto_user(self, user: UserLoginSchema):
        
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    existing_user = await session.execute(select(Users).where(Users.email == user.email))
                    first_user = existing_user.scalars().first()
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 400)
                
                
                # Password validation
                if first_user and check_password(user.password,first_user.password):

                    # Check kyc is exist for the user
                    merchnat_kyc_obj = await session.execute(select(Kycdetails).where(
                        Kycdetails.user_id == first_user.id
                    ))
                    merchnat_kyc_ = merchnat_kyc_obj.scalar()

                    # If kyc not submitted
                    if not first_user.is_kyc_submitted and not first_user.is_admin and not merchnat_kyc_:
                        return json({
                            'message': 'Kyc not submitted',  
                            'first_name':  first_user.first_name,
                            'last_name': first_user.lastname,
                            'contact_number': first_user.phoneno,
                            'email': first_user.email,
                            'user_id': first_user.id                
                            }, 400)

                    # For active users
                    if first_user.is_active:
                        current_time = datetime.now()
                        login_count  = first_user.login_count
                       
                        if login_count == None:
                            login_count = 0
                            
                        try:
                            first_user.lastlogin = current_time

                            if login_count == 0:
                                count = login_count + 1
                                first_user.login_count = count

                            elif login_count > 0:
                                count = login_count + 1
                                first_user.login_count = count

                            await session.commit()
                            await session.refresh(first_user)
                            
                        except Exception as e:
                            return json({'msg': 'Login time error', 'error': f'{str(e)}'}, 400)
                        
                        response = json({
                            'is_merchant': first_user.is_merchent,
                            'user_name': first_user.full_name,
                            'access_token': generate_access_token(first_user.id),
                            'refresh_token': generate_refresh_token(first_user.id)
                        },200)

                        return response
                    
                    else:
                        return json({'msg': 'Your account is not active. Please contact the administrator'}, 400)
                    
                else:
                    return json({'msg': 'Invalid credentials'}, 400)

        except Exception as e:
            return json({"Error": str(e)})