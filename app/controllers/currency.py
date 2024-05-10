from blacksheep.server.controllers import APIController, get, post, put, delete
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from Models.models import Currency
from Models import models
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from Models.schemas import CurrencySchemas, UpdateCurrencySchema




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
                        name           = currency.name,
                        symbol         = currency.symbol,
                        fee            = currency.fee,
                        decimal_places = currency.decimal_places
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
    async def update_currency(self, request: Request):

        try:
            async with AsyncSession(async_engine) as session:
                try:
                    req_body = await request.json()
                    
                    currency_name    = req_body['name']
                    currency_symbol  = req_body['symbol']
                    currency_fee     = req_body['fee']

                    #Get currency
                    try:
                        get_currency = await session.execute(select(Currency).where(Currency.name == currency_name))
                        get_currency_obj = get_currency.scalar()
                    except Exception as e:
                        return json({'msg': 'Unable to locate currency'})

                    if currency_name:
                        get_currency_obj.name = currency_name

                    if currency_symbol:
                        get_currency_obj.symbol = currency_symbol

                    if currency_fee:
                        get_currency_obj.fee = currency_fee
                        
                    session.add(get_currency_obj)
                    await session.commit()
                    await session.refresh(get_currency_obj)
                    
                    return json({'msg': 'Currency updated successfully'})

                except Exception as e:
                    return json({'error1': f'{str(e)}'})

        except Exception as e:
            return json({'error': f'{str(e)}'})
    
    @delete()
    async def delete_currency(self, request: Request):
        try:
            async with AsyncSession(async_engine) as session:
                try:
                    req_body = await request.json()

                    currency_id = req_body['currency_id']

                    #Get currency
                    try:
                        get_currency = await session.execute(select(Currency).where(Currency.id == currency_id))
                        get_currency_obj = get_currency.scalar()

                        if get_currency_obj:
                            await session.delete(get_currency_obj)
                            await session.commit()
                        else:
                            return json({'msg': 'Currency is not available in given ID'})

                    except Exception as e:
                        return json({'msg': f'Unable to locate currency{str(e)}'}, 404)
                    
                except Exception as e:
                    return json({'msg': f'{str(e)}'})
                
        except Exception as e:
            return json({'finalerror': f'{str(e)}'})
        
    

