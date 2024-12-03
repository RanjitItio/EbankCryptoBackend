from blacksheep import get, json, Request
from database.db import AsyncSession, async_engine
from Models.models import MerchantGroup
from sqlmodel import select





@get('/api/merchant/groups/')
async def merchant_groups(self, request: Request):
    """
        API endpoint to get all the available merchant groups.<br/>
        Returns a list of all merchant groups.<br/><br/>

        Parameters:<br/>
            - request (Request): The incoming HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the merchant groups(data).<br/>
            - If an error occurs, returns a 500 status code.<br/><br/>

        Error Messages:<br/>
            - Merchant group fetch error: If there is an error while fetching the merchant groups.<br/><br/>
        
        Raises:<br/>
            - Exception: If any error occurs during the database operations or response generation.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            #Get all merchant Groups
            try:
                merchant_grp_obj = await session.execute(select(MerchantGroup))
                merchant_grp     = merchant_grp_obj.scalars().all()
            except Exception as e:
                return json({'msg': 'Merchant group fetch error', 'error': f'{str(e)}'}, 400)
            
            return json({'msg': 'Merchant group data fetched successfully', 'data': merchant_grp}, 200)
        
    except Exception as e:
        return json({'msg': 'Server error', 'error': f'{str(e)}'}, 500)