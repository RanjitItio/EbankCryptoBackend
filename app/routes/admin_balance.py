from blacksheep.server.authorization import auth
from blacksheep import json, get, Request
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantAccountBalance
from sqlmodel import select, and_, desc, DefaultClause





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
            merchant_mature_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == merchantID,
                    MerchantAccountBalance.currency    == currency,
                    MerchantAccountBalance.is_mature   == True
                )
            ))
            merchant_mature_balance = merchant_mature_balance_obj.scalar()

            ## Get merchant Immature Account balance
            merchant_immature_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == merchantID,
                    MerchantAccountBalance.currency    == currency,
                    MerchantAccountBalance.is_mature   == False
                )
            ))
            merchant_immature_balance = merchant_immature_balance_obj.scalar()

            return json({
                'success': True,
                'mature_balance': merchant_mature_balance,
                'immature_balance': merchant_immature_balance
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)