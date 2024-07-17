from app.controllers.controllers import get,post,put
from blacksheep import Request, pretty_json, Response, redirect
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from Models.PG.schema import (
    PGSandBoxSchema, PGSandboxTransactionProcessSchema
    )
from Models.models import UserKeys
from Models.models2 import MerchantPIPE, MerchantSandBoxTransaction
from app.generateID import (
          calculate_sha256_string, base64_decode, 
          generate_unique_id, generate_base64_encode
        )
from sqlmodel import select, and_
from app.auth import decrypt_merchant_secret_key
from decouple import config
import json




is_development = config('IS_DEVELOPMENT')


if is_development == 'True':
    url = 'http://localhost:5173'
else:
    url = 'https://react-payment.oyefin.com/merchant/payment/checkout'


sandbox_api_key    = config('SANDBOX_API')
sandbox_secret_key = config('SANDBOX_API_SECRET_KEY')

# Sand box payment
class PaymentGatewaySandBoxAPI(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'PG Sandbox API'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/pg/sandbox/v1/pay/'
    
    @post()
    async def create_sandbox_order(request: Request, schema: PGSandBoxSchema) -> Response:
        try:
            async with AsyncSession(async_engine) as session:
                header        = request.headers.get_first(b"X-AUTH")
                header_value  = header.decode()
                # Specify checkout url according to the environment
                checkout_url = url

                INDEX = '1'
                payload = schema.request

                # If Header value is not present
                if not header_value:
                    return pretty_json({'error': 'Missing Header: X-AUTH'}, 400)
                
                # Decod the payload
                decoded_payload = base64_decode(payload)
                payload_dict    = json.loads(decoded_payload)

                # Get all the data from Payload
                merchant_public_key = payload_dict.get('merchantPublicKey')
                merchant_secret_key = payload_dict.get('merchantSecretKey')
                merchant_order_id   = payload_dict.get('merchantOrderId')
                amount              = payload_dict.get('amount')
                redirect_url        = payload_dict.get('redirectUrl')
                # redirect_mode       = payload_dict.get('redirectMode')
                callback_url        = payload_dict.get('callbackUrl')
                mobile_number       = payload_dict.get('mobileNumber')
                payment_type        = payload_dict['paymentInstrument']['type']

                # Validate required fields
                required_fields = ['merchantPublicKey', 'merchantSecretKey', 'merchantOrderId', 'amount', 'redirectUrl']
                for field in required_fields:
                    if not payload_dict.get(field):
                        return pretty_json({'error': f'Missing Parameter: {field}'}, 400)
                
                # If Payment type is not present in payload
                if not payment_type:
                    return pretty_json({'error': 'Missing Parameter: paymentInstrument.type'}, 400)
                
                # Decrypt Merchant secret key
                # merchant_secret_key = await decrypt_merchant_secret_key(merchant_secret_key)
                merchant_secret_key = sandbox_secret_key

                # Get the Secrect key and public key data of the merchant
                # merchant_key_obj = await session.execute(select(UserKeys).where(
                #     UserKeys.public_key == merchant_public_key
                # ))
                # merchant_key = merchant_key_obj.scalar()
                merchant_key = sandbox_api_key

                # Public Key & Merchant ID
                merchant_public_key = sandbox_api_key
                merchant_id        = merchant_key.user_id

                if not merchant_key:
                    return pretty_json({'error': 'Invalid merchantId'}, 400)
                
                # Verify header X-AUTH
                sha256   = calculate_sha256_string(payload + '/api/pg/sandbox/v1/pay/' + merchant_key.secret_key)
                checksum = sha256 + '****' + INDEX

                 # Validate header value
                if checksum != header_value:
                    return pretty_json({'error': 'Incorrect X-AUTH header'}, 400)
                
                # Check Merchant pipe
                merchant_pipe_assigned_obj = await session.execute(select(MerchantPIPE).where(
                    and_(MerchantPIPE.merchant == merchant_key.user_id, MerchantPIPE.is_active == True)
                ))
                merchant_pipe_assigned = merchant_pipe_assigned_obj.scalars().all()

                if not merchant_pipe_assigned:
                    return pretty_json({'error': 'No Active Acquirer available, Please contact administration'}, 400)
                
                
                # Encode the merchant ID
                encoded_merchant_id = generate_base64_encode(merchant_public_key)
                
                
                # Save the Merchant Sandbox Transaction details
               
                exact_amount = amount/100
                unique_transaction_id = generate_unique_id()

                merchant_sandbox_transaction = MerchantSandBoxTransaction(
                    merchant_id          = merchant_id,
                    status               = 'PAYMENT_INITIATED',
                    amount               = exact_amount,
                    merchantOrderId      = merchant_order_id,
                    merchantRedirectURl  = redirect_url,
                    # merchantRedirectMode = redirect_mode,
                    merchantCallBackURL  = callback_url,
                    merchantMobileNumber = mobile_number,
                    merchantPaymentType  = payment_type,
                    transaction_id       = unique_transaction_id,
                    is_completd          = False
                )
                
                session.add(merchant_sandbox_transaction)
                await session.commit()
                await session.refresh(merchant_sandbox_transaction)
                
                return pretty_json({
                        "success": True,
                        "code": "PAYMENT_INITIATED",
                        "message": "Payment Initiated",
                        "data": {
                            "merchantId": merchant_public_key,
                            "merchantTransactionId": merchant_order_id,
                            "instrumentResponse": {
                                "type": "PAY_PAGE",
                                "redirectInfo": {
                                    "url": f"{checkout_url}/merchant/payment/checkout/?token={encoded_merchant_id}",
                                "method": "GET"
                                }
                            }
                        }
                    }, 200)

        except Exception as e:
            return pretty_json({'error': 'Unknown Error Occured', 'msg': f'{str(e)}'}, 500)
      



# class PaymentGatewayProcessTransaction(APIController):

#     @classmethod
#     def class_name(cls) -> str:
#         return 'Payment Process'
    
#     @classmethod
#     def route(cls) -> str | None:
#         return '/api/pg/prod/v1/pay/'
    
#     async def process_transaction(request: Request, schema: PGSandboxTransactionProcessSchema):
#         try:
#             async with AsyncSession(async_engine) as session:
#                 payload = schema.request

#                  # Decod the payload
#                 decoded_payload = base64_decode(payload)
#                 payload_dict    = json.loads(decoded_payload)

#                 payment_mode   = payload_dict.get('paymentMode')
#                 upi_id         = payload_dict.get('upiID')
#                 cardNumber     = payload_dict.get('cardNumber')
#                 cardExpiry     = payload_dict.get('cardExpiry')
#                 cardCVV        = payload_dict.get('cardCVV')
#                 cardHolderName = payload_dict.get('cardHolderName')

#                 if payment_mode == "CARD":
#                     if not cardNumber and cardExpiry and cardCVV and cardHolderName:
#                         return pretty_json({'error': 'Missing card detail'}, 400)
                    
#                 elif payment_mode == 'UPI':
#                     pass

#                 else:
#                     pass

#         except Exception as e:
#             return pretty_json({'error': 'Internal Server Error'}, 500)




