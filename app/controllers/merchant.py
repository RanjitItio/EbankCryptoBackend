from blacksheep import json, Request, FromJSON
from app.controllers.controllers import post, put, get
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from blacksheep.exceptions import BadRequest
from Models.models import MerchantProfile, Currency, MerchantGroup, Users
from datetime import datetime
from pathlib import Path
import uuid
from sqlmodel import select, and_
from Models.Merchant.schema import MerchantDetailSchema
from decouple import config
from sqlalchemy import desc

is_development = config('IS_DEVELOPMENT')
development_url = config('DEVELOPMENT_URL_MEDIA')
production_url  = config('PRODUCTION_URL_MEDIA')




class MerchantController(APIController):

    @classmethod
    def route(cls) -> str | None:
        return '/api/v4/user/merchant/'
    
    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Controller'
    

    async def save_business_logo(self, request: Request):
        file_data = await request.files()
    
        for part in file_data:
            file_bytes = part.data
            original_file_name  = part.file_name.decode()

        file_extension = original_file_name.split('.')[-1]

        file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4()}.{file_extension}"

        if not file_name:
            return BadRequest("File name is missing")

        file_path = Path("Static/Merchant") / file_name

        try:
            with open(file_path, mode="wb") as user_files:
                user_files.write(file_bytes)

        except Exception:
            file_path.unlink()
            raise
        
        return str(file_path.relative_to(Path("Static")))
    


    #Create new Merchant by Merchant user
    @auth('userauth')
    @post()
    async def create_merchant(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_body = await request.form()

                if not request_body:
                    return json({'msg': 'Missing request payload'}, 400)
                
                required_fields = ['bsn_name', 'bsn_url', 'currency', 'bsn_msg']

                missing_fields = [field for field in required_fields if field not in request_body]

                if missing_fields:
                    return json({'msg': f'Missing fields: {", ".join(missing_fields)}'}, 400)

                business_name = request_body['bsn_name']
                business_url  = request_body['bsn_url']
                currency_name = request_body['currency']
                # group_name    = request_body['group']
                business_msg  = request_body['bsn_msg']
                logo          = await request.files()
                

                #Check the user is merchant or not
                try:
                    user_obj  = await session.execute(select(Users).where(Users.id == user_id))
                    user_data = user_obj.scalar()

                    is_merchant = user_data.is_merchent
                    is_active   = user_data.is_active

                    if not is_merchant:
                        return json({'msg': 'Only merchant allowed'}, 403)
                    
                    if not is_active:
                        return json({'msg': 'Account not activated yet please contact Administration'}, 403)
                    
                except Exception as e:
                    return json({'msg': 'User error', 'error': f'{str(e)}'}, 400)
                
                #Check the Business name is Exists or not
                try:
                    business_obj  = await session.execute(select(MerchantProfile).where(MerchantProfile.bsn_name == business_name))
                    business_data = business_obj.scalar()

                    if business_data:
                        return json({'msg': 'This business name has already been taken'}, 405)
                    
                except Exception as e:
                    return json({'msg': 'User error', 'error': f'{str(e)}'}, 400)
                
                #Check the Business URL is Exists or not
                try:
                    business_url_obj  = await session.execute(select(MerchantProfile).where(MerchantProfile.bsn_url == business_url))
                    business_url_data = business_url_obj.scalar()

                    if business_url_data:
                        return json({'msg': 'This URl has already been taken'}, 405)
                    
                except Exception as e:
                    return json({'msg': 'User error', 'error': f'{str(e)}'}, 400)
                
                if logo:
                    try:
                        business_logo_path = await self.save_business_logo(request)
                    except Exception as e:
                        return json({'msg': f'Image upload error {str(e)}'}, 400)
                else:
                    business_logo_path = 'Merchant/default-merchant.png'

                #Get the Currency ID
                try:
                    currency_obj = await session.execute(select(Currency).where(Currency.name == currency_name))
                    currency_obj = currency_obj.scalar()

                    if not currency_obj:
                        return json({'msg': 'requested currency not found'}, 404)
                    
                    currency_id = currency_obj.id
                except Exception as e:
                    return json({'msg': 'Currency error', 'error': f"{str(e)}"}, 400)
                

                try:
                    merchant = MerchantProfile(
                        user = user_id,
                        bsn_name = business_name,
                        bsn_url  = business_url,
                        currency = currency_id,
                        bsn_msg  = business_msg,
                        logo     = business_logo_path,
                    )

                    session.add(merchant)
                    await session.commit()
                    await session.refresh(merchant)

                except Exception as e:
                    return json({'msg': 'Merchant create error', 'error': f'{str(e)}'}, 400)


                return json({'msg': 'Merchant created successfully'}, 200)
                    
        except Exception as e:
            return json({'msg':'Server Error', 'error': f'{str(e)}'}, 500)
        


    # Update Merchant by Merchant user
    @auth('userauth')
    @put()
    async def update_merchant(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_body = await request.form()

                if not request_body:
                    return json({'msg': 'Missing request payload'}, 400)
                
                required_fields = ['bsn_name', 'bsn_url', 'currency', 'bsn_msg', 'merchant_id']

                missing_fields = [field for field in required_fields if field not in request_body]

                if missing_fields:
                    return json({'msg': f'Missing fields: {", ".join(missing_fields)}'}, 400)

                business_name = request_body['bsn_name']
                business_url  = request_body['bsn_url']
                currency_name = request_body['currency']
                business_msg  = request_body['bsn_msg']
                merchant_id   = request_body['merchant_id']
                logo          = await request.files()

                merchant_id  = int(merchant_id)

                #Check the user is merchant or not
                try:
                    user_obj  = await session.execute(select(Users).where(Users.id == user_id))
                    user_data = user_obj.scalar()

                    is_merchant = user_data.is_merchent
                    is_active   = user_data.is_active

                    if not is_merchant:
                        return json({'msg': 'Only merchant allowed'}, 403)
                    
                    if not is_active:
                        return json({'msg': 'Account not activated yet please contact Administration'}, 403)
                    
                except Exception as e:
                    return json({'msg': 'User error', 'error': f'{str(e)}'}, 400)
                
                #Check merchant belongs to the requested user or Not
                try:
                    merchant_check_obj      = await session.execute(select(MerchantProfile).where
                                                                    (and_(MerchantProfile.id == merchant_id, MerchantProfile.user == user_id)))
                    merchant_check_obj_data = merchant_check_obj.scalar()

                    if not merchant_check_obj_data:
                        return json({'msg': 'Merchant not belongs to requested user'}, 403)

                except Exception as e:
                    return json({'msg': 'Merchant error', 'error': f'{str(e)}'}, 400)
                
                #Check the Business name is Exists for other merchant or Not
                if business_name != merchant_check_obj_data.bsn_name:
                    try:
                        business_obj  = await session.execute(select(MerchantProfile).where(MerchantProfile.bsn_name == business_name))
                        business_data = business_obj.scalar()

                        if business_data:
                            return json({'msg': 'This business name has already been taken'}, 405)
                            
                    except Exception as e:
                        return json({'msg': 'Business Name error', 'error': f'{str(e)}'}, 400)
                
                #Check the Business URL is Exists for other merchant or not
                if business_url != merchant_check_obj_data.bsn_url:
                    try:
                        business_url_obj  = await session.execute(select(MerchantProfile).where(MerchantProfile.bsn_url == business_url))
                        business_url_data = business_url_obj.scalar()

                        if business_url_data:
                            return json({'msg': 'This URl has already been taken'}, 405)
                        
                    except Exception as e:
                        return json({'msg': 'Business URL error', 'error': f'{str(e)}'}, 400)
                
                #Check user is providing logo or not
                if logo:
                    try:
                        business_logo_path = await self.save_business_logo(request)
                    except Exception as e:
                        return json({'msg': f'Image upload error {str(e)}'}, 400)
                else:
                    business_logo_path = merchant_check_obj_data.logo

                #Get the Currency ID
                try:
                    currency_obj = await session.execute(select(Currency).where(Currency.name == currency_name))
                    currency_obj = currency_obj.scalar()

                    if not currency_obj:
                        return json({'msg': 'requested currency not found'}, 404)
                    
                    currency_id = currency_obj.id
                except Exception as e:
                    return json({'msg': 'Currency error', 'error': f"{str(e)}"}, 400)
                
                #Get the merchant Group ID
                # try:
                #     merchant_grp_obj = await session.execute(select(MerchantGroup).where(MerchantGroup.name == group_name))
                #     merchant_grp_obj = merchant_grp_obj.scalar()

                #     if not merchant_grp_obj:
                #         return json({'msg': 'requested group not found'}, 404)
                    
                #     merchant_group_id = merchant_grp_obj.id

                # except Exception as e:
                #     return json({'msg': 'Group error', 'error': f"{str(e)}"}, 400)

                try:
                    
                    merchant_check_obj_data.bsn_name = business_name
                    merchant_check_obj_data.bsn_url  = business_url
                    merchant_check_obj_data.currency = currency_id
                    merchant_check_obj_data.bsn_msg  = business_msg
                    merchant_check_obj_data.logo     = business_logo_path
                    # merchant_check_obj_data.group    = merchant_group_id

                    session.add(merchant_check_obj_data)
                    await session.commit()
                    await session.refresh(merchant_check_obj_data)

                except Exception as e:
                    return json({'msg': 'Merchant create error', 'error': f'{str(e)}'}, 400)
                
            return json({'msg': 'Merchant Updated Successfully'}, 200)
        
        except Exception as e:
            return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    

    #View Merchant detail
    @auth('userauth')
    @get()
    async def get_merchant_detail(self, request: Request, id: int):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')
                # print(request)
                
                # input_data    = input.value
                merchant_id   = id

                try:
                    merchant = await session.execute(select(Users).where(Users.id == user_id))
                    merchant_obj = merchant.scalar()

                    is_merchant = merchant_obj.is_merchent

                    if not is_merchant:
                        return json({'msg': 'Only Merchant allowed'}, 403)
                    
                except Exception as e:
                    return json({'msg': 'User identify error', 'error': f'{str(e)}'}, 400)

                #Check the requested merchant id is of requested user or not
                try:
                    merchant_obj      = await session.execute(select(MerchantProfile).where
                                                         (and_(MerchantProfile.id == merchant_id, MerchantProfile.user ==  user_id)))
                    merchant_obj_data = merchant_obj.scalar()

                    if not merchant_obj_data:
                        return json({'msg': 'Merchant is not of Requested user'}, 403)
                    
                except Exception as e:
                    return json({'msg': 'Merchant Check error', 'error': f'{str(e)}'}, 400)
                
                try:
                    currency_obj      = await session.execute(select(Currency))
                    currency_obj_data = currency_obj.scalars().all()

                except Exception as e:
                    return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
                
                currency_dict = {currency.id: currency for currency in currency_obj_data}
                currency_     = merchant_obj_data.currency
                currency_data = currency_dict.get(currency_)

                combined_data = []

                combined_data.append({
                    'currency': currency_data,
                    'merchant': merchant_obj_data
                })

                return json({'msg': 'Merchant detail fetched successfully', 'data': combined_data}, 200)

        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)
        



# #Get all Created merchant by Merchant user
class UserAvailableMerchantController(APIController):

    @classmethod
    def class_name(cls):
        return 'Availbale Merchants of User'
    
    @classmethod
    def route(cls):
        return '/api/v4/user/all/merchants/'
    
    if is_development == 'True':
        url = development_url
    else:
        url = production_url
        
    @auth('userauth')
    @get()
    async def get_user_created_merchants(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None

                #Get the available merchant of the user
                try:
                    merchants_obj     = await session.execute(select(MerchantProfile).
                                                              where(MerchantProfile.user == user_id).
                                                              order_by(desc(MerchantProfile.id)))
                    
                    all_merchants_obj = merchants_obj.scalars().all()

                    if not all_merchants_obj:
                        return json({'msg': 'Merchant not available'}, 404)

                except Exception as e:
                    return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)
                
                #Get The currency of the Merchant
                try:
                    currency_obj      = await session.execute(select(Currency))
                    currency_obj_data = currency_obj.scalars().all()

                except Exception as e:
                    return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
                
                currency_dict = {currency.id: currency for currency in currency_obj_data}
                combined_data = []

                for merchants in all_merchants_obj:
                    currency_id   = merchants.currency
                    currency_data = currency_dict.get(currency_id)

                    merchant_data = {
                        'bsn_url':     merchants.bsn_url,
                        'id':          merchants.id,
                        'merchant_id': merchants.merchant_id,
                        'logo':        f'{self.url}{merchants.logo}',
                        'created_time': merchants.created_time,
                        'is_active':    merchants.is_active,
                        'currency':     merchants.currency,
                        'bsn_name':     merchants.bsn_name,
                        'user':         merchants.user,
                        'bsn_msg':      merchants.bsn_msg,
                        'fee':          merchants.fee if merchants.fee else None,
                        'created_date': merchants.created_date,
                        'status':       merchants.status if merchants.status else None
                    }

                    combined_data.append({
                        'merchants': merchant_data,
                        'currency': currency_data
                    })

                return json({'msg': 'Merchant data fetched successfully', 'data': combined_data}, 200)

        except Exception as e:
            return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)