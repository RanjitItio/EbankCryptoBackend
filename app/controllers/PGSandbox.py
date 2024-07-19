from app.controllers.controllers import get,post
from blacksheep import Request, pretty_json, Response, redirect
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from Models.PG.schema import (
    PGSandBoxSchema, PGSandboxTransactionProcessSchema
    )
from Models.models2 import MerchantSandBoxTransaction
from app.generateID import (
          calculate_sha256_string, base64_decode, 
          generate_unique_id, generate_base64_encode
        )
from sqlmodel import select, and_
from decouple import config
import json




is_development = config('IS_DEVELOPMENT')


if is_development == 'True':
    url = 'http://localhost:5173'
else:
    url = 'https://react-payment.oyefin.com'


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
                currency            = payload_dict.get('currency')
                redirect_url        = payload_dict.get('redirectUrl')
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
                
                merchant_public_key = sandbox_api_key
                merchant_secret_key = sandbox_secret_key


                # Verify header X-AUTH
                sha256   = calculate_sha256_string(payload + '/api/pg/sandbox/v1/pay/' + merchant_secret_key)
                checksum = sha256 + '****' + INDEX

                 # Validate header value
                if checksum != header_value:
                    return pretty_json({'error': 'Incorrect X-AUTH header'}, 400)
                
                # Save the Merchant Sandbox Transaction details
                exact_amount          = amount/100
                unique_transaction_id = generate_unique_id()

                # Merchant order ID unique check
                merchant_order_id_validation_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchantOrderId == merchant_order_id
                ))
                merchant_order_id_validation_ = merchant_order_id_validation_obj.scalar()

                if merchant_order_id_validation_:
                    return pretty_json({'error': 'Please provide unique order ID'}, 400)

                # Encode the merchant ID
                encoded_merchant_public_key = generate_base64_encode(merchant_public_key)
                encoded_amount           = generate_base64_encode(exact_amount)
                encodedMerchantOrderID   = generate_base64_encode(merchant_order_id)
                encodedCurrency          = generate_base64_encode(currency)


                merchant_sandbox_transaction = MerchantSandBoxTransaction(
                    # merchant_id          = merchant_id,
                    status               = 'PAYMENT_INITIATED',
                    amount               = exact_amount,
                    merchantOrderId      = merchant_order_id,
                    merchantRedirectURl  = redirect_url,
                    merchantRedirectMode = 'REDIRECT',
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
                        "status": "PAYMENT_INITIATED",
                        "message": "Payment Initiated",
                        "data": {
                            "merchantId": merchant_public_key,
                            "merchantTransactionId": merchant_order_id,
                            "transactionID":  merchant_sandbox_transaction.transaction_id,
                            "instrumentResponse": {
                                "type": "PAY_PAGE",
                                "redirectInfo": {
                                    "url": f"{checkout_url}/merchant/payment/sb/checkout/?token={encoded_merchant_public_key},{encoded_amount},{encodedMerchantOrderID},{encodedCurrency}",
                                "method": "GET"
                                }
                            }
                        }
                    }, 200)

        except Exception as e:
            return pretty_json({'error': 'Unknown Error Occured', 'msg': f'{str(e)}'}, 500)
      



# Merchant Transaction Status
class MerchantSandboxTransactionStatus(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Sandbox Transaction Status'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/pg/sandbox/merchant/transaction/status/{merchant_public_key}/{merchant_order_id}'
    
    @get()
    async def MerchantSandboxTransactionStatus(request: Request, merchant_public_key: str, merchant_order_id: str):
        try:
            async with AsyncSession(async_engine) as session:
                merchantPublicKey = merchant_public_key
                merchantOrderID   = merchant_order_id

                if merchantPublicKey != sandbox_api_key:
                    return pretty_json({'error': 'Wrong Public Key'}, 400)
                
                # Get The transaction of the Merchant
                merchant_transaction_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchantOrderId == merchantOrderID
                    ))
                merchant_transaction = merchant_transaction_obj.scalar()

                payment_status    = merchant_transaction.status
                merchant_order_id = merchant_transaction.merchantOrderId
                transaction_id    = merchant_transaction.transaction_id
                amount            = merchant_transaction.amount
                currency          = merchant_transaction.currency
                payment_mode      = merchant_transaction.payment_mode


                if payment_status == 'PAYMENT_INITIATE':
                    message = 'Payment Initiated remained to complete the transaction'
                    state   = 'STARTED'
                    responseCode = 'INITIATED'
                    success = False

                elif payment_status == 'PAYMENT_SUCCESS':
                    message      = 'Payment Successfull'
                    responseCode = 'SUCCESS'
                    state        = 'COMPLETED'
                    success      = True
                    

                elif payment_status == 'PAYMENT_PENDING':
                    message      = 'Payment Pending'
                    responseCode = 'PENDING'
                    state        = 'PENDING'
                    success      = False

                elif payment_status == 'PAYMENT_FAILED':
                    message      = 'Payment Failed'
                    responseCode = 'FAILED'
                    state        = 'FAILED'
                    success      = False

                if merchant_transaction:

                    return pretty_json({
                                "success": success,
                                "status": merchant_transaction.status,
                                "message": message,
                                "data": {
                                    "merchantPublicKey": merchantPublicKey,
                                    "merchantOrderId": merchant_order_id,
                                    "transactionId": transaction_id,
                                    "amount": amount,
                                    'currency': currency,
                                    "state": state,
                                    "responseCode": responseCode,
                                    "paymentInstrument": {
                                        "type": payment_mode,
                                    }
                                }
                            })
                
        except Exception as e:
            return pretty_json({'error': 'Server Error'}, 500)


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




