from blacksheep import Request, json, pretty_json
from blacksheep import post
from database.db import AsyncSession, async_engine
from blacksheep.server.authorization import auth
from sqlmodel import select
from Models.models import Users, Wallet
from Models.Admin.User.schemas import EachUserWalletSchema



    
 
@auth('userauth')
@post('/api/v2/admin/user/wallet/')
async def user_wallets(self, request: Request, schema: EachUserWalletSchema):
    """
        This API Endpoint list all the available wallet of users.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming request object containing user identity.<br/>
            - schema (EachUserWalletSchema): The schema for validating the incoming request data.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the status of the operation and the list of wallets if successful.<br/>
            - HTTP Status Code: 200 if successful, 400 if invalid request data, or 500 if an error occurs.<br/>
            - Unauthorized: If the user is not authenticated or not admin.<br/>
            - Server Error: If an error occurs during the database operations.<br/><br/>

        Error Messages:<br/>
            - Unauthorized: If the user is not authenticated or not admin.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
            - Invalid request data: If the request data does not match the EachUserWalletSchema.<br/>
            - User Wallet not available: If the user does not have any wallet.<br/>
            - Unable to get Admin detail: If the admin detail is not fetched from the database.<br/>
            - Unable to get the Wallet of user: If the wallets of the user are not fetched from the database.<br/><br/>

        Raises:<br/>
            - BadRequest: If the request data is invalid or the file data is not provided.<br/>
            - Unauthorized: If the user is not authenticated or not admin.<br/>
            - Server Error: If an error occurs during the database operations.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            userID          = user_identity.claims.get("user_id") if user_identity else None

            #Check the user is admin or Not
            try:
                user_obj      = await session.execute(select(Users).where(Users.id == userID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            

            #Get the wallets related to the user
            try:
                user_wallet_obj = await session.execute(select(Wallet).where(Wallet.user_id == schema.user_id))
                user_wallets    = user_wallet_obj.scalars().all()

                if not user_wallets:
                    return pretty_json({'msg': 'User Wallet not available'}, 404)

            except Exception as e:
                return pretty_json({'msg': 'Unable to get the Wallet of user', 'error': f'{str(e)}'}, 400)
            

            return pretty_json({'msg': 'Wallet fetched suuccessfully', 'user_wallet_data': user_wallets})
        

    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)