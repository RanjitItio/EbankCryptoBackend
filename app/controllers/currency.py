from blacksheep.server.controllers import APIController
from blacksheep import Request, json
from database.db import async_engine, AsyncSession
from Models.models import Currency
from Models import models
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from Models.schemas import CurrencySchemas, UpdateCurrencySchema
from app.controllers.controllers import get, post, put, delete
from decouple import config
from httpx import AsyncClient



currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')




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
                    return json({'msg': 'Currency error'}, 400)

                if not all_currency:
                    return json({'msg': 'No currency available'}, 400)
                
                return json({'currencies': all_currency}, 200)
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
        



class CurrencyConverterController(APIController):

    @classmethod
    def route(cls):
        return '/api/v2/convert/currency/'
    
    @classmethod
    def class_name(cls):
        return "Currency Converter"

    @post()
    async def convert_currency(self, request: Request):
        request_body = await request.json()
        
        from_currency = request_body['from_currency']
        to_currency   = request_body['to_currency']
        amount        = request_body['amount']

        try:
            url = f"{currency_converter_api}/convert?from={from_currency}&to={to_currency}&amount={amount}"
            headers = {
            'X-RapidAPI-Key': f"{RAPID_API_KEY}",
            'X-RapidAPI-Host': f"{RAPID_API_HOST}"
        }
                                
            async with AsyncClient() as client:
                response = await client.get(url, headers=headers)
                # print('APi Response', response)

                if response.status_code == 200:
                    api_data = response.json()
                    # print('api data', api_data)

                else:
                    return json({'msg': 'Error calling external API', 'error': response.text}, 400)
                                    
        except Exception as e:
            return json({'msg': 'Currency API Error', 'error': f'{str(e)}'}, 400)

        converted_amount = api_data['result'] if 'result' in api_data else None

        if not converted_amount:
            return json({'msg': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
        

        return json({'converted_amount': converted_amount}, 200)
        
    

