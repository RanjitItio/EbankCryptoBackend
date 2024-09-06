from blacksheep import json, Request, get
from blacksheep.server.authorization import auth
from database.db import AsyncSession, async_engine
from Models.models3 import MerchantAPILogs
from sqlmodel import select, desc, func



# Get all the API Logs created by the merchant During transaction
@auth('userauth')
@get('/api/v5/merchant/transaction/logs/')
async def get_merchantTransactionLogs(request: Request, limit: int = 10, offset: int = 0):
    try:
        async with AsyncSession(async_engine) as session:
            user_identity = request.identity
            user_id       = user_identity.claims.get('user_id') if user_identity else None

            combined_data = []

            # Count total availble rows
            count_stmt = await session.execute(select(
                func.count(MerchantAPILogs.id)
                ).where(
                    MerchantAPILogs.merchant_id == user_id
                ))
            total_rows = count_stmt.scalar()
            

            # Get all the logs of the merchant
            merchant_logs_obj = await session.execute(select(MerchantAPILogs).where(
                MerchantAPILogs.merchant_id == user_id
                ).order_by(desc(MerchantAPILogs.id)).limit(limit).offset(offset)
            )
            merchant_logs = merchant_logs_obj.scalars().all()

            for logs in merchant_logs:
                combined_data.append({
                    'id': logs.id,
                    'merchantID': logs.merchant_id,
                    'createdAt': logs.createdAt,
                    'url': logs.end_point,
                    'error': logs.error,
                    'request_header': logs.request_header,
                    'request_body': logs.request_body,
                    'response_header': logs.response_header,
                    'response_body': logs.response_body
                })

            return json({
                'success': True, 
                'merchant_logs': combined_data,
                'total_rows': total_rows}, 200)
        
    except Exception as e:
        return json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)