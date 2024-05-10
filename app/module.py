from sqlmodel import Session, select
from Models.models import Currency ,Wallet
from blacksheep import Request, json
from database.db import async_engine, AsyncSession



async def createcurrencywallet(userid, initial_balance=0.0):
    async with AsyncSession(async_engine) as session:
        currency = await session.execute(select(Currency))
        allcurrency = currency.scalars().all()
        
        for currency_obj in allcurrency:
            wallet = Wallet(
                user_id=userid,
                currency_id=currency_obj.id,
                balance=initial_balance
            )
            session.add(wallet)
            await session.commit()
            
        return True
    
    