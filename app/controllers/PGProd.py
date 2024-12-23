from decouple import config
from blacksheep.server.controllers import APIController
from blacksheep import pretty_json, Request, Response, redirect
from database.db import AsyncSession, async_engine
from Models.models import UserKeys
from Models.models2 import MerchantPIPE, MerchantProdTransaction, PIPE, MerchantPIPE, MerchantAccountBalance
from Models.models3 import MerchantAPILogs
from Models.PG.schema import PGProdSchema, PGProdMasterCardSchema
from app.auth import decrypt_merchant_secret_key
from app.generateID import (
            base64_decode, calculate_sha256_string, 
            generate_base64_encode, generate_unique_id
          )
from app.controllers.PG.paymentFormProcess import ProcessPaymentFormTransaction
from app.controllers.PG.APILogs import createNewAPILogs
from app.controllers.controllers import post, get
from app.controllers.PG.Mastercard.mastercard import (
    Create_Session, Update_Session, 
    Initiate_Authentication, send_webhook_response,
    MasterCardWebhookPayload, deduct_amount, Mastercard_Transaction_Status)
from app.controllers.PG.merchantTransaction import CalculateMerchantAccountBalance
from sqlmodel import select, and_
from datetime import timedelta
import json
import re




is_development = config('IS_DEVELOPMENT')



# URL according to Environment
if is_development == 'True':
    url         = 'http://localhost:5173'
    redirectURL = 'https://dec7-122-176-92-114.ngrok-free.app/api/mastercard/redirect/response/url'

else:
    url = 'https://react-payment.oyefin.com'
    redirectURL = 'https://python-uat.oyefin.com/api/mastercard/redirect/response/url'




