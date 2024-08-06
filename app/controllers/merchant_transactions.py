from app.controllers.controllers import get
from blacksheep import Request, json
from database.db import AsyncSession, async_engine
from blacksheep.server.controllers import APIController
from Models.models2 import MerchantProdTransaction, MerchantSandBoxTransaction
from sqlmodel import select, and_
from blacksheep.server.authorization import auth
from datetime import datetime, timedelta



# All transactions made by merchant in production
class MerchantProductionTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Production Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/prod/transactions/'
    
   
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request, limit: int = 10, offset: int = 0):
        # Authenticcate users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # fetch all the transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.merchant_id == user_id
                ).order_by(MerchantProdTransaction.id.desc()).limit(limit).offset(offset)
            )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)
                
                return json({'msg': 'Success', 'merchant_prod_trasactions': merchant_transactions}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        


# All transactions made by merchant in production without limit
class MerchantAllProductionTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant All Production Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/all/prod/transactions/'
    

    @auth('userauth')
    @get()
    async def get_all_transactions(self, request: Request):
        # Authenticate users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(seconds=1)

        try:
            async with AsyncSession(async_engine) as session:

                # Fetch transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.merchant_id == user_id,
                         MerchantProdTransaction.createdAt >= start_of_month,
                         MerchantProdTransaction.createdAt <= end_of_month
                         )
                )
            )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)
                
                return json({'msg': 'Success', 'merchant_all_prod_trasactions': merchant_transactions}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        



# All transactions made by merchant in Sandbox mode
class MerchantSandboxTransactions(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Sandbox Transactions'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/sandbox/transactions/'
    
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request, limit: int = 10, offset: int = 0):
        # Authenticate Users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # Fetch transactions
                merchant_transactions_object = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchant_id == user_id
                ).order_by(MerchantSandBoxTransaction.id.desc()).limit(limit).offset(offset)
            )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)

                return json({'msg': 'Success', 'merchant_sandbox_trasactions': merchant_transactions}, 200)

        except Exception as e:
            return json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        


# Get Account balance of the Merchant
class MerchantAccountBalance(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Account Balace'
    
    @classmethod
    def route(cls) -> str:
        return '/api/v2/merchant/account/balance/'
    
    @auth('userauth')
    @get()
    async def get_transactions(self, request: Request):
        # Authenticate Users
        user_identity = request.identity
        user_id       = user_identity.claims.get('user_id') if user_identity else None

        try:
            async with AsyncSession(async_engine) as session:

                # fetch all the transactions
                merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.merchant_id == user_id,
                         MerchantProdTransaction.is_completd == True,
                         )
                    )
                )
                merchant_transactions = merchant_transactions_object.scalars().all()

                if not merchant_transactions:
                    return json({'error': 'No transaction available'}, 404)

                # Calculate all the amount currency wise
                usd_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'USD')
                euro_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'EUR')
                inr_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'INR')

                return json({
                        'success': True, 
                        'usd_balance': usd_balance if usd_balance else 0,
                        'euro_balance': euro_balance if euro_balance else None,
                        'inr_balance': inr_balance if inr_balance else None,
                        }, 200)
            
        except Exception as e:
            return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)