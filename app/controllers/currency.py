from blacksheep.server.controllers import APIController, get, post, put, delete
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from Models.models import Currency
from Models import models
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlalchemy.orm import selectinload
from Models.schemas import CurrencySchemas




class CurrencyController(APIController):

    @classmethod
    def route(cls):
        return '/api/v2/currency'
    
    @classmethod
    def class_name(cls):
        return "Currency"
    
    @get()
    async def get_currency():
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    available_currency = await session.execute(select(Currency))
                    all_currency = available_currency.scalars().all()
                except Exception as e:
                    return json({'msg': 'Currency error'})

                if not all_currency:
                    return json({'msg': 'No currency available'}, 400)
                
                return json({'currencies': all_currency})
        except SQLAlchemyError as e:
            return json({'error': f'{str(e)}'}, 500)


    @post()
    async  def create_currency(self, request: Request, currency: CurrencySchemas):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    CreateCurrency = Currency(
                        name=currency.name,
                        symbol=currency.symbol,
                        fee=currency.fee,
                        decimal_places=currency.decimal_places
                    )
                except Exception as e:
                    return json({'msg': 'Not able to create currency'}, 400)
                
                session.add(CreateCurrency)
                await session.commit()
                await session.refresh(CreateCurrency)

                return json({'msg': 'Currency created successfully'})

        except Exception as e:
            return json({'msg': f'{str(e)}'})
    

    @put()
    async def update_currency():
        try:
            async with AsyncSession(async_engine) as session:
                pass
        except Exception as e:
            return ""
    
    @delete()
    def delete_currency():
        return "Delete currency"
    

