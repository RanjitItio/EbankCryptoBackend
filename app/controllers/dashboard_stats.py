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
    """
        This function retrieves and calculates various statistics for a merchant's dashboard.<br/>
        Which Include refunds, Account balances, Mature balance, Immature balance, Withdrawal balance, Pending withdrawal balance.<br/><br/>
    
        Parameters:<br/>
            - request (Request): The request object containing user identity and other relevant information.<br/>
            - currency (str): The currency for which the statistics are to be retrieved.<br/><br/>
    
        Returns:<br/>
            - json: A JSON response containing success status(200), and the statistics data(stats_data).<br/>
            - JSON: A JSON response containing error status and error message if any.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/><br/>
        
        Error messages:<br/>
            - Unauthorized: If the user is not authenticated.<br/>
            - Server Error: If an error occurs while executing the database query.<br/>
            - Error 401: Unauthorized Access<br/>
            - Error 500: Server Error<br/>
    """
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
            total_merchant_withdrawals               = sum(withdrawals.amount for withdrawals in merchant_withdrawal_requests)
            total_merchant_refunds                   = sum(refunds.amount for refunds in merchant_refund_requests)
            total_merchant_account_balance           = sum(balance.account_balance for balance in merchant_account_balance if balance.account_balance is not None)
            total_merchant_mature_balance            = sum(balance.mature_balance for balance in merchant_account_balance if balance.mature_balance is not None)
            total_merchant_immature_balance          = sum(balance.immature_balance for balance in merchant_account_balance if balance.immature_balance is not None)
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
                'merchant_mature_balance': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_mature_balance
                }],
                'merchant_immature_balance': [{
                    'currency': currency_name.name,
                    'amount':   total_merchant_immature_balance
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
async def get_merchantRecentTransactions(request: Request):
    """
        This API endpoint is used to get recent transactions made by a merchant.<br/><br/>

        Parameters:<br/>
            - request (Request): Request object<br/>
            - limit (int, optional): Number of transactions to return. Default is 5.<br/>
            - offset (int, optional): Offset for pagination. Default is 0.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the success status and recent transactions(recent_transactions).<br/>
            - HTTP Status Code: 200 if successful, 401 if the user is not authenticated, or 500 if an error occurs.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authenticated.<br/>
            - Server Error: If an error occurs during the database operations.<br/><br/>

        Raises:<br/>
            - HTTPException: If the request payload is invalid or if the user is not authenticated.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs.<br/>
    """
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
    """
        This function retrieves and calculates the total amounts of success transactions, withdrawals, and refunds for a merchant.
        It can filter the results based on a specified currency.<br/><br/>

        Parameters:<br/>
            - request (Request): The request object containing user identity and other relevant information.<br/>
            - currency (str, optional): The currency for which the transactions need to be filtered. If not provided, all currencies are considered.<br/><br/>

        Returns:<br/>
            - JSON response containing the total amounts of success transactions, withdrawals, and refunds.<br/>
            - If an exception occurs during the process, it returns a JSON response with an error message.<br/><br/>

        Error Messages:<br/>
            Error response status 500 - 'error': 'Server error'.<br/>
            Error response status 400 - 'error': 'Invalid request data'.<br/><br/>

        Raises:<br/>
            - Exception: If any error occurs during the database operations or processing.<br/>
    """
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
    
