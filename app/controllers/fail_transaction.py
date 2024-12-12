from blacksheep.server.controllers import APIController
from app.controllers.controllers import get 
from blacksheep import Request, json
from sqlmodel import select, and_
from database.db import AsyncSession, async_engine
from Models.models2 import MerchantProdTransaction
from Models.models import UserKeys




### Fail a transaction if timer Completed
class FailProdTransactionController(APIController):

    @classmethod
    def class_name(cls):
        return 'Failed A Prod Transaction'
    
    @classmethod
    def route(cls):
        return '/api/v5/fail/prod/transaction/{transaction_id}/{public_key}'
    

    @get()
    async def post(self, request: Request, transaction_id: str, public_key: str):
        try:
            async with AsyncSession(async_engine) as session:
                    transaction_id = transaction_id
                    public_key     = public_key
                    
                    merchant_key_obj = await session.execute(select(UserKeys).where(
                        UserKeys.public_key == public_key
                    ))
                    merchant_key = merchant_key_obj.scalar()

                    ### Get the transaction of the user
                    merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                         and_(
                              MerchantProdTransaction.transaction_id == transaction_id,
                              MerchantProdTransaction.merchant_id     == merchant_key.user_id
                              )
                    ))
                    merchant_prod_transaction = merchant_prod_transaction_obj.scalar()

                    if not merchant_prod_transaction:
                         return json({'error': 'Transaction Not Found'}, 404)
                    
                    merchant_prod_transaction.status = "PAYMENT_FAILED"
                    merchant_prod_transaction.is_completd = False

                    session.add(merchant_prod_transaction)
                    await session.commit()
                    await session.refresh(merchant_prod_transaction)

                    return json({'message': 'Transaction Failed Successfully'}, 200)
        
        except Exception as e:
            return json({'error': 'Server Error', 'message': str(e)}, 500)
