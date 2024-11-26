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




# Get all the available Currencies
class CurrencyController(APIController):

    @classmethod
    def route(cls):
        return '/api/v2/currency'
    
    @classmethod
    def class_name(cls):
        return "Currency"

    @get()
    async def get_currency():
        """
            This function retrieves all available currencies using SQLAlchemy in an asynchronous manner and returns them as JSON.<br/><br/>

            Returns:<br/>
            - JSON response with a list of currencies if they are available in the database.<br/>
            - If there is an error during the execution, it will return an empty list of currencies.<br/>
            - If there is an error during the execution, it will return an appropriate error message along with the corresponding status code.<br/>
        """
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
    async  def create_currency(self, request: Request, currency_schema: CurrencySchemas):
        """
        This function is responsible for creating a new currency in the system.<br/>
<br/>
        Parameters:<br/>
        - request (Request): The incoming request object containing the currency data.<br/>
        - currency_schema (CurrencySchemas): The validated currency data schema.<br/>
<br/>
        Returns:<br/>
        - JSON response with a success message if the currency is created successfully.<br/>
        - JSON response with an error message if the currency already exists or if there is an error creating the currency.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                ### Get the currency with same name
                currency_obj = await session.execute(select(Currency).where(
                    Currency.name == currency_schema.name
                ))
                currency = currency_obj.scalar()

                if currency:
                    return json({'message': 'Currency Already exists'}, 400)
                
                try:
                    CreateCurrency = Currency(
                        name           = currency_schema.name,
                        symbol         = currency_schema.name,
                        fee            = 0,
                        decimal_places = 0
                    )
                except Exception as e:
                    return json({'msg': 'Not able to create currency'}, 400)
                
                session.add(CreateCurrency)
                await session.commit()
                await session.refresh(CreateCurrency)

                return json({'msg': 'Currency created successfully'})

        except Exception as e:
            return json({'msg': f'{str(e)}'}, 500)
    

    @put()
    async def update_currency(self, request: Request):
        """
            This function updates a currency object in a database based on the provided request data.<br/><br/>

            Parameters:<br/>
               - request: The `request` parameter in the `update_currency` method is of type `Request`,
                          which is used to represent an HTTP request. It contains information about the incoming request
                          such as headers, body, method, URL, etc.<br/><br/>
            
            Returns:<br/>
            - JSON response with a success message 'Currency updated successfully' if the currency update operation is successful.<br/>
            - JSON response with an error message if the currency update operation fails.<br/>
        """
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
            return json({'error': f'{str(e)}'}, 500)
    
    @delete()
    async def delete_currency(self, request: Request):
        """
            This Python function deletes a currency object from a database based on the provided currency ID.<br/><br/>

            Parameters:<br/>
            - request: The `request` parameter in the `delete_currency` method represents the HTTP
                        request object that contains information about the incoming request, such as headers, body, and currency ID<br/><br/>

            Returns:<br/>
            - JSON response with a success message 'Currency deleted successfully' if the currency deletion operation is successful.<br/>
            - JSON response with an error message if the currency deletion operation fails.<br/>
            - If the currency with the given ID is not found, it returns a JSON response indicating that
              the currency is not available in the given ID.<br/>
        """
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
                            return json({'msg': 'Currency is not available in given ID'}, 400)

                    except Exception as e:
                        return json({'msg': f'Unable to locate currency{str(e)}'}, 404)
                    
                except Exception as e:
                    return json({'msg': f'{str(e)}'}, 500)
                
        except Exception as e:
            return json({'finalerror': f'{str(e)}'}, 500)
        


#### Convert Currency using Rapid API
class CurrencyConverterController(APIController):

    @classmethod
    def route(cls):
        return '/api/v2/convert/currency/'
    
    @classmethod
    def class_name(cls):
        return "Currency Converter"

    @post()
    async def convert_currency(self, request: Request):
        """
            This function converts currency using an external API and returns the converted amount.<br/><br/>

            Parameters:<br/>
            from_currency (str): The currency to be converted from.<br/>
            to_currency (str): The currency to be converted to.<br/>
            amount (float): The amount to be converted.<br/><br/>
            
            Returns:<br/>
            - A JSON response containing the converted amount if the currency conversion is successful.<br/>
            - If there are any errors during the currency conversion process or while calling the external API, appropriate error messages are returned along with the
                corresponding HTTP status codes.<br/>
        """
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
                    return json({'message': 'Error calling external API', 'error': response.text}, 400)
                                    
        except Exception as e:
            return json({'message': 'Currency API Error', 'error': f'{str(e)}'}, 400)

        converted_amount = api_data['result'] if 'result' in api_data else None

        if not converted_amount:
            return json({'message': 'Invalid Curency Converter API response', 'error': 'Conversion result missing'}, 400)
        

        return json({'converted_amount': converted_amount}, 200)
        
    

