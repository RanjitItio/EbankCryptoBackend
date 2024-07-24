from blacksheep import json, Request, get, put
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from sqlmodel import select
from Models.models import Users, MerchantGroup, BusinessProfile, Currency
from datetime import datetime, date
import uuid
from blacksheep.exceptions import BadRequest
from pathlib import Path
from decouple import config
from sqlalchemy import desc
import re


is_development  = config('IS_DEVELOPMENT')
development_url = config('DEVELOPMENT_URL_MEDIA')
production_url  = config('PRODUCTION_URL_MEDIA')


if is_development == 'True':
    url = development_url
else:
    url = production_url


async def save_business_logo(request: Request):
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


#Update Merchant by Admin
@auth('userauth')
@put('/api/admin/merchant/update/')
async def search_all_transaction(self, request: Request, query: str = ''):
    """
     Admin will be able to Update Merchant Details
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            AdminID       = user_identity.claims.get('user_id') if user_identity else None

            request_body = await request.form()

            #Request Payload Validation##
            if not request_body:
                return json({'msg': 'Missing request payload'}, 400)
            
            required_fields = ['bsn_name', 'bsn_url', 'currency', 'group', 'fee', 'merchant_id', 'status']

            missing_fields = [field for field in required_fields if field not in request_body]

            if missing_fields:
                return json({'msg': f'Missing fields: {", ".join(missing_fields)}'}, 400)
            ##Request Payload validation##

            business_name = request_body['bsn_name']
            business_url  = request_body['bsn_url']
            currency_name = request_body['currency']
            group_name    = request_body['group']
            merchant_id   = request_body['merchant_id']
            status        = request_body['status']
            fee           = request_body['fee']
            logo          = await request.files()


            merchant_id  = int(merchant_id)
            fee          = float(fee)

            #Check the user is Admin or not
            try:
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can update the Merchant details'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Check Finish

            #Get the merchant with requested merchant ID
            try:
                merchant_obj      = await session.execute(select(BusinessProfile).where(BusinessProfile.id == merchant_id))
                merchant_obj_data = merchant_obj.scalar()

            except Exception as e:
                return json({'msg': 'Merchant error', 'error': f'{str(e)}'}, 400)
            
            
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
            try:
                merchant_grp_obj = await session.execute(select(MerchantGroup).where(MerchantGroup.name == group_name))
                merchant_grp_obj = merchant_grp_obj.scalar()

                if not merchant_grp_obj:
                    return json({'msg': 'requested group not found'}, 404)
                
                merchant_group_id = merchant_grp_obj.id

            except Exception as e:
                return json({'msg': 'Group error', 'error': f"{str(e)}"}, 400)
            
            #Check Admin is sending logo or not
            if logo:
                try:
                    business_logo_path = await save_business_logo(request)
                except Exception as e:
                    return json({'msg': f'Image upload error {str(e)}'}, 400)
            else:
                business_logo_path = merchant_obj_data.logo

            if status == 'Approved':
                try:
                    merchant_obj_data.bsn_name  = business_name
                    merchant_obj_data.bsn_url   = business_url
                    merchant_obj_data.currency  = currency_id
                    merchant_obj_data.group     = merchant_group_id
                    merchant_obj_data.fee       = fee
                    merchant_obj_data.logo      = business_logo_path
                    merchant_obj_data.status    = status
                    merchant_obj_data.is_active = True

                    session.add(merchant_obj_data)
                    await session.commit()
                    await session.refresh(merchant_obj_data)

                except Exception as e:
                    return json({'msg': 'Merchant update error', 'error': f'{str(e)}'}, 400)

            elif status == 'Moderation': 

                try:
                    merchant_obj_data.bsn_name  = business_name
                    merchant_obj_data.bsn_url   = business_url
                    merchant_obj_data.currency  = currency_id
                    merchant_obj_data.group     = merchant_group_id
                    merchant_obj_data.fee       = fee
                    merchant_obj_data.logo      = business_logo_path
                    merchant_obj_data.status    = status
                    merchant_obj_data.is_active = False

                    session.add(merchant_obj_data)
                    await session.commit()
                    await session.refresh(merchant_obj_data)

                except Exception as e:
                    return json({'msg': 'Merchant update error', 'error': f'{str(e)}'}, 400)

            else:
                try:
                    merchant_obj_data.bsn_name  = business_name
                    merchant_obj_data.bsn_url   = business_url
                    merchant_obj_data.currency  = currency_id
                    merchant_obj_data.group     = merchant_group_id
                    merchant_obj_data.fee       = fee
                    merchant_obj_data.logo      = business_logo_path
                    merchant_obj_data.status    = 'Cancelled'
                    merchant_obj_data.status    = status
                    merchant_obj_data.is_active = False

                    session.add(merchant_obj_data)
                    await session.commit()
                    await session.refresh(merchant_obj_data)

                except Exception as e:
                    return json({'msg': 'Merchant update error', 'error': f'{str(e)}'}, 400)
                
            return json({'msg': 'Merchant data updated Successfully'}, 200)
        
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    



#View all merchant by Admin
@auth('userauth')
@get('/api/admin/all/merchant/')
async def search_all_transaction(self, request: Request, limit: int = 25, offset: int = 0):
    """
     Admin will be able to View Merchants
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            AdminID       = user_identity.claims.get('user_id') if user_identity else None

            #Check the user is Admin or not
            try:
                admin_obj      = await session.execute(select(Users).where(Users.id == AdminID))
                admin_obj_data = admin_obj.scalar()

                if not admin_obj_data.is_admin:
                    return json({'msg': 'Only admin can update the Merchant details'}, 401)
                
            except Exception as e:
                return json({'msg': 'Admin authentication error', 'error': f'{str(e)}'}, 400)
            #Admin Verification Complete

            try:
                merchant_obj = await session.execute(select(BusinessProfile).order_by(desc(BusinessProfile.id)).limit(limit).offset(offset))
                merchant_obj_data = merchant_obj.scalars().all()

                if not merchant_obj_data:
                    return json({'msg': 'No merchant available to show'}, 404)
                
            except Exception as e:
                return json({'msg': 'Merchant fetch error', 'error': f'{str(e)}'}, 400)
            
            #Get The users
            try:
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'User fetch error', 'error': f'{str(e)}'}, 400)
            

            #Get The Merchant Groups
            try:
                group_obj      = await session.execute(select(MerchantGroup))
                group_obj_data = group_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'Group fetch error', 'error': f'{str(e)}'}, 400)
            
            #Get The Merchant Groups
            try:
                currency_obj      = await session.execute(select(Currency))
                currency_obj_data = currency_obj.scalars().all()
                
            except Exception as e:
                return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
            
            user_dict     = {user.id: user for user in user_obj_data}
            group_dict    = {grp.id: grp for grp in group_obj_data}
            currency_dict = {cur.id: cur for cur in currency_obj_data}

            combined_data = []
        
            for merchant in merchant_obj_data:
                user_id   = merchant.user
                merchant_user = user_dict.get(user_id)

                group_id   = merchant.group
                group_data = group_dict.get(group_id)

                currency_id   = merchant.currency
                currency_data = currency_dict.get(currency_id)

                user_data = {
                    'full_name': merchant_user.full_name,
                    'id': merchant_user.id

                } if merchant_user else None

                combined_data.append(
                    {
                        'user': user_data,
                        'group': group_data,
                        'currency': currency_data,
                        'merchant': {
                            'id':           merchant.id,
                            'bsn_url':      merchant.bsn_url,
                            'user':         merchant.user,
                            'merchant_id':  merchant.merchant_id,
                            'logo':         f"{url}{merchant.logo}",
                            'group':        merchant.group,
                            'created_time': merchant.created_time,
                            'is_active':    merchant.is_active,
                            'bsn_name':     merchant.bsn_name,
                            'currency':     merchant.currency,
                            'bsn_msg':      merchant.bsn_msg,
                            'fee':          merchant.fee,
                            'created_date': merchant.created_date,
                            'status':       merchant.status
                        }
                    }
                )

            return json({'msg': 'Merchant data fetched successfully', 'data': combined_data}, 200)

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)
    



