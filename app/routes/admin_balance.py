from blacksheep.server.authorization import auth
from blacksheep import json, get, Request, post, put
from database.db import AsyncSession, async_engine
from Models.models import Users
from Models.models2 import MerchantAccountBalance, MerchantProdTransaction
from Models.Admin.PG.schema import MerchantBalancePeriodUpdateSchema
from sqlmodel import select, and_, desc
import re






## Get all the available balances of the merchant
@auth('userauth')
@get('/api/v7/admin/merchant/account/balance/')
async def merchant_account_balance(self, request: Request, id: int, currency: str):
    """
        Get mature and Immature balance of a merchant account.<br/><br/>

        Parameters:<br/>
            - id (int): Merchant ID<br/>
            - currency (str): Currency code<br/>
            - request (Request):  The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing mature and immature balance of the merchant account.<br/>
            - HTTP Status Code: 200 on success, 401 on unauthorized access.<br/><br/>

        Raises:<br/>
            - Exception: If any unexpected error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/><br/>
        
        Error Messages:<br/>
            - Unauthorized Access: If the user is not authorized to access the endpoint.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            merchantID = id

            # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            ## Get available mature balance of the merchant
            merchant__balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == merchantID,
                    MerchantAccountBalance.currency    == currency,
                )
            ))
            merchant__balance = merchant__balance_obj.scalar()

            return json({
                'success': True,
                'mature_balance': merchant__balance.mature_balance,
                'immature_balance': merchant__balance.immature_balance
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    





# Update Merchant settlement periods
@auth('userauth')
@put('/api/v7/admin/merchant/update/period/')
async def merchant_update_settlement_period(self, request: Request, schema: MerchantBalancePeriodUpdateSchema):
    """
        This API Endpoint let Admin user to update user's settlement period.<br/><br/>

        Parameters:<br/>
            schema (MerchantBalancePeriodUpdateSchema): Schema object with data for updating settlement period.<br/>
            request (Request): HTTP request object.<br/><br/>

        Returns:<br/>
            JSON response: Success message if update is successful, or error message if not.<br/>
            Error message: If any error occurs during update.<br/>
            HTTP Status Code: 200 if successful, 401 if authentication failed, or 400 if any error occurs.<br/>
            HTTP Status: 500 Internal Server Error if any error occurs during database operations.<br/><br/>

        Raises:<br/>
            - BadRequest: If any required data is missing or data format is incorrect.<br/>
            - Unauthorized: If user authentication failed.<br/>
            - SQLAlchemyError: If there is an error during database operations.<br/>
            - Exception: If any other unexpected error occurs during the database operations.<br/><br/>

        Error message:<br/>
            - Unauthorized: If user authentication failed.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            # # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            # Get payload data
            merchantID             = schema.merchant_id
            settlement_period      = schema.settlement_period
            minimum_withdrawal_amt = schema.minimum_withdrawal_amt
            
            # Get the merchant
            merchant_user_obj = await session.execute(select(Users).where(
                Users.id == int(merchantID)
            ))
            merchant_user = merchant_user_obj.scalar()
            
            # Get merchant settlement period
            numeric_settlement_period = re.findall(r'\d+', settlement_period)
            settlement_period_value    = numeric_settlement_period[0]

            merchant_user.settlement_period = settlement_period
            # merchant_user.settlement_date   = settlement_period_date
            merchant_user.minimum_withdrawal_amount = float(minimum_withdrawal_amt)

            session.add(merchant_user)
            await session.commit()
            await session.refresh(merchant_user)

            return json({
                'success': True,
                'message': 'Updated Successfully'
            }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    





## Get settlement period, Frozen balance by Admin
@auth('userauth')
@get('/api/v7/admin/merchant/balance/period/{user_id}/')
async def merchant_balance_period(self, request: Request, user_id: int):
    """
        This function retrieves the settlement period and minimum withdrawal balance of the merchant by admin.<br/><br/>
        
        Parameters:<br/>
            - request (Request): The incoming request object containing user identity.<br/>
            - user_id (int): The unique identifier of the merchant for which the balance is to be retrieved.<br/><br/>
        
        Returns:<br/>
            - JSON response with the settlement period and minimum withdrawal balance if the operation is successful.<br/>
            - JSON response with error message if the operation fails.<br/>
            - Error 401: 'Unauthorized'.<br/>
            - Error 404: 'Not Found'.<br/>
            - Error 500: 'Server Error'.<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
            - Error 401: 'Unauthorized'.<br/>
            - Error 404: 'Not Found'.<br/>
            - Error 500: 'Server Error'.<br/><br/>

        Error message:<br/>
            - Error 401: 'Unauthorized'.<br/>
            - Error 404: 'Not Found'.<br/>
            - Error 500: 'Server Error'.<br/>
        
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            admin_id      = user_identity.claims.get('user_id')

            # # Admin Authentication
            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({"message": 'Admin authentication failed'}, 401)
            # Admin authentication ends

            # Get minimum withdrawal amount of the merchant
            merchant_user_obj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            merchant_user = merchant_user_obj.scalar()

            minimum_withdrawal_amount = merchant_user.minimum_withdrawal_amount

            settlement_period = merchant_user.settlement_period

            return json({
                'success': True,
                'minimum_withdrawal_amount': minimum_withdrawal_amount,
                'settlement_period': settlement_period
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)