from blacksheep import json, Request, get, put
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from sqlmodel import select
from Models.models import Users, MerchantGroup, MerchantProfile, Currency
from datetime import datetime
import uuid
from blacksheep.exceptions import BadRequest
from pathlib import Path


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
                merchant_obj      = await session.execute(select(MerchantProfile).where(MerchantProfile.id == merchant_id))
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
                    merchant_obj_data.status    = status
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
async def search_all_transaction(self, request: Request, query: str = ''):
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
                merchant_obj = await session.execute(select(MerchantProfile))
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
            
            user_dict  = {user.id: user for user in user_obj_data}
            group_dict = {grp.id: grp for grp in group_obj_data}

            combined_data = []
        
            for merchant in merchant_obj_data:
                user_id   = merchant.user
                user      = user_dict.get(user_id)

                group_id   = merchant.group
                group_data = group_dict.get(group_id)

                user_data = {
                    'full_name': user.full_name,
                    'id': user.id

                } if user else None

                combined_data.append(
                    {
                        'user': user_data,
                        'group': group_data,
                        'merchant': merchant
                    }
                )

            return json({'msg': 'Merchant data fetched successfully', 'data': combined_data}, 200)

    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)

