from blacksheep import get, post, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantProdTransaction, MerchantSandBoxTransaction
from sqlmodel import select



# Get all the merchant production transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/transactions/')
async def get_merchant_pg_transaction(request: Request, limit : int = 25, offset : int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Admin Authentication
            admin_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin = admin_object.scalar()

            is_admin_user = admin.is_admin

            if not is_admin_user:
                return json({'error': 'Unauthorized Access'}, 403)
            
            # Get all the Production transactions
            merchant_transactions_obj = await session.execute(select(MerchantProdTransaction).order_by(
                (MerchantProdTransaction.id).desc()
            ).limit(limit).offset(offset))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL': transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                    'is_completed':          transactions.is_completd
                })

            return json({'success': True, 'message': 'Transaction fetched successfuly', 'AdminmerchantPGTransactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
    


# Get all the merchant sandbx transactions by Admin
@auth('userauth')
@get('/api/v2/admin/merchant/pg/sandbox/transactions/')
async def get_merchant_pg_sandbox_transaction(request: Request, limit : int = 25, offset : int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Admin Authentication
            admin_object = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin = admin_object.scalar()

            is_admin_user = admin.is_admin

            if not is_admin_user:
                return json({'error': 'Unauthorized Access'}, 403)
            
            # Get all the Production transactions
            merchant_transactions_obj = await session.execute(select(MerchantSandBoxTransaction).order_by(
                (MerchantSandBoxTransaction.id).desc()
            ).limit(limit).offset(offset))
            merchant_transactions = merchant_transactions_obj.scalars().all()

            # get the user id
            user_obj = await session.execute(select(Users))
            users    = user_obj.scalars().all()

            # User data dictionary
            users_dict = {user.id: user for user in users}

            for transactions in merchant_transactions:
                user_id = users_dict.get(transactions.merchant_id)

                # All the transaction inside the combined_data
                combined_data.append({
                    'id': transactions.id,
                    'merchant': {
                        'merchant_id': user_id.id,
                        'merchant_name': user_id.full_name
                    },
                    # 'gatewayRes': transactions.gateway_res,
                    'payment_mode': transactions.payment_mode,
                    'transaction_id': transactions.transaction_id,
                    'currency': transactions.currency,
                    'status':   transactions.status,
                    'amount':   transactions.amount,
                    'createdAt': transactions.createdAt,
                    'merchantOrderId': transactions.merchantOrderId,
                    'merchantRedirectURl': transactions.merchantRedirectURl,
                    'merchantCallBackURL': transactions.merchantCallBackURL,
                    'merchantMobileNumber': transactions.merchantMobileNumber,
                    'merchantPaymentType':  transactions.merchantPaymentType,
                    'is_completed':          transactions.is_completd
                })

            return json({'success': True, 'message': 'Transaction fetched successfuly', 'AdminmerchantPGSandboxTransactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)