from blacksheep import get, json, Request
from blacksheep.server.authorization import auth
from Models.models import Users
from Models.models2 import MerchantProdTransaction, PIPE, MerchantPIPE
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_




# Get all collected Revenues
@auth('userauth')
@get('/api/v6/admin/revenues/')
async def GetAdminRevenues(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'message': 'Unauthorized access'}, 401)
            # Authentication ends here

            pipe_obj = await session.execute(select(PIPE))
            pipes    = pipe_obj.scalars().all()

            # Transactions related to every pipe\
            pipe_revenue_data = []

            for p in pipes:
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.pipe_id == p.id
                ))
                merchant_transactions = merchant_transaction_obj.scalars().all()

                currency_wise_transactions = {}
                
                for transaction in merchant_transactions:
                    currency = transaction.currency 
                    amount = transaction.amount if not transaction.is_refunded else -transaction.amount

                    if currency not in currency_wise_transactions:
                        currency_wise_transactions[currency] = 0

                    currency_wise_transactions[currency] += amount

                # pipe_total_transaction_amount = sum(transaction.amount if not transaction.is_refunded else
                #                             - transaction.amount for transaction in merchant_transactions)

                total_transaction_amounts = [
                    {'currency': currency, 'total_amount': total_amount}
                    for currency, total_amount in currency_wise_transactions.items()
                ]

                pipe_revenue_data.append({
                    'pipe_id': p.id,
                    'pipe_name': p.name,
                    'total_transaction_amount': total_transaction_amounts
                })

            return json({
                'success': True,
                'pipe_wise_transaction': pipe_revenue_data
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)







