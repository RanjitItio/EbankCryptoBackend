from Models.fee import FeeStructure
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_


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
        

