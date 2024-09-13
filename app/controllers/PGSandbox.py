from app.controllers.controllers import get,post
from blacksheep import Request, pretty_json, Response, redirect
from blacksheep.server.controllers import APIController
from database.db import AsyncSession, async_engine
from Models.PG.schema import (
    PGSandBoxSchema, PGSandboxTransactionProcessSchema
    )
from Models.models2 import MerchantSandBoxTransaction
from Models.models import UserKeys
from app.generateID import (
          calculate_sha256_string, base64_decode, 
          generate_unique_id, generate_base64_encode
        )
from sqlmodel import select, and_
from app.auth import decrypt_merchant_secret_key
from app.controllers.PG.webhook import send_webhook_response, WebhookPayload
from decouple import config
import json




is_development = config('IS_DEVELOPMENT')


if is_development == 'True':
    url = 'http://localhost:5173'
    redirectURL = 'http://localhost:5173/mastercard/payment/status'
else:
    url = 'https://react-payment.oyefin.com'
    redirectURL = 'https://react-payment.oyefin.com/mastercard/payment/status'




# Sand box payment
class PaymentGatewaySandboxAPI(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'PG Sandbox API'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/pg/sandbox/v1/pay/'
    

    @post()
    async def create_order(request: Request, schema: PGSandBoxSchema) -> Response:
        try:
            async with AsyncSession(async_engine) as session:
                header        = request.headers.get_first(b"X-AUTH")

                if not header:
                    return pretty_json({'error': 'Missing Header: X-AUTH'}, 400)
                
                header_value  = header.decode()

                # Specify checkout url according to the environment
                checkout_url = url

                INDEX = '1'
                payload = schema.request

                # Decode the payload
                decoded_payload = base64_decode(payload)
                payload_dict    = json.loads(decoded_payload)

                # Get all the data from Payload
                merchant_public_key = payload_dict.get('merchantPublicKey')
                merchant_secret_key = payload_dict.get('merchantSecretKey')
                merchant_order_id   = payload_dict.get('merchantOrderId')
                currency            = payload_dict.get('currency')
                amount              = payload_dict.get('amount')
                redirect_url        = payload_dict.get('redirectUrl')
                callback_url        = payload_dict.get('callbackUrl')
                mobile_number       = payload_dict.get('mobileNumber')
                business_name       = payload_dict.get('BusinessName')
                payment_type        = payload_dict['paymentInstrument']['type']


                # If Header value is not present
                if not header_value:
                    return pretty_json({ 'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": "Missing Header: X-AUTH",
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                'transactionID': '',
                                'time': '',
                                "amount": amount,
                                'currency': currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)

                # Validate required fields
                required_fields = ['merchantPublicKey', 'merchantSecretKey', 'merchantOrderId', 'amount', 'redirectUrl', 'currency']
                for field in required_fields:
                    if not payload_dict.get(field):
                        return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": f'Missing Parameter: {field}',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                "transactionID": '',
                                'time': '',
                                "amount": amount,
                                "currency": currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)


                # If Payment type is not present in payload
                if not payment_type:
                    # return pretty_json({'error': 'Missing Parameter: paymentInstrument.type'}, 400)
                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": 'Missing Parameter: paymentInstrument.type',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                'transactionID':  'not created',
                                'time': 'not created',
                                "amount": amount,
                                "currency": currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)
                
                # Decrypt Merchant secret key
                merchant_secret_key = await decrypt_merchant_secret_key(merchant_secret_key)

                # Get the Secrect key and public key data of the merchant
                merchant_key_obj = await session.execute(select(UserKeys).where(
                    UserKeys.public_key == merchant_public_key
                ))
                merchant_key = merchant_key_obj.scalar()

                if not merchant_key:
                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": 'Invalid merchantPublicKey',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                "transactionID": 'not created',
                                'time': 'not created',
                                "amount": amount,
                                "currency": currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)
                
                # Public Key & Merchant ID
                merchant_public_key = merchant_key.public_key
                merchant_id         = merchant_key.user_id

                # Verify header X-AUTH
                sha256   = calculate_sha256_string(payload + '/api/pg/sandbox/v1/pay/' + merchant_key.secret_key)
                checksum = sha256 + '****' + INDEX

                 # Validate header value
                if checksum != header_value:
                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": 'Incorrect X-AUTH header',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                'transactionID': 'not created',
                                'time': 'not created',
                                "amount": amount,
                                "currency": currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)
                
                if currency != 'USD':
                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": 'Invalid Currency: Only USD Accepted',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                "transactionID": 'not created',
                                "time": 'not created',
                                "amount": amount,
                                "currency": currency,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)

                # Merchant order ID unique check
                merchant_order_id_validation_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    MerchantSandBoxTransaction.merchantOrderId == merchant_order_id
                ))
                merchant_order_id_validation_ = merchant_order_id_validation_obj.scalar()

                if merchant_order_id_validation_:
                    return pretty_json({ 'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message": 'Please provide unique order ID',
                            "data": {
                                "merchantPublicKey": merchant_public_key,
                                "merchantOrderId": merchant_order_id,
                                "transactionID": 'not created',
                                'time': 'not created',
                                "amount": amount,
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                    "redirectInfo": {
                                        "url": '',
                                    }
                                }
                            }
                        }
                    }, 400)
                
                # Save the Merchant Sandbox Transaction details
                exact_amount = amount/100
                unique_transaction_id = generate_unique_id()

                
                merchant_sandbox_transaction = MerchantSandBoxTransaction(
                    merchant_id          = merchant_id,
                    status               = 'PAYMENT_INITIATED',
                    currency             = currency,
                    amount               = exact_amount,
                    merchantOrderId      = merchant_order_id,
                    merchantRedirectURl  = redirect_url,
                    merchantRedirectMode = "REDIRECT",
                    merchantCallBackURL  = callback_url,
                    merchantMobileNumber = mobile_number,
                    merchantPaymentType  = payment_type,
                    transaction_id       = unique_transaction_id,
                    is_completd          = False,
                    gateway_res          = '' ,  
                    business_name        = business_name
                )
                
                # Save the transaction into database
                session.add(merchant_sandbox_transaction)
                await session.commit()
                await session.refresh(merchant_sandbox_transaction)

                # Encode the merchant ID
                encoded_merchant_public_key = generate_base64_encode(merchant_public_key)
                encoded_amount              = generate_base64_encode(exact_amount)
                encodedOrderID              = generate_base64_encode(merchant_sandbox_transaction.merchantOrderId)
                encodedCurrency             = generate_base64_encode(currency)
                encodedBusinessName         = generate_base64_encode(business_name)


                return pretty_json({
                        "success": True,
                        "status": "PAYMENT_INITIATED",
                        "message": "Payment Initiated",
                        "data": {
                            "merchantPublicKey": merchant_public_key,
                            "merchantOrderId": merchant_order_id,
                            "transactionID":  merchant_sandbox_transaction.transaction_id,
                            "time": merchant_sandbox_transaction.createdAt,
                            'currency': currency,
                            "amount": exact_amount,
                            "instrumentResponse": {
                                "type": "PAY_PAGE",
                                "redirectInfo": {
                                    "url": f"{checkout_url}/merchant/payment/sb/checkout/?token={encoded_merchant_public_key},{encoded_amount},{encodedOrderID},{encodedCurrency},{encodedBusinessName}",
                                "method": "GET"
                                }
                            }
                        }
                    }, 200)

        except Exception as e:
            return pretty_json({'error': 'Unknown Error Occured', 'msg':f'{str(e)}'}, 500)
        



