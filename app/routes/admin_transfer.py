from blacksheep import get, Request, json, pretty_json
from database.db import AsyncSession, async_engine
from app.auth import decode_token
from sqlmodel import select
from Models.models import Users, Transection, Currency
from blacksheep.server.authorization import auth
from app.docs import docs




@docs(responses={
    400: 'Only admin can view the Transactions',
    400: 'Unable to get Admin detail',
    400: 'Transaction error',
    400: 'Currency not available',
    400: 'Currency error',
    404: 'User is not available',
    400: 'User not found',
    404: 'No Transaction available to show',
    200: 'Transfer Transaction data fetched successfully',
    500: 'Server Error'
})
@auth('userauth')
@get('/api/v1/transfer/transactions')
async def get_transferTransaction(self, request: Request):
    """
      Get all transfer Transactions, Only by Admin, All the API responses are mentioned
    """
    try:
        async with AsyncSession(async_engine) as session:
            user_identity   = request.identity
            AdminID          = user_identity.claims.get("user_id") if user_identity else None

            #Check the user is admin or Not
            try:
                user_obj = await session.execute(select(Users).where(Users.id == AdminID))
                user_obj_data = user_obj.scalar()

                if not user_obj_data.is_admin:
                    return json({'msg': 'Only admin can view the Transactions'}, 400)
                
            except Exception as e:
                return pretty_json({'msg': 'Unable to get Admin detail', 'error': f'{str(e)}'}, 400)
            
            #Get all transaction Data
            try:
                get_all_transaction     = await session.execute(select(Transection).where(Transection.txdtype == 'Transfer'))
                get_all_transaction_obj = get_all_transaction.scalars().all()
            except Exception as e:
                return json({'msg': 'Transaction error', 'error': f'{str(e)}'}, 400)
            
            #Get the Currency
            try:
                currency     = await session.execute(select(Currency))
                currency_obj = currency.scalars().all()

                if not currency_obj:
                    return json({'msg': 'Currency not available'}, 404)
                    
            except Exception as e:
                return pretty_json({'msg': 'Currency error','error': f'{str(e)}'}, 400)
            
            #Get the user data
            try:
                user_obj      = await session.execute(select(Users))
                user_obj_data = user_obj.scalars().all()

                if not user_obj_data:
                    return json({'msg': 'User is not available'}, 404)
                
            except Exception as e:
                return json({'msg': 'User not found'}, 400)
            
            # Prepare dictionaries for output data
            currency_dict = {currency.id: currency for currency in currency_obj}
            user_dict     = {user.id: user for user in user_obj_data}
            receiver_dict = {receiver.id: receiver for receiver in user_obj_data}

            combined_data = []
            
            for transaction in get_all_transaction_obj:
                    currency_id             = transaction.txdcurrency
                    currency_data           = currency_dict.get(currency_id)

                    user_id   = transaction.user_id
                    user_data = user_dict.get(user_id)
                    user_data = {'first_name': user_data.first_name, 'lastname': user_data.lastname, 'id': user_data.id} if user_data else None

                    receiver_id   = transaction.txdrecever
                    receiver_data = receiver_dict.get(receiver_id)
                    receiver_data = {'first_name': receiver_data.first_name, 'lastname': receiver_data.lastname, 'id': receiver_data.id} if receiver_data else None

                    combined_data.append({
                        'transaction': transaction,
                        'currency': currency_data,
                        'user': user_data,
                        'receiver': receiver_data
                    })

            if not get_all_transaction_obj:
                return json({'msg': "No Transaction available to show"}, 404)
            
            return json({'msg': 'Transfer Transaction data fetched successfully', 'data': combined_data}, 200)
        
    except Exception as e:
        return json({'msg': 'Server Error', 'error': f'{str(e)}'}, 500)