##########################################
## Production Payment to initiate the payment
##########################################
class PaymentGatewayProductionAPI(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'PG Production API'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/pg/prod/v1/pay/'
    

    @post()
    async def create_order(request: Request, schema: PGProdSchema, form_id: str = '') -> Response:
        """
          This API Endpoint Initiate a payment request in production environment. 
          It performs various validations, checks, and database operations to process a payment request in a production environment.<br/><br/>
             - The method starts by extracting the necessary headers and payload from the incoming request. It then validates the payload, checks the merchant's key, and performs various checks to ensure the payment request is valid.<br/>
             - If all validations pass, the method saves the transaction details into the database and returns a JSON response with the necessary information for the merchant to redirect their customers to the payment gateway.<br/><br/>

          Parameters:<br/>
              - request(Request): The HTTP request object containing the user's identity and payload data.<br/>
              - schema(PGProdSchema): The schema object containing the required fields for creating a payment request in production environment.<br/>
              - form_id(str): Optional parameter to specify the form ID for the payment request while making payment through payment form.<br/><br/>

         Returns:<br/>
              - JSON response with success status, message, and necessary data for the merchant to redirect their customers to the payment gateway.<br/>
              - JSON response with error status and message if an exception occurs.<br/><br/>

          Error Messages:<br/>
            - 'Missing Header: X-AUTH': If the 'X-AUTH' header is missing in the incoming request.<br/>
            - 'Incorrect X-AUTH header': If the provided 'X-AUTH' header is invalid.<br/>
            - 'Invalid merchantPublicKey': If the provided merchant public key is invalid.<br/>
            - 'Missing Parameter: paymentInstrument'  - If the provided payment instrument is missing.<br/>
            - Amount should be greater than 0 - If the provided amount is less than 0.<br/>
            - Incorrect paymentInstrument type - If the provided payment instrument type is invalid.<br/>
            - Key is in Sandbox mode, Please activate the key - If the provided key is in sandbox mode.<br/>
            - Inactive key, Please contact administrations - If the provided key is inactive.<br/>
            - No Active Acquirer assigned, Please contact administration - If No Active Acquirer assigned.<br/>
            - Duplicate merchantOrderId - If the provided merchant order id is duplicated.<br/>
        """
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


                ## Get all the data from Payload
                merchant_public_key = payload_dict.get('merchantPublicKey')
                merchant_secret_key = payload_dict.get('merchantSecretKey') 
                merchant_order_id   = payload_dict.get('merchantOrderId')   
                currency            = payload_dict.get('currency')
                amount              = payload_dict.get('amount')
                redirect_url        = payload_dict.get('redirectUrl')
                callback_url        = payload_dict.get('callbackUrl')
                mobile_number       = payload_dict.get('mobileNumber')
                business_name       = payload_dict.get('BusinessName')
                payment_type        = payload_dict.get('paymentInstrument')


                if not business_name:
                    business_name = ''

                # Get the Secrect key and public key data of the merchant
                merchant_key_obj = await session.execute(select(UserKeys).where(
                    UserKeys.public_key == merchant_public_key
                ))
                merchant_key = merchant_key_obj.scalar()

                if not merchant_key:

                    return pretty_json({'error': {
                        "success": False,
                        "status": "PAYMENT_PROCESSING",
                        "message":  "Invalid merchantPublicKey",
                    }}, 400)
                

                # If transaction amount is 0
                if amount == 0 or amount == 0.00:
                    # Create API Log for the Error
                    api_log_obj = MerchantAPILogs(
                        merchant_id      = merchant_key.user_id,
                        error            = 'Wrong Amount entered, Should be greater than 0 and +ve Integer',
                        end_point        = '/api/pg/prod/v1/pay/',
                        request_header   = header_value,
                        request_body     = payload,
                        response_header  = '',
                        response_body    = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "Amount should be greater than 0"
                            }}
                        )
                    
                    session.add(api_log_obj)
                    await session.commit()
                    await session.refresh(api_log_obj)
                    
                    return pretty_json({'error': {
                        'success': False,
                        'status': 'PAYMENT PROCESSING',
                        "message": "Amount should be greater than 0"
                    }}, 400)
                
                # Validate required fields
                required_fields = ['merchantPublicKey', 'merchantSecretKey', 'merchantOrderId', 'amount', 'redirectUrl', 'currency']
                
                # Missing fields validation
                for field in required_fields:

                    if not payload_dict.get(field):
                        # Create Log for the error
                        response_header = ''
                        response_body = {'error': {
                                    'success': False,
                                    'status': 'PAYMENT_PROCESSING',
                                    "message": f'Missing Parameter {field}'
                                }}
                        
                        await createNewAPILogs(
                            merchant_key.user_id,
                            f'Missing Parameter {field}',
                            '/api/pg/prod/v1/pay/',
                            header_value,
                            payload,
                            response_header,
                            response_body
                        )

                        return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message":  f'Missing Parameter: {field}',
                        }}, 400)

                # If Payment type is not present in payload
                if not payment_type:

                    # Create Log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": f'Missing Parameter {field}'
                            }}
                    
                    await createNewAPILogs(
                        merchant_key.user_id,
                        'Missing Parameter: paymentInstrument',
                        '/api/pg/prod/v1/pay/',
                        header_value,
                        payload,
                        response_header,
                        response_body
                    )

                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message":  "Missing Parameter: paymentInstrument",
                        }}, 400)
                

                # If paymentInstrument.type is not present
                if not payment_type['type']:
                    # Create Log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": 'Missing Parameter: paymentInstrument.type'
                            }}
                    
                    await createNewAPILogs(
                        merchant_key.user_id,
                        'Incorrect paymentInstrument.type',
                        '/api/pg/prod/v1/pay/',
                        header_value,
                        payload,
                        response_header,
                        response_body
                    )

                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message":  "Missing Parameter: paymentInstrument.type"
                        }}, 400)
                

                # If payment Instrument type is not PAY_PAGE
                if payment_type['type'] != 'PAY_PAGE':
                    # Create Log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": 'Incorrect paymentInstrument.type'
                            }}
                    
                    await createNewAPILogs(
                        merchant_key.user_id,
                        'Incorrect paymentInstrument.type',
                        '/api/pg/prod/v1/pay/',
                        header_value,
                        payload,
                        response_header,
                        response_body
                    )

                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message":  "Incorrect paymentInstrument type"
                        }}, 400)
                

                # If payment done through Form
                if form_id:
                    # process Transaction for Payment forms
                    return await ProcessPaymentFormTransaction(
                        header_value, merchant_public_key, amount, payload_dict,
                        payload, currency, payment_type, mobile_number, merchant_secret_key, 
                        merchant_order_id, redirect_url, business_name
                    )
                
                # Decrypt Merchant secret key
                merchant_secret_key = await decrypt_merchant_secret_key(merchant_secret_key)

                
                # Public Key & Merchant ID
                merchant_public_key = merchant_key.public_key
                merchant_id         = merchant_key.user_id

                merchant_key_status = merchant_key.is_active

                # IF merchant key is not active
                if merchant_key_status == False:
                    # Create Log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "Key is in Sandbox mode, Please activate the key"
                            }}
                    
                    await createNewAPILogs(
                        merchant_key.user_id,
                        "Key is in Sandbox mode, Please activate the key",
                        '/api/pg/prod/v1/pay/',
                        header_value,
                        payload,
                        response_header,
                        response_body
                    )


                    return pretty_json({'error': {
                        "success": False,
                        "status": "PAYMENT_PROCESSING",
                        "message":  "Inactive key, Please contact administrations",
                    }}, 400)
                

                # Verify header X-AUTH
                sha256   = calculate_sha256_string(payload + '/api/pg/prod/v1/pay/' + merchant_key.secret_key)
                checksum = sha256 + '****' + INDEX

                 # Validate header value
                if checksum != header_value:
                    # Create log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "Incorrect X-AUTH header"
                            }}
                    
                    await createNewAPILogs(merchant_key.user_id, "Incorrect X-AUTH header", '/api/pg/prod/v1/pay/',
                                            header_value, payload, response_header, response_body
                                )


                    return pretty_json({'error': {
                        "success": False,
                        "status": "PAYMENT_PROCESSING",
                        "message":  "Incorrect X-AUTH header",
                    }}, 400)
                

                if currency != 'USD':
                    # Create log for for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "Invalid Currency: Only USD Accepted"
                            }}
                    
                    await createNewAPILogs(merchant_key.user_id, "Invalid Currency: Only USD Accepted", '/api/pg/prod/v1/pay/',
                                            header_value, payload, response_header, response_body
                                )
                    
                    return pretty_json({'error': {
                        "success": False,
                        "status": "PAYMENT_PROCESSING",
                        "message":  "Invalid Currency: Only USD Accepted",
                    }}, 400)
                

                # Check Merchant pipe
                merchant_pipe_assigned_obj = await session.execute(select(MerchantPIPE).where(
                    and_(MerchantPIPE.merchant == merchant_key.user_id, MerchantPIPE.is_active == True)
                ))
                merchant_pipe_assigned = merchant_pipe_assigned_obj.scalars().all()

                if not merchant_pipe_assigned:
                    # Create log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "No Active Acquirer assigned, Please contact administration"
                            }}
                    
                    await createNewAPILogs(merchant_key.user_id, "No Active Acquirer available, Please contact administration", '/api/pg/prod/v1/pay/',
                                            header_value, payload, response_header, response_body
                                )
                    
                    return pretty_json({'error': {
                        "success": False,
                        "status": "PAYMENT_PROCESSING",
                        "message":  "No Active Acquirer available, Please contact administration",
                    }}, 400)
                

                # Merchant order ID unique check
                merchant_order_id_validation_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(
                        MerchantProdTransaction.merchantOrderId == merchant_order_id,
                        MerchantProdTransaction.merchant_id     == merchant_key.user_id
                        )
                ))
                merchant_order_id_validation_ = merchant_order_id_validation_obj.scalar()

                if merchant_order_id_validation_:
                    # Create Log for the error
                    response_header = ''
                    response_body = {'error': {
                                'success': False,
                                'status': 'PAYMENT_PROCESSING',
                                "message": "Duplicate merchantOrderId"
                            }}
                    
                    await createNewAPILogs(merchant_key.user_id, "Duplicate merchantOrderId", '/api/pg/prod/v1/pay/',
                                            header_value, payload, response_header, response_body
                                )
                    
                    return pretty_json({'error': {
                            "success": False,
                            "status": "PAYMENT_PROCESSING",
                            "message":  "Please provide unique order ID",
                            "data": {
                                "merchantPublicKey": merchant_public_key if merchant_public_key else '',
                                "merchantOrderId": merchant_order_id if merchant_order_id else '',
                                "amount": amount if amount else '',
                            }
                        }}, 400)


                # Save the Merchant Sandbox Transaction details
                exact_amount = amount / 100
                unique_transaction_id = generate_unique_id()
                
                # Save the transaction into database
                merchant_prod_transaction = MerchantProdTransaction(
                    merchant_id          = merchant_id,
                    status               = 'PAYMENT_INITIATED',
                    currency             = currency,
                    amount               = exact_amount,
                    merchantOrderId      = merchant_order_id,
                    merchantRedirectURl  = redirect_url,
                    merchantRedirectMode = "REDIRECT",
                    merchantCallBackURL  = callback_url,
                    merchantMobileNumber = mobile_number,
                    merchantPaymentType  = payment_type['type'],
                    transaction_id       = unique_transaction_id,
                    is_completd          = False,
                    gateway_res          = '',
                    business_name        = business_name    
                )
                
                session.add(merchant_prod_transaction)
                await session.commit()
                await session.refresh(merchant_prod_transaction)
                

                # Encode the ID's
                encoded_merchant_public_key = generate_base64_encode(merchant_public_key)
                encoded_amount              = generate_base64_encode(exact_amount)
                encodedBusinessName         = generate_base64_encode(business_name)
                encodedTransactionID        = generate_base64_encode(merchant_prod_transaction.transaction_id)
                encodedCurrency             = generate_base64_encode(currency)

                return pretty_json({
                        "success": True,
                        "status": "PAYMENT_INITIATED",
                        "message": "Payment Initiated",
                        "data": {
                            "merchantPublicKey": merchant_public_key,
                            "merchantOrderId": merchant_order_id,
                            "transactionID":  merchant_prod_transaction.transaction_id,
                            "amount": exact_amount,
                            'time': merchant_prod_transaction.createdAt,
                            'currency': merchant_prod_transaction.currency,
                            "instrumentResponse": {
                                "type": "PAY_PAGE",
                                "redirectInfo": {
                                    "url": f"{checkout_url}/merchant/payment/checkout/?token={encoded_merchant_public_key},{encoded_amount},{encodedTransactionID},{encodedCurrency},{encodedBusinessName}",
                                }
                            }
                        }
                    }, 200)

        except Exception as e:
            return pretty_json({'error': 'Unknown Error Occured', 'message': f'{str(e)}'}, 500)

        