# Get the payment detials of the merchant and show transaction response
class MerchantProcessTransactionController(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Process Sandbox Transaction'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/pg/sandbox/merchant/process/transactions/'
    
    @post()
    async def process_merchant_transaction(request: Request, schema: PGSandboxTransactionProcessSchema):
        try:
            async with AsyncSession(async_engine) as session:
                request_payload = schema.request

                # Decode the card details
                decode_payload = base64_decode(request_payload)
                decoded_dict   = json.loads(decode_payload)

                card_no           = decoded_dict.get('cardNumber')
                card_expiry       = decoded_dict.get('cardExpiry')
                card_cvv          = decoded_dict.get('cardCvv')
                card_name         = decoded_dict.get('cardHolderName')
                merchant_order_id = decoded_dict.get('MerchantOrderId')
                payment_mode      = decoded_dict.get('paymentMode')


                # Get the merchant production Transaction
                merchant_sandbox_transaction_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                        MerchantSandBoxTransaction.merchantOrderId == merchant_order_id
                ))
                merchant_sandbox_transaction = merchant_sandbox_transaction_obj.scalar()

                if not merchant_sandbox_transaction:
                    return pretty_json({'error': 'Please initiate transaction'}, 400)
                
                # Check transaction status
                trasnaction_status = merchant_sandbox_transaction.is_completd

                # If the transaction has been completed
                if trasnaction_status:
                    return pretty_json({'error': 'Transaction has been closed'}, 400)
                
                # Get The Merchant Public key
                merchant_key_obj = await session.execute(select(UserKeys).where(
                    UserKeys.user_id == merchant_sandbox_transaction.merchant_id
                ))
                merchant_key_ = merchant_key_obj.scalars().first()
                
                if not merchant_key_:
                    return pretty_json({'error': 'Merchant Public key not found'}, 404)
                
                 # Transaction ID and amount sent to master card
                transaction_id = merchant_sandbox_transaction.transaction_id
                amount         = merchant_sandbox_transaction.amount
                currency       = merchant_sandbox_transaction.currency

                # Merchant Public Key
                merchantPublicKey = merchant_key_.public_key

                # Merchant Redirect url given during transaction
                merchantRedirectURL  = merchant_sandbox_transaction.merchantRedirectURl

                # Merchant callback URL given during transaction
                merchantCallBackURL  = merchant_sandbox_transaction.merchantCallBackURL

                #Transaction Time
                transactionTime = merchant_sandbox_transaction.createdAt.strftime('%Y-%m-%d %H:%M:%S.%f')

                # Send Webhook to merchant webhook url
                if merchantCallBackURL:
                    webhook_payload_dict = {
                        "success": True,
                        "status": "PAYMENT_SUCCESS",
                        "message": 'SUCCESS',
                        "data": {
                            "merchantPublicKey": merchantPublicKey,
                            "merchantOrderId": merchant_order_id,
                            'transactionID': transaction_id,
                            'time': transactionTime,
                            "instrumentResponse": {
                                "type": "PAY_PAGE",
                                    "redirectInfo": {
                                    "url": merchantRedirectURL,
                            }
                            }
                        }
                    }

                    webhook_payload = WebhookPayload(
                        success = webhook_payload_dict['success'],
                        status  = webhook_payload_dict["status"],
                        message = webhook_payload_dict["message"],
                        data    = webhook_payload_dict["data"]
                    )

                    await send_webhook_response(webhook_payload, merchantCallBackURL)

                # Update the merchant transaction status
                merchant_sandbox_transaction.status       = 'PAYMENT_SUCCESS'
                merchant_sandbox_transaction.payment_mode = payment_mode
                merchant_sandbox_transaction.is_completd  = True

                session.add(merchant_sandbox_transaction)
                await session.commit()
                await session.refresh(merchant_sandbox_transaction)

                # Response to the page
                return pretty_json({
                    'status': 'PAYMENT_SUCCESS',
                    'message': 'SUCCESS',
                    'transactionID': transaction_id,
                    'merchantRedirectURL': merchantRedirectURL
                }, 200)

        except Exception as e:
            return pretty_json({'error': 'Server Error'}, 500)



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

                # Validate the merchant public
                user_key_obj = await session.execute(select(UserKeys).where(
                    UserKeys.public_key == merchantPublicKey
                ))
                user_key = user_key_obj.scalar()

                if not user_key:
                    return pretty_json({'error': {
                        'success': False,
                        'message': 'Invalid merchantPublicKey'
                    }}, 400)
                
                merchant_id = user_key.user_id

                # Get The transaction of the Merchant
                merchant_transaction_obj = await session.execute(select(MerchantSandBoxTransaction).where(
                    and_(MerchantSandBoxTransaction.merchantOrderId == merchantOrderID,
                         MerchantSandBoxTransaction.merchant_id     == merchant_id
                         )
                    ))
                merchant_transaction = merchant_transaction_obj.scalar()

                if not merchant_transaction:
                    return pretty_json({'error': {
                        'success': False,
                        'message': 'Transaction not found'
                    }}, 404)
                
                payment_status    = merchant_transaction.status
                merchant_order_id = merchant_transaction.merchantOrderId
                transaction_id    = merchant_transaction.transaction_id
                amount            = merchant_transaction.amount
                currency          = merchant_transaction.currency
                payment_mode      = merchant_transaction.payment_mode
                time              = merchant_transaction.createdAt


                if payment_status == 'PAYMENT_INITIATED':
                    message = 'Payment Initiated remained to complete the transaction'
                    status   = 'STARTED'
                    responseCode = 'INITIATED'
                    success = False

                elif payment_status == 'PAYMENT_SUCCESS':
                    message      = 'Payment Successfull'
                    responseCode = 'SUCCESS'
                    status        = 'COMPLETED'
                    success      = True
                    

                elif payment_status == 'PAYMENT_PENDING':
                    message      = 'Payment Pending'
                    responseCode = 'PENDING'
                    status        = 'PENDING'
                    success      = False

                elif payment_status == 'PAYMENT_FAILED':
                    message      = 'Payment Failed'
                    responseCode = 'FAILED'
                    status        = 'FAILED'
                    success      = False
                else:
                    message      = 'Payment Failed'
                    responseCode = 'FAILED'
                    status        = 'FAILED'
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
                                    'time': time,
                                    "amount": amount,
                                    'currency': currency,
                                    "responseCode": responseCode,
                                    "paymentInstrument": {
                                        "type": payment_mode,
                                    }
                                }
                            }, 200)
                
        except Exception as e:
            return pretty_json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)




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




