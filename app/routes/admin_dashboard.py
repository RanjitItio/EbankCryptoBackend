from blacksheep import json, Request, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantProdTransaction, PIPE
from sqlmodel import select, and_, func




# Pipe transactions in Admin dashboard  
@auth('userauth')
@get('/api/v6/admin/dash/pipe/transactions/')
async def Admin_dashPipeTransactions(self, request: Request, currency: str = 'USD'):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id')

            # Admin authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization failed'}, 401)
            # Admin authentication ends here

            # Get Transactions for every pipe
            stmt = select(
                MerchantProdTransaction.currency,
                func.sum(MerchantProdTransaction.amount).label('total_amount'),
                PIPE.name.label('pipe_name')

                ).join(
                    PIPE, PIPE.id == MerchantProdTransaction.pipe_id
                ).where(
                    and_(
                     MerchantProdTransaction.status == 'PAYMENT_SUCCESS',
                     MerchantProdTransaction.currency == currency
                )).group_by(
                    PIPE.name, MerchantProdTransaction.currency
                )   
            
            transaction_obj = await session.execute(stmt)
            all_pipe_transactions = transaction_obj.all()

            transaction_list = []
        
            for row in all_pipe_transactions:
                transaction_list.append({
                    "total_amount": row.total_amount,
                    "currency": row.currency,
                    "pipe_name": row.pipe_name
                })

            return json({'success': True, 'pipe_transactions': transaction_list}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)