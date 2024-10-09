from blacksheep.server.authorization import auth
from blacksheep import json, get, Request, post, put
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantAccountBalance, MerchantProdTransaction
from Models.Admin.PG.schema import MerchantBalancePeriodUpdateSchema
from sqlmodel import select, and_, desc
from datetime import timedelta
import re






## Get all the available balances of the merchant
@auth('userauth')
@get('/api/v7/admin/merchant/account/balance/')
async def merchant_account_balance(self, request: Request, id: int, currency: str):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            merchantID = id

            # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            ## Get available mature balance of the merchant
            merchant__balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == merchantID,
                    MerchantAccountBalance.currency    == currency,
                )
            ))
            merchant__balance = merchant__balance_obj.scalar()

            return json({
                'success': True,
                'mature_balance': merchant__balance.mature_balance,
                'immature_balance': merchant__balance.immature_balance
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    




# Update Merchant settlement periods
@auth('userauth')
@put('/api/v7/admin/merchant/update/period/')
async def merchant_account_balance(self, request: Request, schema: MerchantBalancePeriodUpdateSchema):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            # # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            # Get payload data
            merchantID             = schema.merchant_id
            settlement_period      = schema.settlement_period
            minimum_withdrawal_amt = schema.minimum_withdrawal_amt
            
            # Get the merchant
            merchant_user_obj = await session.execute(select(Users).where(
                Users.id == int(merchantID)
            ))
            merchant_user = merchant_user_obj.scalar()
            
            # Get merchant settlement period
            numeric_settlement_period = re.findall(r'\d+', settlement_period)
            settlement_period_value    = numeric_settlement_period[0]

            merchant_user.settlement_period = settlement_period
            # merchant_user.settlement_date   = settlement_period_date
            merchant_user.minimum_withdrawal_amount = float(minimum_withdrawal_amt)

            session.add(merchant_user)
            await session.commit()
            await session.refresh(merchant_user)

            return json({
                'success': True,
                'message': 'Updated Successfully'
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


## Get settlement period, Frozen balance by Admin
@auth('userauth')
@get('/api/v7/admin/merchant/balance/period/{user_id}/')
async def merchant_account_balance(self, request: Request, user_id: int):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            # # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            # Get minimum withdrawal amount of the merchant
            merchant_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            merchant_user = merchant_user_obj.scalar()

            minimum_withdrawal_amount = merchant_user.minimum_withdrawal_amount

            settlement_period = merchant_user.settlement_period

            return json({
                'success': True,
                'minimum_withdrawal_amount': minimum_withdrawal_amount,
                'settlement_period': settlement_period
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)