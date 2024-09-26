from database.db import AsyncSession, async_engine
from Models.models4 import DepositTransaction
from sqlmodel import select
import uuid



# Create unique Transaction ID for Deposit Transactions
async def UniqueDepositTransactionID():
    async with AsyncSession(async_engine) as session:
        # Get the deposit transaction
        unique_id = str(uuid.uuid4())

        while True:
            deposit_transaction_obj = await session.execute(select(DepositTransaction).where(
                DepositTransaction.transaction_id == unique_id
            ))
            deposit_transaction = deposit_transaction_obj.scalars().first()

            if not deposit_transaction:
                return unique_id

