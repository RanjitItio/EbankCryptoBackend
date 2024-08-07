from decouple import config
import json
import requests
import httpx




MERCHANT_ID      = config('MASTERCARD_MERCHANT_ID')
MERCHANT_PASSWORD= config('MASTERCARD_MERCHANT_AUTH_PASSWORD')

is_development = config('IS_DEVELOPMENT')

# Webhook url according to the environment
if is_development == 'True':
    notification_url = 'https://d5ff-122-176-92-114.ngrok-free.app'
else:
    notification_url = 'https://python-uat.oyefin.com'


authorization_value = f'merchant.{MERCHANT_ID}:{MERCHANT_PASSWORD}'
# base64_encoded_authorization_header = generate_base64_encode(authorization_value)
base64_encoded_authorization_header = 'bWVyY2hhbnQuR0xBRENPUklHS0VOOjRkM2Y4ZTA3YjJjNjI1ZDc3OWI4MWM2NzgwODZjYzFk'


# Create Session
def Create_Session():
    create_session_url = f'https://ap-gateway.mastercard.com/api/rest/version/78/merchant/{MERCHANT_ID}/session'
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': f'Basic {base64_encoded_authorization_header}'
    }

    payload = json.dumps({
        "session": {
            "authenticationLimit": 25
        }
    })

    response = requests.request("POST", url=create_session_url, headers=headers, data = payload)

    if response.status_code == 201:
        return response.json()
    
    else:
        return {
            'status_code': response.status_code,
            'error': response.json()
        }





# Update Session
def Update_Session(sessionID, transaction_id, card_no, card_cvv, card_expiry, currency, amount, redirect_url):
    update_session_url = f'https://ap-gateway.mastercard.com/api/rest/version/78/merchant/{MERCHANT_ID}/session/{sessionID}'

    exact_amount = amount/100

    month, year = card_expiry.split('/')

    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': f'Basic {base64_encoded_authorization_header}'
    }

    payload = json.dumps({
                "order": {
                    "currency": currency,
                    "amount": exact_amount,
                    "id": transaction_id,
                    "reference": transaction_id,
                    "notificationUrl": f'{notification_url}/api/v1/prod/mastercard/webhook/'
                },
            "authentication": {
                "channel": "PAYER_BROWSER",
                "redirectResponseUrl": f'{redirect_url}/?transaction={transaction_id}'
            },
            "transaction": {
                "id": transaction_id
            },
            "sourceOfFunds": {
                "provided": {
                    "card": {
                        "number": card_no,
                        "securityCode": card_cvv,
                        "expiry": {
                            "month": month,
                            "year": year
                        }
                    }
                },
                "type": "CARD"
            }
    })

    response = requests.request("PUT", url=update_session_url, headers=headers, data = payload)

    if response.status_code == 200:
        return response.json()
    
    else:
        return {
            'status_code': response.status_code,
            'error':response.json()
            }



# Initiate Authentication
def Initiate_Authentication(transaction_id, sessionID, currency):
    initiate_auth_url = f'https://ap-gateway.mastercard.com/api/rest/version/78/merchant/{MERCHANT_ID}/order/{transaction_id}/transaction/{transaction_id}'

    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': f'Basic {base64_encoded_authorization_header}'
    }

    payload = json.dumps({
            "apiOperation": "INITIATE_AUTHENTICATION",
            "authentication": {
                "purpose": "PAYMENT_TRANSACTION",
                "channel": "PAYER_BROWSER"
            },
            "correlationId": "test",
            "order": {
                "reference": transaction_id,
                "currency": currency
            },
            "session": {
                "id": sessionID
            },
            "transaction": {
                "reference": transaction_id
            }
        })
    
    response = requests.request("PUT", url=initiate_auth_url, headers=headers, data = payload)

    if response.status_code == 201:
        return response.json()
    
    else:
        return {
            'error': response.json(),
            'status_code ': response.status_code
        }
    


def deduct_amount(transaction_id, sessionID):
    url = f'https://ap-gateway.mastercard.com/api/rest/version/78/merchant/{MERCHANT_ID}/order/{transaction_id}/transaction/{transaction_id}A'

    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': f'Basic {base64_encoded_authorization_header}'
    }

    payload = json.dumps({
                "apiOperation": "PAY",
                "authentication": {
                    "transactionId": transaction_id
                },
                "session": {
                    "id": sessionID
                },
                "transaction": {
                    "reference": transaction_id
                }
            })
    
    response = requests.request("PUT", url=url, headers=headers, data = payload)

    if response.status_code == 200:
        return response.json()
    
    else:
        return {
            'error': response.json(),
            'status_code ': response.status_code
        }
    



# Transaction Status
def Mastercard_Transaction_Status(transactionID):
    transaction_status_url = f'https://ap-gateway.mastercard.com/api/rest/version/78/merchant/{MERCHANT_ID}/order/{transactionID}/transaction/{transactionID}'

    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'Authorization': f'Basic {base64_encoded_authorization_header}'
    }

    response = requests.request("GET", url=transaction_status_url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            'error': response.json()
        }






# Send Master card Webhook Response to Client
class MasterCardWebhookPayload:
    def __init__(self, success: bool, status: str, message: str, transactionID: str, data: dict) -> None:
        self.success = success
        self.status  = status
        self.message = message
        self.data    = data
        self.transactionID = transactionID


async def send_mastercard_webhook(url: str, payload: MasterCardWebhookPayload):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={
            "success": payload.success,
            "status":  payload.status,
            "message": payload.message,
            "transactionID": payload.transactionID,
            "data": payload.data
        })
        return response


# @post('/api/send-webhook/')
async def send_webhook_response(payload: MasterCardWebhookPayload, url: str):

    try:
        response = await send_mastercard_webhook(url, payload)

        if response.status_code == 200:
            return {"message": "Webhook sent successfully"}
        else:
            return {"message": "Failed to send webhook", "status_code": response.status_code}
        
    except Exception as e:
        return {"message": "An error occurred while sending the webhook", "error": str(e)}
    