# Master Card Transaction Process
class MasterCardTransaction(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Mastercard Transactions' 
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/pg/prod/v1/pay/mc/'
    

    @post()
    async def create_mastercard_transaction(request: Request, schema: PGProdMasterCardSchema):
        """
            This API Endpoint handles the creation of a Mastercard transaction, including decoding card
            details, checking transaction status, initiating authentication, and handling various error
            scenarios.<br/><br/>

            Parameters:<br/>
                - request(Request): The request object to be used to create a Mastercard transaction.<br/>
                - schema(PGProdMasterCardSchema): The schema object to be used to validate and extract data from the request payload.<br/><br/>

            Procedures:<br/>
                1. Decode the card details from the request payload.<br/>
                2. Check if the required fields are present in the decoded payload.<br/>
                3. Check if the merchant production transaction is found and initiated.<br/>
                4. Check if the transaction has already been completed.<br/>
                5. If all the conditions are met, initiate the Mastercard transaction process.<br/>
                6. Handle various error scenarios, such as invalid card details, authentication failures,
                   or webhook errors.<br/>
                7. If the Mastercard transaction is successful, create a new API logs entry.<br/>
                8. Return the appropriate JSON response based on the transaction status.<br/><br/>

            Returns:<br/>
            - JSON response containing the Mastercard transaction details and the status of the transaction.<br/><br/>
            
            Raises:<br/>
                1. Error message for missing parameters if required fields are not present in the decoded
                    payload.<br/>
                2. Error message if the merchant production transaction is not found or not initiated.<br/>
                3. Error message if the transaction has already been completed.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                request_payload = schema.request
                redirect_url    = redirectURL

                # Decode the card details
                decode_payload = base64_decode(request_payload)
                decoded_dict   = json.loads(decode_payload)

                # Get the payload data
                card_no           = decoded_dict.get('cardNumber')
                card_expiry       = decoded_dict.get('cardExpiry')
                card_cvv          = decoded_dict.get('cardCvv')
                card_name         = decoded_dict.get('cardHolderName')
                
                merchant_transaction_id = decoded_dict.get('MerchantTransactionId')

                required_fields = ['cardNumber', 'cardExpiry', 'cardCvv', 'cardHolderName']

                missing_fields = [field for field in required_fields if field not in decoded_dict]

                if missing_fields:
                    return pretty_json({'error': f'Missing Parameter {", ".join(missing_fields)}'}, 400)
                
                # Get the merchant production Transaction
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                        MerchantProdTransaction.transaction_id == merchant_transaction_id
                ))
                merchant_prod_transaction = merchant_prod_transaction_obj.scalar()

                if not merchant_prod_transaction:
                    return pretty_json({'error': 'Please initiate transaction'}, 400)
                
                merchant_order_id = merchant_prod_transaction.merchantOrderId

                # Check transaction status
                trasnaction_status = merchant_prod_transaction.is_completd

                # If the transaction has been completed
                if trasnaction_status:
                    return pretty_json({'error': 'Transaction has been closed'}, 400)

                # Get The Merchant Public key
                merchant_key_obj = await session.execute(select(UserKeys).where(
                    UserKeys.user_id == merchant_prod_transaction.merchant_id
                ))
                merchant_key_ = merchant_key_obj.scalars().first()
                
                if not merchant_key_:
                    return pretty_json({'error': 'Merchant Public key not found'}, 404)
                
                # Transaction ID and amount sent to master card
                transaction_id = merchant_prod_transaction.transaction_id
                amount         = merchant_prod_transaction.amount
                currency       = merchant_prod_transaction.currency

                # Merchant Public Key
                merchantPublicKey = merchant_key_.public_key

                #Merchant Redirect URL and Redirect Mode
                merchantRedirectURL  = merchant_prod_transaction.merchantRedirectURl
               
                merchantCallBackURL  = merchant_prod_transaction.merchantCallBackURL

                # Get the pipe which payment medium is card
                # card_pipe_obj = await session.execute(select(PIPE).where(
                #     PIPE.payment_medium == 'Card'
                # ))
                # card_pipe = card_pipe_obj.scalar()

                # if card_pipe:
                #     # Get the pipe assigned to the merchant
                #     merchant_assigned_pipe_obj = await session.execute(select(MerchantPIPE).where(
                #         and_(MerchantPIPE.merchant == merchant_prod_transaction.merchant_id,
                #             MerchantPIPE.is_active == True,
                #             MerchantPIPE.pipe      == card_pipe.id
                #             )
                #     ))
                #     merchant_assigned_pipe = merchant_assigned_pipe_obj.scalar()
                # else:

                # Get the pipe assigned to the merchant
                merchant_assigned_pipe_obj = await session.execute(select(MerchantPIPE).where(
                    and_(
                        MerchantPIPE.merchant == merchant_prod_transaction.merchant_id,
                        MerchantPIPE.is_active == True,
                        )
                    ))
                merchant_assigned_pipe = merchant_assigned_pipe_obj.scalar()

                ## Get The settlement period of the assigned pipe
                pipe_id_obj = await session.execute(select(PIPE).where(
                    PIPE.id == merchant_assigned_pipe.pipe
                ))
                pipe_id = pipe_id_obj.scalar()

                # Calculate settlement date
                pipe_settlement_period  = pipe_id.settlement_period
                numeric_period          = re.findall(r'\d+', pipe_settlement_period)

                if numeric_period:
                    settlement_period_value = int(numeric_period[0])
                else:
                    settlement_period_value = 0

                # Calculate settlement date
                transaction_date            = merchant_prod_transaction.createdAt
                transaction_settlement_date = transaction_date + timedelta(days=settlement_period_value)


                ## If not acquirer assigned
                ## if not merchant_assigned_pipe:
                ##     return pretty_json({'error': 'pipe with payment medium card is not available'}, 400)

                ## Master card Transaction started
                ## Create session
                mastercard_session = Create_Session()
                session_result     = mastercard_session.get('result')

                if session_result == 'SUCCESS':
                    sessionID = mastercard_session.get('session')['id']

                    ### Update session
                    update_session = Update_Session(sessionID, transaction_id, card_no, card_cvv, card_expiry, currency, amount, redirect_url)

                    if update_session.get('session')['updateStatus'] == 'SUCCESS':

                        # Calculate transaction fee amount
                        transaction_fee_amount = (merchant_prod_transaction.amount / 100) * merchant_assigned_pipe.fee

                        # Store json response in transaction
                        merchant_prod_transaction.gateway_res          = update_session
                        merchant_prod_transaction.payment_mode         = 'Card'
                        merchant_prod_transaction.pipe_id              = merchant_assigned_pipe.pipe if merchant_assigned_pipe.pipe else 0
                        merchant_prod_transaction.transaction_fee      = merchant_assigned_pipe.fee if merchant_assigned_pipe.fee else 0
                        merchant_prod_transaction.fee_amount           = transaction_fee_amount
                        merchant_prod_transaction.pg_settlement_period = pipe_settlement_period
                        merchant_prod_transaction.pg_settlement_date   = transaction_settlement_date
                        merchant_prod_transaction.balance_status       = "Immature"


                        session.add(merchant_prod_transaction)
                        await session.commit()
                        await session.refresh(merchant_prod_transaction)

                        # Initiate Authentication
                        initiate_auth = Initiate_Authentication(transaction_id, sessionID, currency)

                        if initiate_auth.get('result') == 'SUCCESS' and initiate_auth.get('response')['gatewayCode'] == 'AUTHENTICATION_IN_PROGRESS':

                            # Response to page
                            return pretty_json({
                                    'status': 'AUTHENTICATION_IN_PROGRESS',
                                    'session': sessionID,
                                    'transactionID': transaction_id
                                }, 200)
                        
                        
                        if initiate_auth.get('result') == 'FAILURE' and initiate_auth.get('response')['gatewayCode'] == 'DECLINED':
                            # Send Webhook URL for Authentication Error
                            if merchantCallBackURL:
                                webhook_payload_dict = {
                                    "success": False,
                                    "status": "PAYMENT_FAILED",
                                    "message": initiate_auth.get('response')['gatewayRecommendation'],
                                    "data": {
                                        "merchantPublicKey": merchantPublicKey,
                                        "merchantOrderId": merchant_order_id,
                                        "transactionId":'',
                                        "time": '',
                                        "instrumentResponse": {
                                            "type": "PAY_PAGE",
                                                "redirectInfo": {
                                                "url": merchantRedirectURL,
                                        }
                                        }
                                    }
                                }
                                
                                webhook_payload = MasterCardWebhookPayload(
                                    success = webhook_payload_dict['success'],
                                    status  = webhook_payload_dict["status"],
                                    message = webhook_payload_dict["message"],
                                    data    = webhook_payload_dict["data"]
                                )

                                await send_webhook_response(webhook_payload, merchantCallBackURL)

                            # Update the merchant transaction status
                            merchant_prod_transaction.status       = 'PAYMENT_FAILED'
                            merchant_prod_transaction.payment_mode = 'Card'
                            merchant_prod_transaction.gateway_res  = initiate_auth


                            session.add(merchant_prod_transaction)
                            await session.commit()
                            await session.refresh(merchant_prod_transaction)

                            # Response to the page
                            return pretty_json({
                                'status': 'PAYMENT_FAILED',
                                'message': initiate_auth.get('response')['gatewayRecommendation'],
                                'transactionID': transaction_id,
                                'merchantRedirectURL': merchantRedirectURL
                            }, 400)

                        else:
                            # Send Webhook URL for Authentication Error
                            if merchantCallBackURL:
                                webhook_payload_dict = {
                                    "success": False,
                                    "status": "PAYMENT_FAILED",
                                    "message": initiate_auth['error']['error']['explanation'],
                                    "data": {
                                        "merchantPublicKey": merchantPublicKey,
                                        "merchantOrderId": merchant_order_id,
                                        "transactionId":'',
                                        "time": '',
                                        "instrumentResponse": {
                                            "type": "PAY_PAGE",
                                                "redirectInfo": {
                                                "url": merchantRedirectURL,
                                        }
                                        }
                                    }
                                }
                                
                                webhook_payload = MasterCardWebhookPayload(
                                    success = webhook_payload_dict['success'],
                                    status  = webhook_payload_dict["status"],
                                    message = webhook_payload_dict["message"],
                                    data    = webhook_payload_dict["data"]
                                )

                                await send_webhook_response(webhook_payload, merchantCallBackURL)

                            # Update the merchant transaction status
                            merchant_prod_transaction.status       = 'PAYMENT_FAILED'
                            merchant_prod_transaction.payment_mode = 'Card'
                            merchant_prod_transaction.gateway_res  = initiate_auth


                            session.add(merchant_prod_transaction)
                            await session.commit()
                            await session.refresh(merchant_prod_transaction)

                            # Response to the page
                            return pretty_json({
                                'status': 'PAYMENT_FAILED',
                                'message': initiate_auth['error']['error']['explanation'],
                                'transactionID': transaction_id,
                                'merchantRedirectURL': merchantRedirectURL
                            }, 400)

                    else:
                        # Send webhook url if present for Update session error

                        if merchantCallBackURL:
                            webhook_payload_dict = {
                                "success": False,
                                "status": "PAYMENT_FAILED",
                                "message": 'To be updated',
                                "data": {
                                    "merchantPublicKey": merchantPublicKey,
                                    "merchantOrderId": merchant_order_id,
                                    "transactionId":'',
                                    "time": '',
                                    "instrumentResponse": {
                                        "type": "PAY_PAGE",
                                            "redirectInfo": {
                                            "url": merchantRedirectURL,
                                    }
                                    }
                                }
                            }
                            
                            webhook_payload = MasterCardWebhookPayload(
                                success = webhook_payload_dict['success'],
                                status  = webhook_payload_dict["status"],
                                message = webhook_payload_dict["message"],
                                data    = webhook_payload_dict["data"]
                            )

                            await send_webhook_response(webhook_payload, merchantCallBackURL)

                        # Update the merchant transaction status
                        merchant_prod_transaction.status      = 'PAYMENT_FAILED'
                        merchant_prod_transaction.payment_mode = 'Card'

                        session.add(merchant_prod_transaction)
                        await session.commit()
                        await session.refresh(merchant_prod_transaction)
                        
                        # Response for the page
                        return pretty_json({
                            'status': 'PAYMENT_FAILED',
                            'message': 'To be Updated',
                            'transactionID': transaction_id,
                            'merchantRedirectURL': merchantRedirectURL
                        }, 400)
                    
                else:
                    # Send webhook url if present for Session create error 
                    if merchantCallBackURL:
                        webhook_payload_dict = {
                            "success": False,
                            "status": "PAYMENT_FAILED",
                            "message": initiate_auth['error']['error']['explanation'],
                            "data": {
                                "merchantPublicKey": merchantPublicKey,
                                "merchantOrderId": merchant_order_id,
                                "transactionID":'',
                                "time": '',
                                "instrumentResponse": {
                                    "type": "PAY_PAGE",
                                        "redirectInfo": {
                                        "url": merchantRedirectURL,
                                    }
                                }
                            }
                        }
                        
                        webhook_payload = MasterCardWebhookPayload(
                            success = webhook_payload_dict['success'],
                            status  = webhook_payload_dict["status"],
                            message = webhook_payload_dict["message"],
                            data    = webhook_payload_dict["data"]
                        )

                        await send_webhook_response(webhook_payload, merchantCallBackURL)
                        
                    # Update the merchant transaction status
                    merchant_prod_transaction.status       = 'PAYMENT_FAILED'
                    merchant_prod_transaction.payment_mode = 'Card'
                    merchant_prod_transaction.pipe_id      = merchant_assigned_pipe.pipe
                    
                    session.add(merchant_prod_transaction)
                    await session.commit()
                    await session.refresh(merchant_prod_transaction)

                    # Response for the page
                    return pretty_json({
                        'status':  'PAYMENT_FAILED',
                        'message': 'To be Updated',
                        'transactionID': transaction_id,
                        'merchantRedirectURL': merchantRedirectURL
                    }, 400)

        except Exception as e:
            return pretty_json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)



####################################
# Mastercard webhook response format
####################################
# print('json',json_data)
# print('\n')
# print('auth',          json_data['authentication'])
# print('\n')
# print('transactionID', json_data['authentication']['3ds']['transactionId'])
# print('\n')
# print('response',      json_data['response'])
# print('\n')
class ReceiveMasterCardWebhook(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "Mastercard Webhook"

    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/prod/mastercard/webhook/'
    
    @post()
    async def mastercard_webhook(request: Request):
        """
            The API Endpoint processes webhook data for Mastercard transactions and updates the status of the transaction accordingly.<br/><br/>

            Parameters:<br/>
                - request (Request): The incoming POST request containing webhook data from Mastercard.<br/>
                - redirectURL (str): The URL to redirect the user after processing the response.<br/>
            
            Includes:<br/>
                - send_webhook_response: A function that sends a webhook response to the specified URL.<br/>
                - MasterCardWebhookPayload: A class representing the structure of the webhook data from Mastercard.<br/>
                - deduct_amount: A function that deducts the amount from the user's account.<br/>
                - CalculateMerchantAccountBalance: A function that calculates the new balance for the merchant's account.<br/>
                - UserKeys: The database model representing the user keys.<br/>
                - MerchantProdTransaction: The database model representing the merchant transactions.<br/>
                - AsyncSession: The asynchronous session for interacting with the database.<br/>
                - select: The SQLModel function for selecting data from the database.<br/>
                - and_: The SQLModel function for combining conditions.<br/><br/>
            
            Procedures:<br/>
                1. Extract the necessary data from the mastercard webhook payload.<br/>
                2. Check if the transaction status is "CAPTURED" and the gateway code is "00" (Success).<br/>
                3. If the transaction status is "CAPTURED" and the gateway code is "00", update the transaction status in the database.<br/>
                4. If the transaction status is "CAPTURED" and the gateway code is "00", update the user's account balance.<br/>
                5. Send a webhook response to the specified URL with the updated transaction status and user account balance.<br/>
                6. Return a JSON response with the updated transaction status and user account balance.<br/>
                7. gateway_code is DECLINED and authentication_status is AUTHENTICATION_UNSUCCESSFUL send a webhook response to the specified URL with the updated transaction status.<br/>
                8. gateway_code is PENDING and authentication_status is AUTHENTICATION_INITIATED send a webhook response to the specified URL with the updated transaction status.<br/><br/>

            Webhook Response:<br/>
                - Send a webhook response to the specified URL with the updated transaction status after receiving response form mastercard.<br/><br/> 

            Returns:<br/>
            - json: A JSON response containing the updated transaction status and user account balance.<br/>
            - 400: If the 'order' ID is not available in the webhook data.<br/>
            - 500: If there is a server error during the webhook response process.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                json_data = await request.json()

                response_data = json_data.get('response', {})
                gateway_code  = response_data.get('gatewayCode')
                order_data    = json_data.get('order')
                result        = json_data.get('result')
                authentication_status = order_data.get('status')
                # print('\n')
                # print('gateway code', gateway_code)
                # print('\n')
                # print('transaction id', json_data['order']['id'])

                transaction_id = json_data['order']['id']

                if transaction_id:
                    # Get the merchant transaction
                    merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                        MerchantProdTransaction.transaction_id == transaction_id
                    ))
                    merchant_transaction  = merchant_transaction_obj.scalar()
                    
                    merchant_webhook_url  = merchant_transaction.merchantCallBackURL
                    merchant_redirect_url = merchant_transaction.merchantRedirectURl # Merchant Redirect url
                    merchant_order_id     = merchant_transaction.merchantOrderId   # Merchant Order ID
                    transactionId         = merchant_transaction.transaction_id # Transaction ID
                    transactionTime       = merchant_transaction.createdAt   # Transaction Time
                    transactionAmount     = merchant_transaction.amount
                    transactionCurrency   = merchant_transaction.currency

                    merchantPipeFee         = merchant_transaction.transaction_fee
                    merchantID              = merchant_transaction.merchant_id

                else:
                    return pretty_json({'error': "['order']['id'] not available"}, 400)
                

                # Webhook response after successful(OTP Page) authentication
                if gateway_code == 'APPROVED' and authentication_status == 'AUTHENTICATION_SUCCESSFUL' and result == 'SUCCESS':

                    # Get the merchant public key
                    if merchant_transaction:
                        
                        # Get merchant Public key and secret keys
                        merchant_key_obj = await session.execute(select(UserKeys).where(
                            UserKeys.user_id == merchant_transaction.merchant_id
                        ))
                        merchant_key_ = merchant_key_obj.scalar()

                        if not merchant_key_:
                            return pretty_json({'msg': 'Merchant donot have any assigned key'}, 400)
                        
                        # Merchant Public Key
                        merchantPublicKey = merchant_key_.public_key

                        # Fetch the session ID from the saved log
                        gateway_data_dict = merchant_transaction.gateway_res
                        sessionID         = gateway_data_dict["session"]["id"]

                        # Last process to deduct the amount
                        deduct = deduct_amount(transaction_id, sessionID)

                        response     = deduct.get('response', {})
                        gateway_code = response.get('gatewayCode')

                        # If the payment Succeeded
                        if deduct.get('result') == 'SUCCESS' and gateway_code == 'APPROVED' and response_data['acquirerMessage'] == 'Approved' and response_data['acquirerCode'] == '00':
                            
                            # Account balance update for merchant
                            if not merchant_transaction.is_completd:
                                await CalculateMerchantAccountBalance(transactionAmount, transactionCurrency, merchantPipeFee, merchantID)

                            merchant_transaction.status      = 'PAYMENT_SUCCESS'
                            merchant_transaction.is_completd = True
                            merchant_transaction.gateway_res = deduct

                            if merchant_webhook_url:
                                webhook_payload_dict = {
                                    "success": True,
                                    "status": "PAYMENT_SUCCESS",
                                    "message": 'Transaction Successful',
                                    "data": {
                                        "merchantPublicKey": merchantPublicKey,
                                        "merchantOrderId": merchant_order_id,
                                        'transactionID': transactionId,
                                        'time': str(transactionTime),
                                        "paymentInstrument": {
                                            "type": "Card"
                                        }
                                    }
                                }
                            
                                webhook_payload = MasterCardWebhookPayload(
                                    success = webhook_payload_dict['success'],
                                    status  = webhook_payload_dict["status"],
                                    message = webhook_payload_dict["message"],
                                    data    = webhook_payload_dict["data"]
                                )

                                # Send webhook
                                await send_webhook_response(webhook_payload, merchant_webhook_url)


                            # Calculate Payout balance of the Merchant
                            # Update Account balance of the merchant
                            session.add(merchant_transaction)
                            await session.commit()
                            await session.refresh(merchant_transaction)

                            return pretty_json({'msg': 'success'}, 200)

                        # If the payment Failed
                        elif deduct.get('result') == 'FAILURE':
                            
                            merchant_transaction.status = 'PAYMENT_FAILED'
                            merchant_transaction.is_completd = True
                            merchant_transaction.gateway_res = deduct

                            session.add(merchant_transaction)
                            await session.commit()
                            await session.refresh(merchant_transaction)

                            return pretty_json({'msg': 'success'}, 200)
                        
                        # If the transaction is pending
                        elif deduct.get('result') == 'PENDING':
                            merchant_transaction.status      = 'PAYMENT_PENDING'
                            merchant_transaction.is_completd = True
                            merchant_transaction.gateway_res = deduct

                            session.add(merchant_transaction)
                            await session.commit()
                            await session.refresh(merchant_transaction)

                            return pretty_json({'msg': 'success'}, 200)
                        
                        else:
                            return pretty_json({'msg': 'success'}, 200)
                
                # If Webhook response is Pending after authentication
                elif gateway_code == 'PENDING' and authentication_status == 'AUTHENTICATION_INITIATED' and result == 'PENDING':

                    if merchant_transaction:
                            # Get merchant Public key and secret keys
                        merchant_key_obj = await session.execute(select(UserKeys).where(
                            UserKeys.user_id == merchant_transaction.merchant_id
                        ))
                        merchant_key_ = merchant_key_obj.scalar()

                        # Merchant Public Key
                        merchantPublicKey = merchant_key_.public_key

                    if merchant_webhook_url:
                        webhook_payload_dict = {
                                "success": False,
                                "status": "PAYMENT_PENDING",
                                "message": 'Transaction Pending',
                                "data": {
                                    "merchantPublicKey": merchantPublicKey,
                                    "merchantOrderId": merchant_order_id,
                                    'transactionID': transactionId,
                                    'time': str(transactionTime),
                                    "paymentInstrument": {
                                        "type": "Card"
                                    }
                                }
                            }
                        
                        webhook_payload = MasterCardWebhookPayload(
                            success = webhook_payload_dict['success'],
                            status  = webhook_payload_dict["status"],
                            message = webhook_payload_dict["message"],
                            data    = webhook_payload_dict["data"]
                        )

                        # Send webhook
                        await send_webhook_response(webhook_payload, merchant_webhook_url)

                    merchant_transaction.status      = 'PAYMENT_PENDING'
                    merchant_transaction.gateway_res = json_data

                    session.add(merchant_transaction)
                    await session.commit()
                    await session.refresh(merchant_transaction)

                    return pretty_json({'msg': 'success'}, 200)
                        
                # If webhook response is declined after authentication
                elif gateway_code == 'DECLINED' and authentication_status == 'AUTHENTICATION_UNSUCCESSFUL' and result == 'FAILURE':

                    if merchant_transaction:
                        # Get merchant Public key and secret keys
                        merchant_key_obj = await session.execute(select(UserKeys).where(
                            UserKeys.user_id == merchant_transaction.merchant_id
                        ))
                        merchant_key_ = merchant_key_obj.scalar()

                        if not merchant_key_:
                            return pretty_json({'msg': 'Merchant donot have any assigned key'}, 400)
                        
                        # Merchant Public Key
                        merchantPublicKey = merchant_key_.public_key

                    #### Webhook URL
                    if merchant_webhook_url:
                        webhook_payload_dict = {
                                "success": False,
                                "status": "PAYMENT_FAILED",
                                "message": 'Transaction Failed',
                                "data": {
                                    "merchantPublicKey": merchantPublicKey,
                                    "merchantOrderId": merchant_order_id,
                                    'transactionID': transaction_id,
                                    'time': str(transactionTime),
                                    'amount': transactionAmount,
                                    'currency': transactionCurrency,
                                    "paymentInstrument": {
                                        "type": "Card"
                                    }
                                }
                            }
                
                        webhook_payload = MasterCardWebhookPayload(
                            success       = webhook_payload_dict['success'],
                            status        = webhook_payload_dict["status"],
                            message       = webhook_payload_dict["message"],
                            data          = webhook_payload_dict["data"]
                        )

                        await send_webhook_response(webhook_payload, merchant_webhook_url)
                    
                    merchant_transaction.status      = 'PAYMENT_FAILED'
                    merchant_transaction.is_completd = True
                    merchant_transaction.gateway_res = json_data

                    session.add(merchant_transaction)
                    await session.commit()
                    await session.refresh(merchant_transaction)

                    return pretty_json({'msg': 'success'}, 200)
            
                elif response_data['acquirerMessage'] == 'Approved' and response_data['acquirerCode'] == '00' and gateway_code == 'APPROVED' and result == 'SUCCESS':
                    # Get merchant Public key and secret keys
                    merchant_key_obj = await session.execute(select(UserKeys).where(
                        UserKeys.user_id == merchant_transaction.merchant_id
                    ))
                    merchant_key_ = merchant_key_obj.scalar()

                    if not merchant_key_:
                        return pretty_json({'msg': 'Merchant donot have any assigned key'}, 400)
                    
                    # Merchant Public Key
                    merchantPublicKey = merchant_key_.public_key

                    # print('transactionId, test', transactionId)
                    # # send webhook response to merchant about successful transaction 
                    if merchant_webhook_url:
                        webhook_payload_dict = {
                                "success": False,
                                "status": "PAYMENT_SUCCESS",
                                "message": 'Transaction Successfull',
                                "data": {
                                    "merchantPublicKey": merchantPublicKey,
                                    "merchantOrderId": merchant_order_id,
                                    'transactionID': transactionId,
                                    'time': str(transactionTime),
                                    'amount': transactionAmount,
                                    'currency': transactionCurrency,
                                    "paymentInstrument": {
                                            "type": "Card"
                                        }
                                }
                            }
                
                        webhook_payload = MasterCardWebhookPayload(
                            success = webhook_payload_dict['success'],
                            status  = webhook_payload_dict["status"],
                            message = webhook_payload_dict["message"],
                            data    = webhook_payload_dict["data"]
                        )

                        # Send webhook response
                        await send_webhook_response(webhook_payload, merchant_webhook_url)

                    # Update the database
                    merchant_transaction.status      = 'PAYMENT_SUCCESS'
                    merchant_transaction.is_completd = True
                    merchant_transaction.gateway_res = json_data

                    session.add(merchant_transaction)
                    await session.commit()
                    await session.refresh(merchant_transaction)

                    return pretty_json({'msg': 'success'}, 200)

                else:
                    return pretty_json({'msg': 'success'}, 200)

        except Exception as e:
            # print('error', f'{str(e)}')
            return pretty_json({'error': 'Server error', 'msg': f'{str(e)}'}, 500)
        


