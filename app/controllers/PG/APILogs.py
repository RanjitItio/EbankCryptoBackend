from Models.models3 import MerchantAPILogs
from database.db import AsyncSession, async_engine


# Create New API Log for any payment error
async def createNewAPILogs(merchant_id, error, end_point, request_header, request_body, response_header, response_body):
    async with AsyncSession(async_engine) as session:
        api_log_obj = MerchantAPILogs(
            merchant_id      = merchant_id,
            error            = error,
            end_point        = end_point,
            request_header   = request_header,
            request_body     = request_body,
            response_header  = response_header,
            response_body    = response_body
            )
        
        session.add(api_log_obj)
        await session.commit()
        await session.refresh(api_log_obj)