from blacksheep import json, get, Request
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_
from Models.models import Users
from Models.models2 import MerchantAccountBalance




# Get merchant Account balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/account/balance/{user_id}/')
async def merchant_account_balance(request: Request, user_id: int, currency: str = None):
    """
        Get all the balances for merchant account including mature, Immature, frozen.<br/><br/>

        Parameters:<br/>
            - user_id (int): User ID<br/>
            - currency (str): Currency name<br/>
            - request (Request):  The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the balances of the merchant account.<br/>
            - HTTP Status Code: 200 on success, 401 on unauthorized access.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/><br/>
        
        Raises:<br/>
            - Exception: If any unexpected error occurs during the database query or response generation.<br/><br/>
        
        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')\
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends
            # Get the account balance of the user
            if currency:
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(
                        MerchantAccountBalance.merchant_id == user_id,
                        MerchantAccountBalance.currency    == currency
                        )
                    ))
                merchant_account_balance = merchant_account_balance_obj.scalar()

            else:
                merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                    and_(
                        MerchantAccountBalance.merchant_id == user_id,
                        MerchantAccountBalance.currency    == 'USD'
                        )
                    ))
                merchant_account_balance = merchant_account_balance_obj.scalar()

            return json({
                'success': True,
                'merchant_balance_data': merchant_account_balance
            }, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)




# Get matured balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/mature/account/balance/{user_id}/')
async def merchant_mature_account_balance(request: Request, user_id: int, currency: str):
    """
        Get the mature account balance of a merchant.<br/><br/>

        Parameters:<br/>
            - user_id (int): User ID<br/>
            - currency (str): Currency code<br/>
            - request (Request):  The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the mature account balance of the merchant(merchant_mature_balance).<br/>
            - HTTP Status Code: 200 on success, 401 on unauthorized access.<br/><br/>

        Raises:<br/>
            - Exception: If any unexpected error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/><br/>

        Error Messages:<br/>
            - Unauthorized Access: If the user is not authorized to access the endpoint.<br/>
            - Server Error: If an error occurs while executing the database query.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_mature_account_balance = merchant_account_balance.mature_balance
                
            else:
                merchant_mature_account_balance = 0

            return json({
                'success': True,
                'merchant_mature_balance': merchant_mature_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    




@auth('userauth')
@get('/api/v4/admin/merchant/frozen/account/balance/{user_id}/')
async def merchant_frozen_account_balance(request: Request, user_id: int, currency: str):
    """
        Get the frozen balance of a user's account.<br/><br/>

        Parameters:<br/>
            - user_id (int): User ID<br/>
            - currency (str): Currency code<br/>
            - request (Request):  The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the frozen balance of the user's account(merchant_frozen_balance).<br/>
            - HTTP Status Code: 200 on success, 401 on unauthorized access.<br/><br/>

        Raises:<br/>
            - Exception: If any unexpected error occurs during the database query or response generation.<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/><br/>
        
        Error Messages:<br/>
            - Error 401: 'error': 'Unauthorized Access'.<br/>
            - Error 500: 'error': 'Server Error'.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_frozen_account_balance = merchant_account_balance.frozen_balance
            else:
                merchant_frozen_account_balance = 0

            return json({
                'success': True,
                'merchant_frozen_balance': merchant_frozen_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
    





# Get immatured balance by Admin
@auth('userauth')
@get('/api/v4/admin/merchant/immature/account/balance/{user_id}/')
async def merchant_immature_account_balance(request: Request, user_id: int, currency: str):
    """
        Get the immature balance of a merchant account by admin.<br/><br/>

        Parameters:<br/>
            user_id (int): Merchant ID<br/>
            currency (str): Currency Name<br/>
            request (Request):  The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the immature balance of the merchant account.<br/>
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
            admin_identity = request.identity
            admin_id       = admin_identity.claims.get('user_id')
            
            user_id = user_id

            admin_user_obj = await session.execute(select(Users).where(
                Users.id == admin_id
            ))
            admin_user = admin_user_obj.scalar()

            if not admin_user.is_admin:
                return json({'message': 'Admin authorization Failed'}, 401)
            # Admin authentication ends

            # Get the account balance of the user
            merchant_account_balance_obj = await session.execute(select(MerchantAccountBalance).where(
                and_(
                    MerchantAccountBalance.merchant_id == user_id,
                    MerchantAccountBalance.currency    == currency
                    )
                ))
            merchant_account_balance = merchant_account_balance_obj.scalar()

            if merchant_account_balance:
                merchant_immature_account_balance = merchant_account_balance.immature_balance
            else:
                merchant_immature_account_balance = 0

            return json({
                'success': True,
                'merchant_immature_balance': merchant_immature_account_balance
            }, 200)
    
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