# Mastercard Transaction Status
class MastercardTransactionStatus(APIController):

    @classmethod
    def class_name(cls) -> str:
        return "Mastercard Transaction Status"
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/prod/mastercard/validate/{id}/'

    @get()
    async def mastercard_transaction_status(request: Request, id: str):
        """
            This API Endpoint retrieves the status of PG production transaction based on the provided transaction ID and includes error handling
            for various scenarios.<br/><br/>

            Parameters:<br/>
               - request: The HTTP request object.<br/>
               - id: The unique identifier of the PG transaction,for which the transaction status needs to be retrieved.<br/><br/>

            Returns:<br/>
            - JSON: A JSON response containing the transaction status, error message, and merchant redirect URL if available.<br/>
            - Error: A JSON response with an error message if the transaction ID is invalid or the transaction status cannot be retrieved.<br/><br/>

            Raises:<br/>
            - Exception: If any error occurs during the database query or response generation.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                transaction_id = id

                # Get merchant production transaction
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.transaction_id == transaction_id
                ))
                merchant_transaction = merchant_transaction_obj.scalar()

                merchant_redirct_url   = merchant_transaction.merchantRedirectURl
                # merchant_redirect_mode = merchant_transaction.merchantRedirectMode

                if merchant_redirct_url:
                    merchant_redirct_url   = merchant_redirct_url
                    # merchant_redirect_mode = merchant_redirect_mode
                else:
                    # merchant_redirect_mode = None
                    merchant_redirct_url   = None


                if transaction_id == 'null':
                    return pretty_json({'error': 'Please provide Transaction ID'}, 400)
                
                elif transaction_id:
                    transaction_status = Mastercard_Transaction_Status(transaction_id)

                    result           = transaction_status['result']
                    gateway_response = transaction_status['response']['gatewayCode']

                    return pretty_json({
                        'result': result, 
                        'gateway_response': gateway_response,
                        'redirect_url': merchant_redirct_url
                        }, 200)
                else:
                    
                    return pretty_json({'error': 'Please provide Transaction ID'}, 400)

        except Exception as e:
            return pretty_json({'error': 'Server Error', 'msg': f'{str(e)}'}, 500)
        



# Merchant Transaction Status
class MerchantTransactionStatus(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Merchant Transaction Status'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/v1/pg/prod/merchant/transaction/status/{merchant_public_key}/{merchant_order_id}'
    

    @get()
    async def MerchantTransactionStatus(request: Request, merchant_public_key: str, merchant_order_id: str):
        """
            This API Endpoint Retrieve the status of a specific transaction for a given merchant.<br/><br/>

            Parameters:<br/>
             - request: The HTTP request object.<br/>
             - merchant_public_key: The public key of the merchant.<br/>
             - merchant_order_id: The unique identifier of the transaction.<br/>

            Returns:<br/>
             - JSON response containing the transaction status or an error message in case of failure.<br/>
             - Error: A JSON response with an error message if the key is invalid or the transaction status cannot be retrieved.<br/><br/>

            Raises:<br/>
             - Exception: If any error occurs during the database query or response generation.<br/>
             - Error 500: 'error': 'Server Error'.<br/>
        """
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
                    return pretty_json({"error": {
                            "success": False,
                            "message": "Invalid merchantPublicKey"
                        }}, 400)
                
                merchant_id = user_key.user_id

                # Get The transaction of the Merchant
                merchant_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    and_(MerchantProdTransaction.merchantOrderId == merchantOrderID,
                         MerchantProdTransaction.merchant_id     == merchant_id
                         )
                    ))
                merchant_transaction = merchant_transaction_obj.scalar()


                if not merchant_transaction:
                    return pretty_json({"error": {
                            "success": False,
                            "message": "Transaction not found"
                        }}, 404)
                
                payment_status    = merchant_transaction.status
                merchant_order_id = merchant_transaction.merchantOrderId
                transaction_id    = merchant_transaction.transaction_id
                amount            = merchant_transaction.amount
                currency          = merchant_transaction.currency
                payment_mode      = merchant_transaction.payment_mode


                if payment_status == 'PAYMENT_INITIATED':
                    message      = 'Payment Initiated remained to complete the transaction'
                    status       = 'STARTED'
                    responseCode = 'INITIATED'
                    success      = False

                elif payment_status == 'PAYMENT_SUCCESS':
                    message       = 'Payment Successfull'
                    responseCode  = 'SUCCESS'
                    status        = 'COMPLETED'
                    success       = True
                    

                elif payment_status == 'PAYMENT_PENDING':
                    message       = 'Payment Pending'
                    responseCode  = 'PENDING'
                    status        = 'PENDING'
                    success       = False

                elif payment_status == 'PAYMENT_FAILED':
                    message       = 'Payment Failed'
                    responseCode  = 'FAILED'
                    status        = 'FAILED'
                    success       = False

                else:
                    message       = 'PAYMENT_ERROR'
                    responseCode  = 'FAILED'
                    status        = 'FAILED'
                    success       = False


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
                                "status": status,
                                "responseCode": responseCode,
                                "paymentInstrument": {
                                    "type": payment_mode,
                                }
                            }
                        }, 200)
                
        except Exception as e:
            return pretty_json({'error': 'Server Error'}, 500)
        



# Mastercard redirect url after payment
class MasterCardRedirectResponse(APIController):

    @classmethod
    def class_name(cls) -> str:
        return 'Mastercard Redirect API'
    
    @classmethod
    def route(cls) -> str | None:
        return '/api/mastercard/redirect/response/url/'
    

    @post()
    async def receieve_mastercard_response(request: Request):
        """
            This Python function processes a Mastercard response, updates transaction status, and redirects
            based on success or failure.<br/><br/>

            Parameters:<br/>
                - request (Request): The incoming POST request containing form data from Mastercard.<br/>
                - redirectURL (str): The URL to redirect the user after processing the response.<br/>
                - url (str): The URL to redirect the user after processing the response.<br/>
                - is_development (bool): Flag indicating whether the environment is development or not.<br/><br/>

            Returns:<br/>
                - Redirect response to the success or failure URL based on the Mastercard response.<br/>
                - If the result is 'FAILURE', it updates the status of the transaction to 'PAYMENT_FAILED' and redirects to a fail URL. If the result is 'SUCCESS', it updates the status
                  to 'PAYMENT_SUCCESS' and redirects to a success URL. If the result is neither 'FAILURE' nor 'SUCCESS it redirect to the failure URL.<br/>
        """
        try:
            async with AsyncSession(async_engine) as session:
                form_data = await request.form()

                transaction_id = form_data['transaction.id']
                result = form_data['result']

                successFailURL = url

                # get The merchant Transaction
                merchant_prod_transaction_obj = await session.execute(select(MerchantProdTransaction).where(
                    MerchantProdTransaction.transaction_id == transaction_id
                ))
                merchant_prod_transaction = merchant_prod_transaction_obj.scalar()

                # If the response failed
                if result == 'FAILURE':
                    if merchant_prod_transaction:
                        # Get merchant redirect url
                        redirect_url = merchant_prod_transaction.merchantRedirectURl

                        merchant_prod_transaction.status = 'PAYMENT_FAILED'
                        merchant_prod_transaction.is_completd = True

                        return redirect(f'{successFailURL}/merchant/payment/fail/?transaction={transaction_id}&url={redirect_url}')
                    else:
                        redirect_url = ''

                        return redirect(f'{successFailURL}/merchant/payment/fail/?transaction={transaction_id}&url={redirect_url}')
                
                # If The response success
                if result == 'SUCCESS':
                    if merchant_prod_transaction:
                        # Get merchant redirect url
                        redirect_url = merchant_prod_transaction.merchantRedirectURl

                        merchant_prod_transaction.status = 'PAYMENT_SUCCESS'
                        merchant_prod_transaction.is_completd = True

                        return redirect(f'{successFailURL}/merchant/payment/success/?transaction={transaction_id}&url={redirect_url}')
                    else:
                        redirect_url = ''

                    return redirect(f'{successFailURL}/merchant/payment/success/?transaction={transaction_id}&url={redirect_url}')
                
                else:
                    return redirect(f'{successFailURL}/merchant/payment/fail/?transaction={transaction_id}&url={redirect_url}')

                
        except Exception as e:
            return pretty_json({'error': 'Server Error' }, 500)



