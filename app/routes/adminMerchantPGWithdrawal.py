from blacksheep import Request, json, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantWithdrawals
from Models.models import MerchantBankAccount
from Models.models import Users, Currency
from sqlmodel import select, and_




@auth('userauth')
@get('/api/v4/admin/merchant/pg/withdrawals/')
async def AdminMerchantWithdrawalRequests(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            if not is_admin_user:
                return json({'error': 'Admin authentication failed'}, 401)
            # Admin authentication Ends

            # Get all the merchant withdrawals
            merchant_withdrawals_object = await session.execute(select(MerchantWithdrawals))
            merchant_withdrawals = merchant_withdrawals_object.scalars().all()

            for withdrawals in merchant_withdrawals:
                    # Get the bank account linked to the merchant
                    merchant_bank_account_obj = await session.execute(select(MerchantBankAccount).where(
                        MerchantBankAccount.id == withdrawals.bank_id
                    ))
                    merchant_bank_account = merchant_bank_account_obj.scalar()

                    # Get the withdrawal currency and Bank Currecy
                    merchant_withdrawal_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.currency
                    ))
                    merchant_withdrawal_currency = merchant_withdrawal_currency_obj.scalar()

                    # Get the merchant Bank Currency
                    merchant_bank_currency_obj = await session.execute(select(Currency).where(
                        Currency.id == withdrawals.bank_currency
                    ))
                    merchant_bank_currency = merchant_bank_currency_obj.scalar()

                    # Get the merchant
                    merchant_user_obj = await session.execute(select(Users).where(
                         Users.id == withdrawals.merchant_id
                    ))
                    merchant_user = merchant_user_obj.scalar()

                    combined_data.append({
                        'id': withdrawals.id,
                        'merchant_id': withdrawals.merchant_id,
                        'merchant_name': merchant_user.full_name,
                        'merchant_email': merchant_user.email,
                        'bank_account': merchant_bank_account.bank_name,
                        'withdrawalAmount': withdrawals.amount,
                        'withdrawalCurrency': merchant_withdrawal_currency.name,
                        'bankCurrency': merchant_bank_currency.name,
                        'createdAt': withdrawals.createdAt,
                        'status':   withdrawals.status,
                        'is_active': withdrawals.is_active
                    })


            return json({'success': True, 'AdminMerchantWithdrawalRequests': combined_data}, 200)

            
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)

