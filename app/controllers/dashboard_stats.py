from blacksheep import json, get, Request
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Currency
from Models.models2 import MerchantAccountBalance, MerchantProdTransaction
from Models.models3 import MerchantWithdrawals, MerchantRefund
from sqlmodel import select, and_, desc




# Get the stats of Merchant dashboard section
@auth('userauth')
@get('/api/v6/merchant/dash/stats/{currency}')
async def get_merchantDashStats(request: Request, currency: str):
    try:
        async with AsyncSession(async_engine) as session:
            #Authenticate user
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            # Get currency id
            currency_obj =  await session.execute(select(Currency).where(
                Currency.name == currency
            ))
            currency_name = currency_obj.scalar()

            if not currency_name:
                return json({'message': 'Invalid Currency'}, 400)


            # Get the merchant account balance
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(MerchantAccountBalance.merchant_id == user_id,
                     MerchantAccountBalance.currency    == currency
                     )
            ))
            merchant_account_balance = merchant_account_balance_obj.scalars().all()

            # Get merchant withdrawals
            merchant_withdrawal_requests_obj = await session.execute(select(MerchantWithdrawals).where(
                and_(
                    MerchantWithdrawals.merchant_id == user_id,
                    MerchantWithdrawals.currency    == currency_name.id,
                    MerchantWithdrawals.is_completed == True
                    )
                ))
            merchant_withdrawal_requests = merchant_withdrawal_requests_obj.scalars().all()


            # Get merchant pending withdrawals
            merchant_pending_withdrawal_requests_obj = await session.execute(select(MerchantWithdrawals).where(
                and_(
                    MerchantWithdrawals.merchant_id == user_id,
                    MerchantWithdrawals.currency    == currency_name.id,
                    MerchantWithdrawals.status      == 'Pending'
                    )
            ))
            merchant_pending_withdrawal_requests = merchant_pending_withdrawal_requests_obj.scalars().all()

            # Get merchant Refunds
            merchant_refund_requests_obj = await session.execute(select(MerchantRefund).where(
                and_(
                    MerchantRefund.merchant_id == user_id,
                    MerchantRefund.currency == currency_name.id
                 )
            ))
            merchant_refund_requests = merchant_refund_requests_obj.scalars().all()


            # Count total amount for all the requests
            total_merchant_withdrawals     = sum(withdrawals.amount for withdrawals in merchant_withdrawal_requests)
            total_merchant_refunds         =  sum(refunds.amount for refunds in merchant_refund_requests)
            total_merchant_account_balance = sum(balance.amount for balance in merchant_account_balance)
            total_merchant_pending_withdrawal_amount = sum(pending.amount for pending in merchant_pending_withdrawal_requests)

            combined_data = []

            # Store data inside a list
            combined_data.append({
                'merchant_refunds': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_refunds
                }],
                'merchant_account_balance': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_account_balance
                }],
                'merchant_withdrawals': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_withdrawals
                }],
                'merchant_pending_withdrawals': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_pending_withdrawal_amount
                }],
            })
            
            return json({'success': True, 'stats_data': combined_data}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)





# Get recent 15 merchant Transactions
@auth('userauth')
@get('/api/v6/merchant/recent/transactions/')
async def get_merchantDashStats(request: Request):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            # Get last 15 transactions
            merchant_recent_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                MerchantProdTransaction.merchant_id == user_id
            ).order_by(desc(MerchantProdTransaction.id)).limit(5))

            merchant_recent_transaction = merchant_recent_transaction_obj.scalars().all()

            combined_data = []

            for transaction in merchant_recent_transaction:
                combined_data.append({
                    'id': transaction.id,
                    'transaction_id': transaction.transaction_id,
                    'currency': transaction.currency,
                    'status': transaction.status,
                    'transaction_amount': transaction.amount,
                    'createdAt': transaction.createdAt,
                    'merchantOrderID': transaction.merchantOrderId,
                    'is_completed': transaction.is_completd,
                    'transaction_fee': transaction.transaction_fee,
                    'business_name': transaction.business_name
                })

            return json({'success': True, 'recent_transactions': combined_data}, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    


# Merchant dashboard success transaction and withdrawal transaction chart
@auth('userauth')
@get('/api/v6/merchant/dash/transaction/withdrawal/refund/chart/')
async def merchant_dashboardTransactionWithdrawalChart(request: Request, currency: str = None):
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate user
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            if currency:
                # Get the Currency ID
                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == currency
                ))
                req_currency = currency_obj.scalar()

                # Get all the merchant success transactions
                merchant_success_transactions_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.merchant_id == user_id,
                        MerchantProdTransaction.status      == 'PAYMENT_SUCCESS',
                        MerchantProdTransaction.currency    == req_currency.name
                    )
                ))
                merchant_success_transaction = merchant_success_transactions_obj.scalars().all()

                # Get all the merchant withdrawals
                merchant_success_withdrawals_obj = await session.execute(select(MerchantWithdrawals).where(
                    and_(
                        MerchantWithdrawals.merchant_id == user_id,
                        MerchantWithdrawals.status == 'Approved',
                        MerchantWithdrawals.currency == req_currency.id
                    )
                ))
                merchant_success_withdrawals = merchant_success_withdrawals_obj.scalars().all()

                # Get all the merchant success Refunds
                merchant_success_refund_obj = await session.execute(select(MerchantRefund).where(
                    and_(
                        MerchantRefund.merchant_id == user_id,
                        MerchantRefund.is_completed == True,
                        MerchantRefund.currency     == req_currency.id
                    )
                ))
                merchant_success_refunds = merchant_success_refund_obj.scalars().all()

            else:
                # Get all the merchant success transactions
                merchant_success_transactions_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.merchant_id == user_id,
                        MerchantProdTransaction.status      == 'PAYMENT_SUCCESS'
                    )
                ))
                merchant_success_transaction = merchant_success_transactions_obj.scalars().all()

                # Get all the merchant withdrawals
                merchant_success_withdrawals_obj = await session.execute(select(MerchantWithdrawals).where(
                    and_(
                        MerchantWithdrawals.merchant_id == user_id,
                        MerchantWithdrawals.status == 'Approved'
                    )
                ))
                merchant_success_withdrawals = merchant_success_withdrawals_obj.scalars().all()

                # Get all the merchant success Refunds
                merchant_success_refund_obj = await session.execute(select(MerchantRefund).where(
                    and_(
                        MerchantRefund.merchant_id == user_id,
                        MerchantRefund.is_completed == True
                    )
                ))
                merchant_success_refunds = merchant_success_refund_obj.scalars().all()


            total_success_transaction_amount    = sum(transaction.amount for transaction in merchant_success_transaction)
            total_withdrawal_transaction_amount = sum(withdrawal.amount for withdrawal in merchant_success_withdrawals)
            total_refund_transaction_amount     = sum(refund.amount for refund in merchant_success_refunds)


            return json({
                'success_transaction': total_success_transaction_amount,
                'withdrawal_amount': total_withdrawal_transaction_amount,
                'refund_amount': total_refund_transaction_amount
            }, 200)

    except Exception as e:
        return json({'error': 'Server error', 'message': f'{str(e)}'}, 500)
    
