from blacksheep import json, Request, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantProdTransaction, PIPE
from Models.models3 import MerchantWithdrawals
from sqlmodel import select, and_, func
from datetime import datetime, timedelta




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
    


# Dashboard Income and Outcome
@auth('userauth')
@get('/api/v6/admin/dash/income/stats/')
async def Dashboard_Income_Outcome(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user as admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authentication failed'}, 401)
            # Admin authentication ends here

            # Get the start (Sunday) and end (Saturday) of the current week
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday() + 1)
            end_of_week = start_of_week + timedelta(days=6)

            # Get all the success transactions grouped by day of the week within the current week
            success_transactions_by_day_obj = await session.execute(
                select(
                    func.date_part('dow', MerchantProdTransaction.createdAt).label('day_of_week'),
                    func.sum(MerchantProdTransaction.amount).label('total_amount')
                ).where(
                    and_(
                        MerchantProdTransaction.status == 'PAYMENT_SUCCESS',
                        MerchantProdTransaction.is_completd == True,
                        MerchantProdTransaction.createdAt.between(start_of_week, end_of_week)
                    )
                ).group_by('day_of_week')
            )
            success_transactions_by_day = success_transactions_by_day_obj.fetchall()

            # Get all the withdrawals grouped by day of the week within the current week
            withdrawal_transactions_by_day_obj = await session.execute(
                select(
                    func.date_part('dow', MerchantWithdrawals.createdAt).label('day_of_week'),
                    func.sum(MerchantWithdrawals.amount).label('total_amount')
                ).where(
                    and_(
                        MerchantWithdrawals.status == 'Approved',
                        MerchantWithdrawals.createdAt.between(start_of_week, end_of_week)
                    )
                ).group_by('day_of_week')
            )
            withdrawal_transactions_by_day = withdrawal_transactions_by_day_obj.fetchall()

            # Create a mapping of day numbers to names (0 = Sunday, 6 = Saturday)
            day_mapping = {
                0: 'Sunday',
                1: 'Monday',
                2: 'Tuesday',
                3: 'Wednesday',
                4: 'Thursday',
                5: 'Friday',
                6: 'Saturday'
            }

            # Map results to days of the week for success transactions
            success_by_day = {day_mapping[int(row[0])]: row[1] for row in success_transactions_by_day}

            # Map results to days of the week for withdrawal transactions
            withdrawal_by_day = {day_mapping[int(row[0])]: row[1] for row in withdrawal_transactions_by_day}

            return json({
                'success': True,
                'success_transactions_by_day': success_by_day,
                'withdrawal_transactions_by_day': withdrawal_by_day
            }, 200)
        
    except Exception as e:  
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)