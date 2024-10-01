from app.controllers.controllers import get, post
from blacksheep import json, Request
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_, desc, func
from Models.models import Users
from Models.models4 import FiatWithdrawalTransaction




# Get all fiat withdrawal requests
class AdminAllWithdrawalTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "All Withdrawals"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/admin/fiat/withdrawals/'
    

    # Get all Fiat withdrawal requests
    @auth('userauth')
    @get()
    async def get_all_merchant_withdrawals(self, request: Request, limit: int = 10, offset: int = 0):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                admin_id       = user_identity.claims.get('user_id')

                #Authenticate Admin
                admin_user_obj = await session.execute(select(Users).where(
                        Users.id == admin_id
                ))
                admin_user = admin_user_obj.scalar()

                if not admin_user.is_admin:
                    return json({'message': 'Admin authentication Failed'}, 401)
                # Admin authentication ends

                # Get all the withdrawal transaction
                fiat_withdrawals_obj = await session.execute(select(FiatWithdrawalTransaction).order_by(
                    desc(FiatWithdrawalTransaction.id)
                ).limit(
                    limit
                ).offset(
                    offset
                ))
                fiat_withdrawals     = fiat_withdrawals_obj.scalars().all()

                if not fiat_withdrawals:
                    return json({'message': 'No transaction Found'}, 404)
                
                return json({
                    'success': True,
                    'all_admin_fiat_withdrawals': fiat_withdrawals
                }, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