@auth('userauth')
@get('/api/v2/admin/search/merchant/')
async def search_merchant(self, request: Request, query: str):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            AdminID         = user_identity.claims.get("user_id") if user_identity else None

            searched_text = query

            # Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
            if re.fullmatch(r'\d+', searched_text):
                parsed_value = int(searched_text)

            elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', searched_text):
                parsed_value = datetime.strptime(searched_text, '%Y-%m-%d').date()

            else:
                parsed_value = searched_text

            try:
                all_user_obj      = await session.execute(select(Users))
                all_user_obj_data = all_user_obj.scalars().all()

                user_search_id   = None
                
            except Exception as e:
                return json({'msg': 'User not found'}, 400)
            
            try:
                currency_obj      = await session.execute(select(Currency))
                currency_data     = currency_obj.scalars().all()

                currency_id      = None

            except Exception as e:
                return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
            try:
                merchant_grp_obj  = await session.execute(select(MerchantGroup))
                merchant_grp_data = merchant_grp_obj.scalars().all()

                merchant_grp_id = None

            except Exception as e:
                return json({'msg': 'Currency fetch error', 'error': f'{str(e)}'}, 400)
            
            if parsed_value == ' ':
                try:
                    merchant_profile_obj = select(BusinessProfile).order_by((BusinessProfile.id).desc)
                    
                    searched_profile = await session.execute(merchant_profile_obj)

                    merchant_list = searched_profile.scalars().all()

                except Exception as e:
                    return json({'msg': 'Created date fetch error', 'error': f'{str(e)}'}, 400)
                
            elif isinstance(parsed_value, date):
                try:
                    merchant_profile_obj = select(BusinessProfile).where(
                        BusinessProfile.created_date == parsed_value).order_by((BusinessProfile.id).desc())
                    
                    searched_profile = await session.execute(merchant_profile_obj)

                    merchant_list = searched_profile.scalars().all()

                except Exception as e:
                    return json({'msg': 'Created date fetch error', 'error': f'{str(e)}'}, 400)
            
            elif isinstance(parsed_value, str):

                for user in all_user_obj_data:
                    if user.full_name == parsed_value:
                        user_search_id = user.id

                for currency in currency_data:
                    if currency.name == parsed_value:
                        currency_id   = currency.id

                for grp in merchant_grp_data:
                    if grp.name == parsed_value:
                        merchant_grp_id = grp.id

                if user_search_id:
                    merchant_profile_obj = select(BusinessProfile).where(
                        BusinessProfile.user == user_search_id).order_by((BusinessProfile.id).desc())
                    
                    searched_profile = await session.execute(merchant_profile_obj)
                    merchant_list = searched_profile.scalars().all()

                elif currency_id:
                    merchant_profile_obj = select(BusinessProfile).where(
                        BusinessProfile.currency == currency_id).order_by((BusinessProfile.id).desc())
                    
                    searched_profile = await session.execute(merchant_profile_obj)
                    merchant_list    = searched_profile.scalars().all()
                
                elif merchant_grp_id:
                    merchant_profile_obj = select(BusinessProfile).where(
                        BusinessProfile.group == merchant_grp_id).order_by((BusinessProfile.id).desc())
                    
                    searched_profile = await session.execute(merchant_profile_obj)
                    merchant_list    = searched_profile.scalars().all()

                else:
                    try:
                        merchant_profile_obj = select(BusinessProfile).where(
                            (BusinessProfile.merchant_id.ilike(parsed_value))  |
                            (BusinessProfile.bsn_name.ilike(parsed_value))  |
                            (BusinessProfile.bsn_url.ilike(parsed_value))  |
                            (BusinessProfile.status.ilike(parsed_value))  
                        )

                        searched_profile = await session.execute(merchant_profile_obj)

                        merchant_list = searched_profile.scalars().all()

                    except Exception as e:
                        return json({'msg': 'Merchant profile search error in string', 'error': f'{str(e)}'}, 400)
                    
            user_dict  = {user.id: user for user in all_user_obj_data}
            group_dict = {grp.id: grp for grp in merchant_grp_data}
            currency_dict = {cur.id: cur for cur in currency_data}

            combined_data = []

            for merchant in merchant_list:
                user_id   = merchant.user
                user      = user_dict.get(user_id)

                group_id   = merchant.group
                group_data = group_dict.get(group_id)

                currency_id   = merchant.currency
                currency_data = currency_dict.get(currency_id)

                user_data = {
                    'full_name': user.full_name,
                    'id': user.id

                } if user else None
                
                combined_data.append(
                    {
                        'user': user_data,
                        'group': group_data,
                        'currency': currency_data,
                        'merchant': {
                            'id':           merchant.id,
                            'bsn_url':      merchant.bsn_url,
                            'user':         merchant.user,
                            'merchant_id':  merchant.merchant_id,
                            'logo':         f"{url}{merchant.logo}",
                            'group':        merchant.group,
                            'created_time': merchant.created_time,
                            'is_active':    merchant.is_active,
                            'bsn_name':     merchant.bsn_name,
                            'currency':     merchant.currency,
                            'bsn_msg':      merchant.bsn_msg,
                            'fee':          merchant.fee,
                            'created_date': merchant.created_date,
                            'status':       merchant.status
                        }
                    }
                )

            return json({'msg': 'merchant data fetched successfully', 'data': combined_data}, 200)
                

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)