from blacksheep import post, Request, json, get, redirect
from database.db import AsyncSession, async_engine
from Models.models import TestModel
import time



@post('/api/test/date/')
async def test_api(self, request: Request):
    try:
        async with AsyncSession(async_engine) as session:

            request_body = await request.json()
            first_name = request_body['first_name']
            last_name = request_body['last_name']

            
            test_model = TestModel(
                first_name = first_name,
                last_name = last_name
            )

            session.add(test_model)
            await session.commit()
            await session.refresh(test_model)
            
    except Exception as e:
        return json({'msg': f'{str(e)}'}, 500)
    
    return json({'msg': 'Success'})



@post('/api/example/redirect/')
async def test_redirection(self, request: Request):
    return redirect('http://localhost:5173/merchant/payment/success/')
