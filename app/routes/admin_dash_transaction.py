from blacksheep import Request, json, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models2 import MerchantProdTransaction
from Models.models import Users
from sqlmodel import select, and_





# Get All the success Transaction Amount  
@auth('userauth')
@get('/api/v3/admin/merchant/success/transactions/')
async def AdminDashTransactionAmount(self, request: Request):
    """
        Get sum of all the success transaction amount of three currencies.<br/>
        Authenticate admin user before fetching the data.<br/><br/>

        Parameters:<br/>
            - request: HTTP Request object.<br/><br/>

        Returns:<br/>
            JSON response with success message and transaction data.<br/>
            success(boolean): if successful.<br/>
            usd_balance(float): Total USD balance.<br/>
            eur_balance(float): Total EUR balance.<br/>
            inr_balance(float): Total INR balance.<br/><br/>

        Raises:<br/>
            - JSON response with error message if any error occurs while fetching data.<br/>
            - JSON response with error message if user is not authenticated.<br/><br/>

        Error Message:<br/>
            - ValueError: If the input data is not valid.<br/>
            - Exception: If there is an error while executing the SQL queries.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            #Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            admin_user = admin_user_obj.scalar()

            is_admin_user = admin_user.is_admin

            # If not admin user
            if not is_admin_user:
                return json({'message': 'Only Admin users'}, 400)
            
            # fetch all the transactions
            merchant_transactions_object = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.is_completd == True
                    )
            )
            merchant_transactions = merchant_transactions_object.scalars().all()

            if not merchant_transactions:
                return json({'error': 'No transaction available'}, 404)

            # Calculate all the amount currency wise
            usd_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'USD')
            euro_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'EUR')
            inr_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'INR')
            gbp_balance = sum(trans.amount for trans in merchant_transactions if trans.currency == 'GBP')

            return json({
                'success': True, 
                'usd_balance': usd_balance if usd_balance else 0,
                'euro_balance': euro_balance if euro_balance else None,
                'inr_balance': inr_balance if inr_balance else None,
                'gbp_balance': gbp_balance if gbp_balance else None,
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)