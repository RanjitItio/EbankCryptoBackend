from blacksheep import get, Request, json
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantProdTransaction
from Models.models3 import MerchantRefund, MerchantWithdrawals
from sqlmodel import select, func



# Get The dashboard counts
@auth('userauth')
@get('/api/v2/admin/dashboard/counts/')
async def DashboardCounts(request: Request):
    """
        Count all the Production Transaction, Refunds, Withdrawals transactions.<br/>
        This endpoint is only accessible by admin users.<br/><br/>
        
        Parameters:<br/>
            - request (Request): The HTTP request object.<br/><br/>
        
        Returns:<br/>
            - JSON: A JSON response containing the counts of Production Transactions, Refunds, Withdrawals transactions.<br/>
            - HTTP Status Code: 200 in case of successful operation.<br/>
            - HTTP Status Code: 401 in case of unauthorized access.<br/>
            - HTTP Status Code: 500 in case of server errors.<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database operations.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authenticated.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Count all the available Merchant
            merchantUserObj = await session.execute(select(func.count(Users.id)).where(Users.is_merchent == True))
            merchantUsers   =  merchantUserObj.scalar()

            if not merchantUsers:
                merchantUsers = 0

            # Count all the Production Transactions
            merchantProdTransactionObj = await session.execute(select(func.count(MerchantProdTransaction.id)))
            merchantProdTransactions   = merchantProdTransactionObj.scalar()

            if not merchantProdTransactions:
                merchantProdTransactions = 0

            # Count all the Refunds
            merchantRefundTransactionObj = await session.execute(select(func.count(MerchantRefund.id)))
            merchantRefundTransaction    = merchantRefundTransactionObj.scalar()

            if not merchantRefundTransaction:
                merchantRefundTransaction = 0

            # Count all Withdrawals
            merchantWithdrawalTransactionsObj = await session.execute(select(func.count(MerchantWithdrawals.id)))
            merchantWithdrawalTransactions    = merchantWithdrawalTransactionsObj.scalar()

            if not merchantWithdrawalTransactions:
                merchantWithdrawalTransactions = 0

            return json({
                'success': True, 
                'merchant_users': merchantUsers,
                'prod_transactions': merchantProdTransactions,
                'refunds': merchantRefundTransaction,
                'withdrawals': merchantWithdrawalTransactions
                }, 200)
              
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)