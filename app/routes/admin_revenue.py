from blacksheep import get, json, Request
from blacksheep.server.authorization import auth
from Models.models import Users
from Models.models2 import MerchantProdTransaction, PIPE, MerchantPIPE
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_




# Get all collected Revenues
@auth('userauth')
@get('/api/v6/admin/revenues/')
async def GetAdminRevenues(request: Request):
    """
        This API endpoint is used to get total amount related to every currency of all the successful transactions made through each pipe.<br/>
        This endpoint is only accessible by admin users.<br/><br/>

        Parameters:<br/>
            - request (Request): The HTTP request object.<br/><br/>

        Returns:<br/>
            - JSON: A JSON response containing the total amount related to every currency of all the successful transactions made through each pipe.<br/>
            - HTTP Status Code: 200.<br/>
            - HTTP Status Code: 401 in case of unauthorized access.<br/>
            - HTTP Status Code: 500 in case of server errors.<br/><br/>

        Error Messages:<br/>
            - Unauthorized Access: If the user is not authenticated as an admin user.<br/>
            - Server Error: If an error occurs while executing the database query or response generation.<br/>
            - Bad Request: If the request data is invalid.<br/><br/>
        
        Raises:<br/>
            - HTTPException: If the user is not authenticated as an admin user.<br/>
            - HTTPStatus: 400 Bad Request if the request data is invalid.<br/>
            - HTTPStatus: 500 Internal Server Error if an error occurs while executing the database query or response generation.<br/>
    """
    try:
        async with AsyncSession(async_engine) as session:
            # Authenticate Admin
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id')

            combined_data = []

            adminUserObj = await session.execute(select(Users).where(
                Users.id == user_id
            ))
            adminUser = adminUserObj.scalar()

            if not adminUser.is_admin:
                return json({'message': 'Unauthorized access'}, 401)
            # Authentication ends here

            pipe_obj = await session.execute(select(PIPE))
            pipes    = pipe_obj.scalars().all()

            # Transactions related to every pipe\
            pipe_revenue_data = []

            for p in pipes:
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.pipe_id == p.id,
                         MerchantProdTransaction.status  == 'PAYMENT_SUCCESS',
                         MerchantProdTransaction.is_completd == True
                        )
                    ))
                merchant_transactions = merchant_transaction_obj.scalars().all()

                currency_wise_transactions = {}
                
                for transaction in merchant_transactions:
                    currency = transaction.currency 
                    amount   = transaction.fee_amount if not transaction.is_refunded else -transaction.fee_amount

                    if currency not in currency_wise_transactions:
                        currency_wise_transactions[currency] = 0

                    currency_wise_transactions[currency] += amount

                # pipe_total_transaction_amount = sum(transaction.amount if not transaction.is_refunded else
                #                             - transaction.amount for transaction in merchant_transactions)

                total_transaction_amounts = [
                    {'currency': currency, 'total_amount': total_amount}
                    for currency, total_amount in currency_wise_transactions.items()
                ]

                pipe_revenue_data.append({
                    'pipe_id': p.id,
                    'pipe_name': p.name,
                    'total_transaction_amount': total_transaction_amounts
                })

            return json({
                'success': True,
                'pipe_wise_transaction': pipe_revenue_data
                }, 200)

    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)







