from httpx import AsyncClient



async def send_request_ipg15(card_number, cvc, url):
    async with AsyncClient() as client:
        public_key    = 'MTEzMTFfMTI3XzIwMjMwODI0MTYyMjU4'
        fullname      = 'Ranjit Kumar'
        bill_ip       = '122.176.92.114'
        bill_amt      = 100.00
        bill_currency = 'USD'
        product_name  = 'Mobile'
        bill_email    = 'ranjit1239@mail.com'
        bill_address  = 'iThum Tower'
        bill_city     = 'Noida'
        bill_state    = 'UP'
        bill_country  = 'India' 
        bill_zip      = '752019'
        bill_phone    = '9090878909'
        reference     = 'webhook testing'
        # webhook_url   = 'https://webhook.site/1281be43-c8ed-4efb-9f21-b56c8e1081e2/?urlaction=notify'
        webhook_url   = 'https://620b-122-176-92-114.ngrok-free.app/api/ipg/webhook/?urlaction=notify'
        return_url    = url
        checkout_url  = ''
        mop           = 'CC'
        ccno          = card_number
        ccvv          = cvc
        month         = '02'
        year          = '24'

        url = f'https://ipg.i15.tech/directapi?public_key={public_key}&integration-type=s2s&fullname={fullname}&bill_ip={bill_ip}&bill_amt={bill_amt}&bill_currency={bill_currency}&product_name={product_name}&bill_email={bill_email}&bill_address={bill_address}&bill_city={bill_city}&bill_state={bill_state}&bill_country={bill_country}&bill_zip={bill_zip}&bill_phone={bill_phone}&reference={reference}&webhook_url={webhook_url}&return_url={return_url}&checkout_url={checkout_url}&mop={mop}&ccno={ccno}&ccvv={ccvv}&month={month}&year={year}'

        response = await client.post(url)

        response.raise_for_status()
        # print(response.json())
        
        return response.json()
    
