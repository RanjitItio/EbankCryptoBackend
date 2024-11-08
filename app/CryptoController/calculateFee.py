from Models.fee import FeeStructure
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_
from blacksheep import Request, json
from blacksheep.server.authorization import auth
from blacksheep.server.controllers import APIController
from app.controllers.controllers import get, post



async def CalculateFee(fee_id: int, amount: float):

    async with AsyncSession(async_engine) as session:
        # Get the fee
        fee_structure_obj = await session.execute(select(FeeStructure).where(
            FeeStructure.id == fee_id
        ))
        fee_structure_ = fee_structure_obj.scalar()

        calculated_fee = 0

        if fee_structure_.fee_type == 'Fixed':
            fixed_fee = fee_structure_.min_value 

            calculated_fee = fixed_fee

        if fee_structure_.fee_type == 'Percentage':
            percentage_fee = (amount / 100) * fee_structure_.tax_rate

            calculated_fee += percentage_fee

        return calculated_fee if calculated_fee > 0 else 10
        



### Get fee 
class FeeController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Fee Controller'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v2/charged/fee/'
    

    @auth('userauth')
    @post()
    async def fee_charged(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                user_identity = request.identity
                user_id       = user_identity.claims.get('user_id')

                request_data = await request.json()
                feeType      = request_data['fee_type']
                amount       = request_data['amount']

                # Get fee type from FeeStrcture
                fee_structure_obj = await session.execute(select(FeeStructure).where(
                    FeeStructure.name == feeType
                ))
                fee_structure = fee_structure_obj.scalar()

                calculated_fee = 0

                if fee_structure:

                    if fee_structure.fee_type == 'Fixed':
                        fixed_fee = fee_structure.min_value 

                        calculated_fee = fixed_fee

                    elif fee_structure.fee_type == 'Percentage':
                        percentage_fee = (float(amount) / 100) * fee_structure.tax_rate

                        calculated_fee += percentage_fee

                else:
                    calculated_fee = 10

                return json({
                    'success': True,
                    'fee': calculated_fee if calculated_fee > 0 else 10
                })
            
        except Exception as e:
            return json({
                'error': 'Server Error',
                'message': f'{str(e)}'
                }, 500)