from blacksheep import pretty_json
from app.auth import decrypt_merchant_secret_key
from app.generateID import calculate_sha256_string, generate_base64_encode, generate_unique_id
from Models.models import UserKeys
from Models.models2 import MerchantPIPE, MerchantProdTransaction
from database.db import AsyncSession, async_engine
from sqlmodel import select, and_
from decouple import config



is_development = config('IS_DEVELOPMENT')


if is_development == 'True':
    url         = 'http://localhost:5173'

else:
    url = 'https://react-payment.oyefin.com'



# Process payment form transactions
async def ProcessPaymentFormTransaction(header_value, merchant_public_key, amount, payload_dict,
                        payload, currency, payment_type, mobile_number, merchant_secret_key, 
                        merchant_order_id, redirect_url):
    try:
        async with AsyncSession(async_engine) as session:
            INDEX = '1'

            # Specify checkout url according to the environment
            checkout_url = url

            if not header_value:
                return pretty_json({'error': {
                    'success': False,
                    "status": "PAYMENT_PROCESSING",
                    "message": "Missing Header: X-AUTH",
                }})
            
            # required_fields = ['merchantPublicKey', 'merchantSecretKey', 'amount', 'redirectUrl', 'currency']
            required_fields = ['merchantPublicKey', 'merchantSecretKey', 'amount', 'currency']

            # for field in required_fields:
            #     if not payload_dict.get(field):
            #         return pretty_json({'error': {
            #             "success": False,
            #             "status": "PAYMENT_PROCESSING",
            #             "message":  f'Missing Parameter: {field}',
            #         }}, 400)
            
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
                    "message":  "Invalid merchantPublicKey"
                }}, 400)
            
             # Public Key & Merchant ID
            merchant_public_key = merchant_key.public_key
            merchant_id         = merchant_key.user_id

            merchant_key_status = merchant_key.is_active

            if merchant_key_status == False:
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
                return pretty_json({'error': {
                    "success":  False,
                    "status":  "PAYMENT_PROCESSING",
                    "message": "Incorrect X-AUTH header",
                }}, 400)
            
            # If currency is not equal to USD
            if currency != 'USD':
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
                return pretty_json({'error': {
                    "success": False,
                    "status": "PAYMENT_PROCESSING",
                    "message":  "No Active Acquirer available, Please contact administration",
                }}, 400)
            
             # Save the Merchant Sandbox Transaction details
            exact_amount = amount/100
            unique_transaction_id = generate_unique_id()

            # Get the merchant button id

            merchant_prod_transaction = MerchantProdTransaction(
                merchant_id          = merchant_id,
                status               = 'PAYMENT_INITIATED',
                currency             = currency,
                amount               = exact_amount,
                merchantOrderId      = merchant_order_id,
                merchantRedirectURl  = redirect_url,
                merchantRedirectMode = "REDIRECT",
                merchantMobileNumber = mobile_number,
                merchantPaymentType  = payment_type,
                transaction_id       = unique_transaction_id,
                is_completd          = False,
                gateway_res          = ''    
            )
                
            session.add(merchant_prod_transaction)
            await session.commit()
            await session.refresh(merchant_prod_transaction)

            merchant_order_id = ''

            # Encode the merchant ID
            encoded_merchant_public_key = generate_base64_encode(merchant_public_key)
            encoded_amount              = generate_base64_encode(exact_amount)
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
                        'time': '',
                        'currency': '',
                        "instrumentResponse": {
                            "type": "PAY_PAGE",
                            "redirectInfo": {
                                "url": f"{checkout_url}/merchant/payment/checkout/?token={encoded_merchant_public_key},{encoded_amount},{encodedTransactionID},{encodedCurrency}",
                            }
                        }
                    }
                }, 200)
            
    except Exception as e:
        return pretty_json({'error': 'Server Error', 'message': f'{str(e)}'}, 500)
