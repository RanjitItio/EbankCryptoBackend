from database.db import AsyncSession, async_engine
from Models.models2 import MerchantAccountBalance, CollectedFees
from sqlmodel import select


# Update merchant Account Balance
async def CalculateMerchantAccountBalance(transactionAmount, currency, merchantPipeFee, merchantID):
    try:
        async with AsyncSession(async_engine) as session:
            merchant_pipe_fee_amount = merchantPipeFee

            charged_fee = transactionAmount * merchant_pipe_fee_amount
            merchant_account_balance = transactionAmount - charged_fee

            # Save the Fees chanrged during the transaction
            existing_collected_fees = await session.execute(
                select(CollectedFees).where(CollectedFees.currency == currency)
            )
            existing_collected_fees = existing_collected_fees.scalar_one_or_none()

            if existing_collected_fees:
                # Add the charged fee to the existing amount
                existing_collected_fees.amount += charged_fee
            else:
                # Create a new entry if no existing record is found
                existing_collected_fees = CollectedFees(
                    amount   = charged_fee,
                    currency = currency
                )

            # Get the Account balance of the merchant if exists or Create one
            merchantAccountBalanceObj = await session.execute(select(MerchantAccountBalance).where(
                MerchantAccountBalance.merchant_id == merchantID
            ))
            merchantAccountBalance = merchantAccountBalanceObj.scalar()

            # If Account does not exists then create one
            if not merchantAccountBalance:
                merchantAccountBalance = MerchantAccountBalance(
                    amount      = merchant_account_balance,
                    merchant_id = merchantID,
                    currency    = currency
                )

                session.add(merchantAccountBalance)
                await session.commit()
                await session.refresh(merchantAccountBalance)

            # Update Merchant Account Balance If Exists
            merchantAccountBalance.amount      += merchant_account_balance
            merchantAccountBalance.merchant_id = merchantID
            merchantAccountBalance.currency    = currency

            session.add(merchantAccountBalance)
            session.add(existing_collected_fees)
            await session.commit()
            await session.refresh(merchantAccountBalance)
            await session.refresh(existing_collected_fees)

    except Exception as e:
        return f'Server Error {str(e)}'