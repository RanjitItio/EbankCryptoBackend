from blacksheep import Request, json
from blacksheep.server.controllers import APIController
from blacksheep.server.authorization import auth
from Models.models2 import MerchantAccountBalance
from Models.models2 import MerchantProdTransaction
from database.db import AsyncSession, async_engine
from app.controllers.controllers import get
from sqlmodel import select, and_
from datetime import datetime




#############################
## Merchant Account Balance 
#############################
class MerchantAccountBalanceController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Account Balance'

    @classmethod
    def route(cls) -> str | None:
        return '/api/v5/merchant/account/balance/'
    

    @auth('userauth')
    @get()
    async def get_merchantAccountBalance(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                # Authenticate User
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id') if user_identity else None
                
                if user_id is None:
                    return json({'error': 'Unauthorized'}, 401)
                
                currenct_datetime =  datetime.now()

                # Get all the transactions related to the merchant
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.merchant_id == user_id,
                        MerchantProdTransaction.status == 'PAYMENT_SUCCESS'
                    )
                ))
                merchant_prod_transaction = merchant_prod_transaction_obj.scalars().all()

                # Check the which transactions related to merchant has been matured
                if merchant_prod_transaction:
                    for transaction in merchant_prod_transaction:
                        if transaction.pg_settlement_date:
                            if transaction.pg_settlement_date < currenct_datetime and transaction.balance_status == 'Immature':
                                # Get the account balance of the merchant
                                merchant_account_balance_Obj = await session.execute(select(MerchantAccountBalance).where(
                                and_(
                                    MerchantAccountBalance.merchant_id == user_id,
                                    MerchantAccountBalance.currency    == transaction.currency
                                    )
                                ))
                                merchant_account_balance = merchant_account_balance_Obj.scalar()

                                charged_fee = (transaction.amount / 100) * transaction.transaction_fee
                                merchant__balance = transaction.amount - charged_fee
                                
                                if merchant_account_balance:
                                    # Update the mature and immature balance
                                    merchant_account_balance.immature_balance -= merchant__balance
                                    merchant_account_balance.mature_balance   += merchant__balance

                                    transaction.balance_status = 'Mature'

                                    session.add(merchant_account_balance)
                                    session.add(transaction)
                                    await session.commit()
                                    await session.refresh(merchant_account_balance)
                                    await session.refresh(transaction)

                ## Get merchant Account Balance
                merchantBalanceObj = await session.execute(select(MerchantAccountBalance).where(
                    MerchantAccountBalance.merchant_id == user_id
                ))
                merchantBalance = merchantBalanceObj.scalars().all()

                if not merchantBalance:
                    return json({'error': 'No Merchant Balance availabel'}, 404)
                
                return json({'success': True, 'merchantAccountBalance': merchantBalance}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500) 



