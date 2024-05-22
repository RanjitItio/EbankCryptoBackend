from blacksheep import Application
from app.settings import Settings
from Models.models import Users
from sqlmodel import select
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
import os
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta



# from database.db import engine
EMAIL_HOST=config('EMAIL_HOST')
EMAIL_PORT =config('EMAIL_PORT')
EMAIL_USERNAME=config('EMAIL_USERNAME')
EMAIL_PASSWORD=config('EMAIL_PASSWORD')
reset_token_secret_key = config('RESET_TOKEN_SECRET_KEY')


SECRET_KEY = "your_secret_key"

# new_salt = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8')
PASSWORD_RESET_SALT = '3BcOCacZqcaKOXuCvb7S1g=='


def generate_access_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=72),
        "iat": datetime.datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def generate_refresh_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
        "iat": datetime.datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"
    

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



def encrypt_password(password: str) -> str:
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')



def check_password(plain_password: str, hashed_password: str) -> bool:
    
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))



def encrypt_password_reset_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token



def decrypt_password_reset_token(token):
    try:
        payload = jwt.decode(token, reset_token_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"


def send_password_reset_email( recipient_email, subject, body):
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



def send_welcome_email( recipient_email, subject, body):
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



def encrypt_password_reset(user_id: int):
    serializer = URLSafeTimedSerializer(SECRET_KEY)

    user_id_bytes = str(user_id).encode('utf-8')
    user_id_base64 = base64.urlsafe_b64encode(user_id_bytes).decode('utf-8')
    
    token = serializer.dumps(user_id_base64, salt=PASSWORD_RESET_SALT)

    return token


def verify_password_reset_token(token: str, max_age: int = 900):

    serializer = URLSafeTimedSerializer(SECRET_KEY)

    try:
        user_id_base64 = serializer.loads(token, salt=PASSWORD_RESET_SALT, max_age=max_age)
        
        user_id_bytes = base64.urlsafe_b64decode(user_id_base64)
        user_id = int(user_id_bytes.decode('utf-8'))
        
        return user_id
    
    except Exception as e:
        raise ValueError("Invalid or expired token") from e


                

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