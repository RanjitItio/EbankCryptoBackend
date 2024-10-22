from decouple import config
from httpx import AsyncClient


currency_converter_api = config('CURRENCY_CONVERTER_API')
RAPID_API_KEY          = config('RAPID_API_KEY')
RAPID_API_HOST         = config('RAPID_API_HOST')


## Convert Currency using Rapid API
async def ConvertRapidAPICurrency(from_currency, to_currency, amount):
    try:
        url = f"{currency_converter_api}/convert?from={from_currency.name}&to={to_currency.name}&amount={amount}"
        headers = {
            'X-RapidAPI-Key': f"{RAPID_API_KEY}",
            'X-RapidAPI-Host': f"{RAPID_API_HOST}"
        }
        
        async with AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                api_data = response.json()
                return api_data

            else:
                return 'Error calling external API'
            
    except Exception as e:
        return 'Currency API Error'
    