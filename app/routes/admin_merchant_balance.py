from blacksheep import json, get, Request
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_
from Models.models import Users
from Models.models2 import MerchantAccountBalance




# Get merchant Account balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/account/balance/{user_id}/')
async def merchant_account_balance(request: Request, user_id: int, currency: str = None):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')\
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends
            # Get the account balance of the user
            if currency:
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(
                        MerchantAccountBalance.merchant_id == user_id,
                        MerchantAccountBalance.currency    == currency
                        )
                    ))
                merchant_account_balance = merchant_account_balance_obj.scalar()

            else:
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(
                        MerchantAccountBalance.merchant_id == user_id,
                        MerchantAccountBalance.currency    == 'USD'
                        )
                    ))
                merchant_account_balance = merchant_account_balance_obj.scalar()

            return json({
                'success': True,
                'merchant_balance_data': merchant_account_balance
            }, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Get matured balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/mature/account/balance/{user_id}/')
async def merchant_account_balance(request: Request, user_id: int, currency: str):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')\
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_mature_account_balance = merchant_account_balance.mature_balance
            else:
                merchant_mature_account_balance = 0

            return json({
                'success': True,
                'merchant_mature_balance': merchant_mature_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    

@auth('userauth')
@get('/api/v4/admin/merchant/frozen/account/balance/{user_id}/')
async def merchant_account_balance(request: Request, user_id: int, currency: str):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')\
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_frozen_account_balance = merchant_account_balance.frozen_balance
            else:
                merchant_frozen_account_balance = 0

            return json({
                'success': True,
                'merchant_frozen_balance': merchant_frozen_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)



# Get immatured balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/immature/account/balance/{user_id}/')
async def merchant_account_balance(request: Request, user_id: int, currency: str):
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_immature_account_balance = merchant_account_balance.immature_balance
            else:
                merchant_immature_account_balance = 0

            return json({
                'success': True,
                'merchant_immature_balance': merchant_immature_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
