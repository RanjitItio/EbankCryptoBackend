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

            stmt = select(
                MerchantProdTransaction.id,
                MerchantProdTransaction.merchant_id,
                MerchantProdTransaction.transaction_fee,
                MerchantProdTransaction.is_refunded,
                MerchantProdTransaction.is_completd,
                MerchantProdTransaction.status,
                MerchantProdTransaction.amount.label('transaction_amount'),
                MerchantProdTransaction.payment_mode,
                MerchantProdTransaction.transaction_id,

                PIPE.id.label('geteway_id'),
                PIPE.name.label('pipe_name')
            ).join(
                PIPE, PIPE.id == MerchantProdTransaction.pipe_id
            ).where(
                and_(MerchantProdTransaction.status == 'PAYMENT_SUCCESS',
                     MerchantProdTransaction.is_refunded == False)
                )

            # Get all the success production transactions
            successTransactionsObj = await session.execute(stmt)
            successTransactions    = successTransactionsObj.fetchall()

            pipe_wise_transactions = {}

            for transaction in successTransactions:
                pipe_name = transaction.pipe_name

                if pipe_name not in pipe_wise_transactions:
                    pipe_wise_transactions[pipe_name] = {
                        'total_revenue': 0,
                        'gateway_id': [],
                        'pipe_name': [],
                    }

                pipe_wise_transactions[pipe_name]['total_revenue'] += transaction.transaction_fee
                pipe_wise_transactions[pipe_name]['gateway_id'] = transaction.geteway_id
                pipe_wise_transactions[pipe_name]['pipe_name'] = transaction.pipe_name

                # pipe_wise_transactions[pipe_name]['transactions'].append({
                #     'id': transaction.id,
                #     'merchant_id': transaction.merchant_id,
                #     'transaction_fee': transaction.transaction_fee,
                #     'is_refunded': transaction.is_refunded,
                #     'is_completd': transaction.is_completd,   
                #     'status': transaction.status,
                #     'transaction_amount': transaction.transaction_amount,
                #     'geteway_id': transaction.geteway_id,
                # })

            return json({
                'success': True,
                'pipe_wise_transactions': pipe_wise_transactions
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)







