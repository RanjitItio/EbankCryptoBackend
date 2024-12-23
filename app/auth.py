from blacksheep import Application
from app.settings import Settings
from Models.models import Users
from sqlmodel import select, and_
import jwt
import datetime
from database.db import async_engine, AsyncSession
import bcrypt
import smtplib
from decouple import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from blacksheep import json
from blacksheep import Request
from guardpost import AuthenticationHandler, Identity
from typing import Optional
from guardpost.authorization import AuthorizationContext
from guardpost.authorization import Requirement
from blacksheep.server.authorization import Policy
import base64
from itsdangerous import URLSafeTimedSerializer
from decouple import config
from cryptography.fernet import Fernet
import zlib
from Models.models import HashValue, UserKeys
import time
import random
import string



# from database.db import engine
EMAIL_HOST=config('EMAIL_HOST')
EMAIL_PORT =config('EMAIL_PORT')
EMAIL_USERNAME=config('EMAIL_USERNAME')
EMAIL_PASSWORD=config('EMAIL_PASSWORD')
reset_token_secret_key = config('RESET_TOKEN_SECRET_KEY')


# Merchant Secret Key
merchant_secret_key = config('SECRET_KEY_MERCHANT')
cipher_suite        = Fernet(merchant_secret_key)
hash_map            = {}


SECRET_KEY = config('SECRET_KEY')

# new_salt = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
PASSWORD_RESET_SALT = config('PASSWORD_RESET_SALT')

## Generate Access token while login
def generate_access_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=96),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "type": "access"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


## Generate refresh token while login
def generate_refresh_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "type": "refresh"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

### Decode token
def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
    

## Generate Access token from refresh token
def generate_access_token_from_refresh_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]

        access_token = generate_access_token(user_id)
        return json({'access_token': access_token})

    except jwt.ExpiredSignatureError:
        return "Refresh token has expired"
    except jwt.InvalidTokenError:
        return "Invalid refresh token"



async def is_authenticated(id):
    async with AsyncSession(async_engine) as session:
        user = await session.exec(select(Users).where(Users.id == id)).first()
        if user is not None:
            return user
        else:
            return False


# Encrypt Users password into Hash
def encrypt_password(password: str) -> str:
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


# Validate password while Loging in
def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


### Excryption whiile reseting password
def encrypt_password_reset_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


## Decrypt Password reset token
def decrypt_password_reset_token(token):
    try:
        payload = jwt.decode(token, reset_token_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"



def send_password_reset_email(recipient_email, subject, body):
    smtp_server = EMAIL_HOST
    smtp_port = int(EMAIL_PORT)  # For TLS
   
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, recipient_email, msg.as_string())



### Send mail while login and update user
def send_welcome_email(recipient_email, subject, body):
    smtp_server = EMAIL_HOST
    smtp_port = int(EMAIL_PORT)  # For TLS
   
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, recipient_email, msg.as_string())
        


async def send_email(recipient_email, subject, body):
    smtp_server = EMAIL_HOST
    smtp_port = int(EMAIL_PORT)  # For TLS
   
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        
        server.starttls()  
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, recipient_email, msg.as_string())


# Encrypt Password Reset Token
def encrypt_password_reset(user_id: int):
    serializer = URLSafeTimedSerializer(SECRET_KEY)

    user_id_bytes = str(user_id).encode('utf-8')
    user_id_base64 = base64.urlsafe_b64encode(user_id_bytes).decode('utf-8')
    
    token = serializer.dumps(user_id_base64, salt=PASSWORD_RESET_SALT)

    return token


# Decode password reset token
def verify_password_reset_token(token: str, max_age: int = 900):

    serializer = URLSafeTimedSerializer(SECRET_KEY)

    try:
        user_id_base64 = serializer.loads(token, salt=PASSWORD_RESET_SALT, max_age=max_age)
        
        user_id_bytes = base64.urlsafe_b64decode(user_id_base64)
        user_id = int(user_id_bytes.decode('utf-8'))
        
        return user_id
    
    except Exception as e:
        raise ValueError("Invalid or expired token") from e


# Generate Unique Merchant Public Key
async def generate_merchant_unique_public_key():
    while True:
        async with AsyncSession(async_engine) as session:
            timestamp    = str(int(time.time()))
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            unique_key   =  f"{timestamp}-{random_chars}"

            statement = select(UserKeys).where(UserKeys.public_key == unique_key)
            result    = (await session.execute(statement)).scalar()

            if not result:
                return unique_key
                   
                

