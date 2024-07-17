import base64
import hashlib
import json


def calculate_sha256_string(data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data.encode('utf-8'))
    return sha256_hash.hexdigest()


def base64_encode(data):
    json_payload = json.dumps(data)
    encoded_data = base64.b64encode(json_payload.encode('utf-8'))
    encoded_str  = encoded_data.decode('utf-8')
    return encoded_str


def base64_decode(encoded_data):
    decoded_data = base64.b64decode(encoded_data)
    decoded_str  = decoded_data.decode('utf-8')
    return decoded_str


def input_data():
    INDEX        = '1'
    MAINPAYLOAD  = {
            "merchantPublicKey": "1718788989-N92D2BSPEBSL",
            "merchantSecretKey": "eJxLdwQBp9ys7IIsN0cD",
            "merchantOrderId": "MUID123",
            'currency': 'USD',
            "amount": 10000,
            "redirectUrl": "https://webhook.site/redirect-url",
            # "redirectMode": "REDIRECT",
            "callbackUrl": "https://webhook.site/callback-url",
            "mobileNumber": "9999999999",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
   
    ENDPOINT     = "/api/pg/prod/v1/pay/"
    SECRET_KEY   = "eJxLdwQBp9ys7IIsN0cD"
    base64String = base64_encode(MAINPAYLOAD)

    mainString   = base64String + ENDPOINT + SECRET_KEY

    sha256Val    = calculate_sha256_string(mainString)

    checkSum     = sha256Val + '****' + INDEX

    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checkSum,
        'accept': 'application/json',
    }

    json_data = {
        'request': base64String,
    }

    return base64String

# chekcsum = input_data()

# print(chekcsum)