# Generate Merchant Secret Key
async def generate_merchant_secret_key(merchant_id):
    try:
        async with AsyncSession(async_engine) as session:
            while True:
                model_id_bytes       = str(merchant_id).encode()
                encrypted_model_id   = cipher_suite.encrypt(model_id_bytes)
                compressed_data      = zlib.compress(encrypted_model_id)
                encoded_data         = base64.urlsafe_b64encode(compressed_data).decode()
                short_hash           = encoded_data[:20]
                # hash_map[short_hash] = encoded_data

                # Check hashvalue exists or Not 
                exist_hash_obj = await session.execute(select(HashValue).where(
                    and_(HashValue.hash_value == short_hash, HashValue.encode_data == encoded_data)
                ))
                exist_hash = exist_hash_obj.scalar()

                if not exist_hash:

                    hash_value = HashValue(
                        hash_value  = short_hash,
                        encode_data = encoded_data
                    )

                    session.add(hash_value)
                    await session.commit()
                    await session.refresh(hash_value)

                    return short_hash
        
    except Exception as e:
        return f'Secret key generation error {str(e)}'
    

#Update a new Merchant Secret Key
async def update_merchant_secret_key(merchant_id, secret_key):
    try:
        async with AsyncSession(async_engine) as session:
            
            model_id_bytes       = str(merchant_id).encode()
            encrypted_model_id   = cipher_suite.encrypt(model_id_bytes)
            compressed_data      = zlib.compress(encrypted_model_id)
            encoded_data         = base64.urlsafe_b64encode(compressed_data).decode()
            short_hash           = encoded_data[:20]

            # Check hashvalue exists or Not 
            exist_hash_obj = await session.execute(select(HashValue).where(
                HashValue.hash_value == secret_key
            ))
            exist_hash = exist_hash_obj.scalar()

            if exist_hash:
                exist_hash.hash_value  = short_hash
                exist_hash.encode_data = encoded_data

                session.add(exist_hash)
                await session.commit()
                await session.refresh(exist_hash)

                return short_hash
            else:
                hsah_value = HashValue(
                    hash_value = short_hash,
                    encode_data = encoded_data
                )

                session.add(hsah_value)
                await session.commit()
                await session.refresh(hsah_value)

                return short_hash
        
    except Exception as e:
        return f'Secret key generation error {str(e)}'


#Decrypt Merchant Secret Key
async def decrypt_merchant_secret_key(short_hash):

    try: 
        async with AsyncSession(async_engine) as session:

            # encoded_data = hash_map.get(short_hash, None)
            # print(type(short_hash))
            encoded_obj   = await session.execute(select(HashValue).where(HashValue.hash_value == short_hash))
            encoded_value = encoded_obj.scalar()

            if not encoded_value:
                return 'Hash value not found'

            encoded_data = encoded_value.encode_data

            if not encoded_data:
                raise ValueError("Invalid hash or hash not found")
            
            compressed_data    = base64.urlsafe_b64decode(encoded_data.encode())
            encrypted_data     = zlib.decompress(compressed_data)
            decrypted_model_id = cipher_suite.decrypt(encrypted_data).decode()

            return int(decrypted_model_id)
        
    except Exception as e:
        return f'Decrypt error {str(e)}'
    
                

def configure_authentication(app: Application, settings: Settings):
    """
    Configure authentication as desired. For reference:
    https://www.neoteroi.dev/blacksheep/authentication/
    """





class UserAuthHandler(AuthenticationHandler):
    def __init__(self):
        pass

    async def authenticate(self, context: Request) -> Optional[Identity]:

        header_value = context.get_first_header(b"Authorization")

        if header_value:
            header_value_str = header_value.decode("utf-8")
            parts            = header_value_str.split()

            if len(parts) == 2 and parts[0] == "Bearer":
                token = parts[1]
                user_data = decode_token(token)

                if user_data == 'Token has expired':
                    context.identity = None
                elif user_data == 'Invalid token':
                    context.identity = None
                else:
                    user_id = user_data["user_id"]
                    context.identity = Identity({"user_id": user_id, "claims": user_data}, "JWT")
            else:
                context.identity = None
        else:
            context.identity = None
            
        return context.identity
    




class AdminRequirement(Requirement):
    def handle(self, context: AuthorizationContext):
        identity = context.identity

        if identity is not None and identity.claims.get("role") == "admin":
            context.succeed(self)



class AdminsPolicy(Policy):
    def __init__(self):
        super().__init__("admin", AdminRequirement())